"""Exercise the installed website, assets, model CRUD, reuse and Ctrl+C cleanup."""
import argparse
import json
from pathlib import Path
import re
import signal
import socket
import subprocess
import tempfile
import time
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory).resolve()
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        base = f'http://127.0.0.1:{port}'
        http = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        def request(path, body=None, method=None):
            req = urllib.request.Request(base + path, data=None if body is None else json.dumps(body).encode(),
                                         method=method, headers={'Content-Type': 'application/json'})
            with http.open(req, timeout=30) as response:
                return response.read()
        command = [args.executable, '--root', str(root), 'web', '--port', str(port), '--no-browser', '--no-setup', '--json']
        helper_port = None
        with (root / 'web.log').open('w+') as log:
            process = subprocess.Popen(command, stdout=log, stderr=log)
            try:
                deadline = time.monotonic() + 120
                while True:
                    if process.poll() is not None or time.monotonic() > deadline:
                        log.seek(0)
                        raise RuntimeError(log.read())
                    try:
                        workspace = json.loads(request('/api/workspace'))
                        assert workspace['root'] == str(root)
                        helper_port = int(workspace['opencode_url'].rsplit(':', 1)[1])
                        break
                    except OSError:
                        time.sleep(.25)
                pages = ('/completion', '/models', '/pair', '/wm', '/detection', '/')
                assets = set()
                for path in pages:
                    page = request(path).decode()
                    assert '<html' in page.lower(), path
                    assets.update(re.findall(r'(?:src|href)="(/pair-assets/[^"?]+)', page))
                for path in assets:
                    assert request(path), path
                model = json.loads(request('/api/models', {'name': 'Installed web verification', 'seed': '42'}))
                assert model['seed'] == 42, model
                assert model['key'] in (root / 'harness/models.json').read_text()
                request('/api/models/' + model['key'], method='DELETE')
                reused = subprocess.run(command, text=True, capture_output=True, timeout=15, check=True)
                assert json.loads(reused.stdout)['existing'] is True, reused.stdout
                assert not (root / 'harness/ui').exists(), 'Assets must come from the package'
                print(json.dumps({'pages': list(pages), 'assets': len(assets), 'model_crud': 'passed', 'reuse': 'passed'}))
            finally:
                if process.poll() is None:
                    process.send_signal(signal.SIGINT)
                    try:
                        process.wait(timeout=20)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
            for target in (port, helper_port):
                if target is not None:
                    with socket.socket() as sock:
                        assert sock.connect_ex(('127.0.0.1', target)) != 0, f'Leaked server on port {target}'
            print('Website and owned session helper stopped cleanly.')


if __name__ == '__main__':
    main()

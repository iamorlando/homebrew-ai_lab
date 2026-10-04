"""Exercise the installed website, assets, model CRUD, reuse and Ctrl+C cleanup."""
import argparse
import json
import os
from pathlib import Path
import re
import signal
import socket
import subprocess
import tempfile
import time
import urllib.request
import urllib.error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable')
    parser.add_argument('--jev-configured', action='store_true', help='Verify Jev discovery with a synthetic server key; no hosted request is sent')
    parser.add_argument('--laya-source', type=Path, help='Reuse an installed Laya runtime and weights for a real packaged-provider check')
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
        env = {k: v for k, v in os.environ.items() if k not in {
            'TYPESAFE_API_KEY', 'JEV_API_KEY', 'AI_LAB_DECISIONS_URL',
            'AI_LAB_DECISIONS_MODEL', 'AI_LAB_DECISIONS_BINARY', 'AI_LAB_DECISIONS_API_KEY',
            'AI_LAB_CLM_UPSTREAM_URL', 'AI_LAB_CLM_UPSTREAM_API_KEY', 'AI_LAB_LAYA_URL', 'AI_LAB_LAYA_API_KEY'}}
        laya_port = None
        if args.laya_source:
            source = args.laya_source.resolve()
            for name in ('.runtime/decisions/laya', '.models/laya', '.runtime/opencode/opencode'):
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.symlink_to(source / name)
            if (source / '.runtime/node').is_dir():
                (root / '.runtime/node').symlink_to(source / '.runtime/node')
            laya_port = 8710
        if args.jev_configured:
            env['TYPESAFE_API_KEY'] = 'synthetic-install-check-key'
        helper_port = None
        with (root / 'web.log').open('w+') as log:
            process = subprocess.Popen(command, stdout=log, stderr=log, env=env)
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
                pages = ('/completion', '/models', '/pair', '/wm', '/detection', '/decisions', '/')
                assets = set()
                for path in pages:
                    page = request(path).decode()
                    assert '<html' in page.lower(), path
                    assert 'rel="manifest" href="/manifest.webmanifest"' in page, path
                    assets.update(re.findall(r'(?:src|href)="(/pair-assets/[^"?]+)', page))
                for path in assets:
                    assert request(path), path
                manifest = json.loads(request('/manifest.webmanifest'))
                assert manifest['display'] == 'standalone'
                assert manifest['start_url'] == '/completion'
                for icon in manifest['icons']:
                    assert request(icon['src']).startswith(b'\x89PNG\r\n\x1a\n')
                assert b"self.addEventListener('fetch'" in request('/service-worker.js')
                decisions = request('/api/decisions/models')
                assert 'synthetic-install-check-key' not in decisions.decode()
                expected = ['contrastive', 'jev'] if args.jev_configured else ['contrastive']
                if args.laya_source:
                    expected.insert(1, 'laya')
                assert [m['name'] for m in json.loads(decisions)['models']] == expected
                schema = json.loads(request('/openapi.json'))
                for path in ('/api/decisions/models', '/api/decisions/systemone', '/api/decisions/rank'):
                    assert path in schema['paths'], path
                assert b'Apache' in request('/pair-assets/licenses/CLM-LICENSE.txt')
                if args.laya_source:
                    result = json.loads(request('/api/decisions/systemone', {'model': 'laya', 'state': 'This is a packaged Laya test.',
                              'questions': {'configured': {'type': 'noul', 'instructions': 'Is this a test?'}}}))
                    assert result['model'] == 'laya', result
                    assert 0 <= result['answers']['configured']['noul'] <= 1, result
                if not args.jev_configured:
                    try:
                        request('/api/decisions/systemone', {'model': 'jev', 'state': 'Synthetic installation check.',
                                'questions': {'test': {'type': 'noul', 'instructions': 'Is this a test?'}}})
                        raise AssertionError('Jev must reject requests without a key')
                    except urllib.error.HTTPError as error:
                        assert error.code == 403, error.code
                model = json.loads(request('/api/models', {'name': 'Installed web verification', 'seed': '42'}))
                assert model['seed'] == 42, model
                assert model['key'] in (root / 'harness/models.json').read_text()
                updated = json.loads(request('/api/models/' + model['key'],
                          {'scheme': 'kgw', 'key': '42' * 32, 'settings': {'delta': 3}}, method='PATCH'))
                assert updated['watermark']['delta'] == 3
                assert (root / 'harness/models.json').stat().st_mode & 0o777 == 0o600
                assert 'patch' in schema['paths']['/api/lab/models/{key}']
                request('/api/models/' + model['key'], method='DELETE')
                reused = subprocess.run(command, text=True, capture_output=True, timeout=15, check=True, env=env)
                assert json.loads(reused.stdout)['existing'] is True, reused.stdout
                assert not (root / 'harness/ui').exists(), 'Assets must come from the package'
                print(json.dumps({'pages': list(pages), 'assets': len(assets), 'model_crud': 'passed', 'reuse': 'passed', 'decisions': expected}))
            finally:
                if process.poll() is None:
                    process.send_signal(signal.SIGINT)
                    try:
                        process.wait(timeout=20)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
            for target in (port, helper_port, laya_port):
                if target is not None:
                    with socket.socket() as sock:
                        assert sock.connect_ex(('127.0.0.1', target)) != 0, f'Leaked server on port {target}'
            print('Website and owned session helper stopped cleanly.')


if __name__ == '__main__':
    main()

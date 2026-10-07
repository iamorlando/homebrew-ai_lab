"""Exercise installed web routes and cleanup with owned Python CPU API fixtures.

Never launches native/model processes. Production eager-start ownership is tested
separately in the release matrix; this checker proves fixture/API availability,
installed assets, supported model CRUD, decoder privacy, reuse and Ctrl+C cleanup.
"""
import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import urllib.error
from urllib.parse import urlparse


# Each endpoint is an independent, owned Python process. No application/runtime
# imports or binary/model discovery are possible inside these fixture servers.
FIXTURE_API = r"""
import json, os, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
family, receipt = sys.argv[1:]
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def send(self, value, status=200):
        data = json.dumps(value).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers(); self.wfile.write(data)
    def do_GET(self):
        if self.path != '/v1/models': return self.send({'error': 'Fixture route missing'}, 404)
        self.send({'data': [{'id': 'ai-lab-fixture-deepseek'}], 'models': [{'name': 'fixture-clm'}],
                   'fixture': True, 'family': family, 'pid': os.getpid()})
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        if family == 'deepseek' and self.path == '/v1/completions':
            return self.send({'choices': [{'text': 'Owned CPU fixture response.', 'finish_reason': 'stop'}],
                              'usage': {'completion_tokens': 6}})
        if family == 'deepseek' and self.path == '/v1/watermark/detect':
            return self.send({'tokens_scored': 100, 'green_count': 80, 'z_score': 6, 'mean_g_value': .8})
        if family == 'contrastive' and self.path == '/v1/systemone':
            return self.send({'model': 'fixture-clm', 'answers': {
                name: {'type': 'noul', 'noul': .75} for name in body['questions']}})
        self.send({'error': 'Fixture route missing'}, 404)
server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
temporary = Path(receipt + '.tmp')
temporary.write_text(json.dumps({'url': 'http://127.0.0.1:' + str(server.server_port), 'pid': os.getpid()}))
temporary.replace(receipt)
server.serve_forever()
"""


@contextmanager
def owned_api_fixtures(directory):
    processes, endpoints, logs = {}, {}, {}
    try:
        for family in ('deepseek', 'contrastive'):
            receipt = directory / (family + '-fixture.json')
            log_path = directory / (family + '-fixture.log')
            logs[family] = log_path.open('w')
            process = subprocess.Popen([sys.executable, '-I', '-u', '-c', FIXTURE_API, family, str(receipt)],
                                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=logs[family])
            processes[family] = process
            deadline = time.monotonic() + 10
            while not receipt.exists():
                if process.poll() is not None or time.monotonic() > deadline:
                    raise RuntimeError(f'Owned {family} CPU fixture failed to start: ' + log_path.read_text())
                time.sleep(.02)
            identity = json.loads(receipt.read_text())
            assert identity['pid'] == process.pid
            endpoints[family] = identity['url']
        yield endpoints, processes
    finally:
        for process in processes.values():
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait(timeout=10)
        for log in logs.values():
            log.close()
        for endpoint in endpoints.values():
            with socket.socket() as sock:
                assert sock.connect_ex(('127.0.0.1', urlparse(endpoint).port)) != 0, 'Leaked owned API fixture'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable')
    parser.add_argument('--root', type=Path, help='Owned retained data root for literal upgrade checks; data is preserved')
    parser.add_argument('--jev-configured', action='store_true', help='Verify Jev discovery with a synthetic server key; no hosted request is sent')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as directory, owned_api_fixtures(Path(directory)) as (endpoints, api_processes):
        root = args.root.resolve() if args.root else Path(directory).resolve()
        root.mkdir(parents=True, exist_ok=True)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        base = f'http://127.0.0.1:{port}'
        http = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        final_urls = {}
        def request(path, body=None, method=None):
            req = urllib.request.Request(base + path, data=None if body is None else json.dumps(body).encode(),
                                         method=method, headers={'Content-Type': 'application/json'})
            with http.open(req, timeout=30) as response:
                final_urls[path] = response.geturl()
                return response.read()
        command = [args.executable, '--root', str(root), 'web', '--port', str(port), '--no-browser', '--json']
        env = {k: v for k, v in os.environ.items() if k not in {
            'TYPESAFE_API_KEY', 'JEV_API_KEY', 'AI_LAB_DECISIONS_URL',
            'AI_LAB_DECISIONS_MODEL', 'AI_LAB_DECISIONS_BINARY', 'AI_LAB_DECISIONS_API_KEY',
            'AI_LAB_CLM_UPSTREAM_URL', 'AI_LAB_CLM_UPSTREAM_API_KEY', 'AI_LAB_LAYA_URL', 'AI_LAB_LAYA_API_KEY',
            'AI_LAB_GENERATION_FIXTURE_FILE'}}
        fixture_file = Path(directory) / 'generation-fixture.json'
        fixture_file.write_text(json.dumps({'version': 1, 'endpoints': {'deepseek': endpoints['deepseek']}}))
        env['AI_LAB_GENERATION_FIXTURE_FILE'] = str(fixture_file)
        env['AI_LAB_DECISIONS_URL'] = endpoints['contrastive']

        def api_request(family, path='/v1/models', body=None):
            req = urllib.request.Request(endpoints[family] + path,
                    data=None if body is None else json.dumps(body).encode(),
                    headers={'Content-Type': 'application/json'})
            with http.open(req, timeout=5) as response:
                return json.loads(response.read())

        def apis_alive():
            for family, api in api_processes.items():
                assert api.poll() is None, f'{family} fixture unexpectedly stopped'
                identity = api_request(family)
                assert identity['pid'] == api.pid and identity['family'] == family

        existing_receipts = {name: (root / '.state' / name).read_bytes() if (root / '.state' / name).exists() else None
                             for name in ('mistral-server.json', 'qwen-server.json', 'decisions-mistral.json')}
        def weight_files():
            return {str(path.relative_to(root)): (path.stat().st_size, path.stat().st_mtime_ns)
                    for path in (root / '.models').rglob('*') if path.is_file()}
        weights_before = weight_files()
        created_profiles = []
        if args.jev_configured:
            env['TYPESAFE_API_KEY'] = 'synthetic-install-check-key'
        with (Path(directory) / 'web-check.log').open('w+') as log:
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
                        assert not workspace.get('opencode_url'), 'Web must not require OpenCode'
                        break
                    except OSError:
                        time.sleep(.25)
                apis_alive()
                retained_profiles = json.loads((root / 'harness/models.json').read_text())
                pages = ('/completion', '/models', '/decoder', '/decisions')
                aliases = ('/', '/pair', '/wm', '/detection')
                assets = set()
                for path in (*pages, *aliases):
                    page = request(path).decode()
                    assert '<html' in page.lower(), path
                    if path in ('/', '/pair', '/wm'):
                        assert urlparse(final_urls[path]).path == '/completion', (path, final_urls[path])
                    assert 'rel="manifest" href="/manifest.webmanifest"' in page, path
                    assert 'data-section="comparison"' not in page and 'data-section="watermark"' not in page, path
                    assets.update(re.findall(r'(?:src|href)="(/pair-assets/[^"?]+)', page))
                for path in assets:
                    assert request(path), path
                revision = re.search(r'<meta name="lab-revision" content="([^"]+)">', page).group(1)
                for prefix in ('/pair-assets/', '/pair-assets/' + revision + '/'):
                    for retired in ('index.html', 'watermarks.html', 'app.js', 'watermarks.js'):
                        try:
                            request(prefix + retired)
                            raise AssertionError('Retired screen asset remains public: ' + prefix + retired)
                        except urllib.error.HTTPError as error:
                            assert error.code == 404, (prefix + retired, error.code)
                shell = request('/pair-assets/shell.js').decode()
                navigation = re.findall(r"\['[^']+', '[^']+', '(/[^']+)'\]", shell)
                assert navigation == ['/completion', '/decisions', '/decoder', '/models'], navigation
                manifest = json.loads(request('/manifest.webmanifest'))
                assert manifest['display'] == 'standalone'
                assert manifest['start_url'] == '/completion'
                for icon in manifest['icons']:
                    assert request(icon['src']).startswith(b'\x89PNG\r\n\x1a\n')
                assert b"self.addEventListener('fetch'" in request('/service-worker.js')
                decisions = request('/api/decisions/models')
                assert 'synthetic-install-check-key' not in decisions.decode()
                expected = ['contrastive', 'jev'] if args.jev_configured else ['contrastive']
                assert [m['name'] for m in json.loads(decisions)['models']] == expected
                schema = json.loads(request('/openapi.json'))
                for path in ('/api/decisions/models', '/api/decisions/systemone', '/api/decisions/rank',
                             '/api/decoder/models', '/api/decoder/detect', '/api/decoder/generate'):
                    assert path in schema['paths'], path
                assert not any(path.startswith(('/api/pairs', '/api/wm')) for path in schema['paths'])
                for route in ('/api/pairs', '/api/wm/experiments'):
                    try:
                        request(route, {})
                        raise AssertionError('Retired action still accepts requests: ' + route)
                    except urllib.error.HTTPError as error:
                        assert error.code in (404, 405), (route, error.code)
                assert b'Apache' in request('/pair-assets/licenses/CLM-LICENSE.txt')
                if not args.jev_configured:
                    try:
                        request('/api/decisions/systemone', {'model': 'jev', 'state': 'Synthetic installation check.',
                                'questions': {'test': {'type': 'noul', 'instructions': 'Is this a test?'}}})
                        raise AssertionError('Jev must reject requests without a key')
                    except urllib.error.HTTPError as error:
                        assert error.code == 403, error.code
                model = json.loads(request('/api/models', {'name': 'Installed web verification', 'seed': '42'}))
                created_profiles.append(model['key'])
                assert model['seed'] == 42, model
                assert model['key'] in (root / 'harness/models.json').read_text()
                updated = json.loads(request('/api/models/' + model['key'],
                          {'scheme': 'kgw', 'key': '42' * 32, 'settings': {'delta': 3}}, method='PATCH'))
                assert updated['watermark']['delta'] == 3
                second = json.loads(request('/api/models', {'name': 'Second DeepSeek verification',
                                    'underlying_model': 'deepseek', 'seed': '43'}))
                created_profiles.append(second['key'])
                assert second['underlying_model'] == 'DeepSeekR1', second
                request('/api/models/' + second['key'],
                        {'scheme': 'kgw', 'key': '43' * 32, 'settings': {'delta': 4}}, method='PATCH')
                for route in ('/api/models', '/api/lab/models'):
                    catalog = json.loads(request(route))
                    assert catalog['underlying_models'] == ['DeepSeekR1'], catalog['underlying_models']
                    assert all(profile['underlying_model'] == 'DeepSeekR1' for profile in catalog['models'])
                    try:
                        request(route, {'name': 'Rejected Qwen', 'underlying_model': 'qwen'})
                        raise AssertionError('Retired standalone Qwen creation must be rejected')
                    except urllib.error.HTTPError as error:
                        assert error.code in (409, 422), error.code
                decoder = json.loads(request('/api/decoder/models'))
                catalog = {profile['id']: profile for profile in decoder['profiles']}
                assert catalog[model['key']]['underlying_model'] == 'DeepSeekR1'
                assert catalog[second['key']]['underlying_model'] == 'DeepSeekR1'
                assert catalog[second['key']]['scheme'] == 'kgw'
                assert catalog[second['key']]['settings']['delta'] == 4
                assert catalog[second['key']]['hasKey'] is True
                assert '42' * 32 not in json.dumps(decoder) and '43' * 32 not in json.dumps(decoder)
                assert all('key' not in profile and 'seed' not in profile for profile in decoder['profiles'])
                for profile in (model, second):
                    generated = json.loads(request('/api/decoder/generate', {'model': profile['key'], 'prompt': 'CPU fixture check.'}))
                    assert generated['fixture'] is True and generated['profile_key'] == profile['key']
                    detected = json.loads(request('/api/decoder/detect', {'model': profile['key'],
                                         'text': generated['answer'], 'snapshot': generated['snapshot']}))
                    assert detected['fixture'] is True and detected['profile_key'] == profile['key']
                    apis_alive()
                decision_body = {'model': 'contrastive', 'state': 'A synthetic check.',
                                 'questions': {'test': {'type': 'noul', 'instructions': 'Is this a test?'}}}
                # Python clients address CLM independently of the web request layer.
                assert api_request('contrastive', '/v1/systemone', decision_body)['answers']['test']['noul'] == .75
                assert json.loads(request('/api/decisions/systemone', decision_body))['answers']['test']['noul'] == .75
                time.sleep(.3)
                apis_alive()
                assert (root / 'harness/models.json').stat().st_mode & 0o777 == 0o600
                assert 'patch' in schema['paths']['/api/lab/models/{key}']
                request('/api/models/' + model['key'], method='DELETE')
                request('/api/models/' + second['key'], method='DELETE')
                created_profiles.clear()
                assert json.loads((root / 'harness/models.json').read_text()) == retained_profiles
                reused = subprocess.run(command, text=True, capture_output=True, timeout=15, check=True, env=env)
                assert json.loads(reused.stdout)['existing'] is True, reused.stdout
                assert not (root / 'harness/ui').exists(), 'Assets must come from the package'
                apis_alive()
                report = {'scope': 'owned_python_cpu_api_fixtures', 'native_model_proof': False,
                                  'production_eager_start': 'not_run_separate_release_matrix_lane',
                                  'pages': list(pages), 'redirect_aliases': list(aliases), 'assets': len(assets),
                                  'model_crud': 'passed', 'qwen_rejected': 'passed', 'decoder_key_privacy': 'passed',
                                  'api_lifetime': 'passed', 'clm_direct_python_http': 'passed',
                                  'reuse': 'passed', 'decisions': expected}
            finally:
                if process.poll() is None:
                    for key in created_profiles:
                        try: request('/api/models/' + key, method='DELETE')
                        except (OSError, ValueError): pass
                if process.poll() is None:
                    process.send_signal(signal.SIGINT)
                    try:
                        process.wait(timeout=20)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
            for target in (port,):
                if target is not None:
                    with socket.socket() as sock:
                        assert sock.connect_ex(('127.0.0.1', target)) != 0, f'Leaked server on port {target}'
            # These are checker-owned APIs, so web must leave them untouched.
            apis_alive()
            for name, before in existing_receipts.items():
                path = root / '.state' / name
                assert (path.read_bytes() if path.exists() else None) == before, name
            assert weight_files() == weights_before, 'Fixture web checks must not create or change weights'
            report['web_cleanup'] = 'passed'
            report['weight_files_unchanged'] = 'passed'
    report['fixture_process_cleanup'] = 'passed'
    print(json.dumps(report))
    print('Website and owned CPU API fixtures stopped cleanly. No native models started.')


if __name__ == '__main__':
    main()

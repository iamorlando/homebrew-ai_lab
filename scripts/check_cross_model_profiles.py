#!/usr/bin/env python3
"""Check an installed AI Lab against explicit, owned HTTP fixtures.

Run with the installed application's Python, not a source-only environment:
  .venv/bin/python packaging/check_cross_model_profiles.py --python /path/to/installed/python

No weights, downloads, native servers, GPU, hosted credentials or foreign processes.
Synthetic trace output proves transport/configuration only, never watermark efficacy.
"""
import argparse
from contextlib import contextmanager
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request


FAMILIES = {'deepseek': 'DeepSeekR1', 'qwen': 'Qwen3-8B'}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def private_json(path, value):
    with open(path, 'w', opener=lambda p, flags: os.open(p, flags, 0o600)) as stream:
        json.dump(value, stream)


def json_request(url, method='GET', body=None):
    request = urllib.request.Request(url, method=method,
        data=None if body is None else json.dumps(body).encode(),
        headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.load(response)


@contextmanager
def fixtures():
    events, servers, threads = [], [], []
    health = {'valid': True}

    def handler(family):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def respond(self, value):
                data = json.dumps(value).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):
                self.respond({'data': [{'id': 'ai-lab-fixture-' + family if health['valid'] else 'default'}]})

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                events.append({'family': family, 'path': self.path, 'body': body})
                # A deliberately synthetic, bounded one-token trace. Never native proof.
                watermark = body.get('watermark')
                token = 'D' if family == 'deepseek' else 'Q'
                step = {'generated_index': 0, 'context_length': 10, 'selected_token_id': 17,
                        'candidate_count': 1, 'candidates': [{'token_id': 17, 'text': token,
                        'pre_watermark_probability': 1, 'post_watermark_probability': 1}],
                        'layers': [], 'watermark': None if watermark is None else
                        {'scheme': watermark['scheme'], 'status': 'fixture'}}
                self.respond({'choices': [{'text': token, 'finish_reason': 'length',
                                           'sampling_trace': {'steps': [step]}}]})
        return Handler

    try:
        for family in FAMILIES:
            server = ThreadingHTTPServer(('127.0.0.1', 0), handler(family))
            servers.append((family, server))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            threads.append(thread)
            thread.start()
        yield {family: f'http://127.0.0.1:{server.server_port}' for family, server in servers}, events, health
    finally:
        for _, server in servers:
            server.shutdown()
            server.server_close()
        for thread in threads:
            thread.join(timeout=5)
            require(not thread.is_alive(), 'Fixture did not close')


@contextmanager
def installed_service(root):
    import ai_lab
    from ai_lab.paths import BUNDLE, load_backend
    require(BUNDLE.is_dir(), 'Use an installed wheel interpreter; source imports are not installed-package proof')
    from ai_lab.setup import prepare
    prepare(root)
    load_backend(root)
    from ai_lab.service import create_app
    from watermark_runtime import WatermarkRuntime
    import inference
    import uvicorn
    require(Path(inference.__file__).is_relative_to(BUNDLE), 'Runtime came from outside the installed bundle')
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    sock.listen()
    url = f'http://127.0.0.1:{sock.getsockname()[1]}'
    server = uvicorn.Server(uvicorn.Config(create_app(root, WatermarkRuntime(allow_start=False)),
                            log_level='critical', access_log=False, timeout_graceful_shutdown=5))
    thread = threading.Thread(target=server.run, kwargs={'sockets': [sock]}, daemon=True)
    try:
        thread.start()
        deadline = time.monotonic() + 10
        while not server.started and thread.is_alive() and time.monotonic() < deadline:
            time.sleep(.02)
        require(server.started, 'Owned installed API did not start')
        yield url, str(Path(ai_lab.__file__).resolve())
    finally:
        server.should_exit = True
        if thread.ident is not None:
            thread.join(timeout=10)
        sock.close()
        require(not thread.is_alive(), 'Owned installed API did not close')


def probe(root, phase):
    """Executed in a fresh installed interpreter with source paths isolated."""
    checkpoint = root / 'checkpoint.json'
    expected = []
    with installed_service(root) as (url, package):
        env = {**os.environ, 'AI_LAB_SERVER': url}

        def cli(*arguments, error=False):
            result = subprocess.run([sys.executable, '-I', '-m', 'ai_lab', '--root', str(root),
                                     *arguments, '--json'], cwd=root, env=env,
                                    capture_output=True, text=True, timeout=20)
            # CLI responses can legitimately include newly created keys. Never echo them.
            require((result.returncode != 0) == error, 'Installed CLI exit status disagrees with expected outcome')
            value = json.loads(result.stderr if error else result.stdout)
            if error:
                require(value.get('ok') is False, 'CLI error was not structured')
            return value

        def stored():
            return {p['key']: p for p in cli('models', 'list')['models']}

        if phase == 'create':
            records = {}
            for family, underlying in FAMILIES.items():
                for kind in ('plain', 'seeded', 'marked'):
                    name = family + ' ' + kind
                    arguments = ['models', 'create', '--underlying-model', family, '--name', name]
                    if kind != 'plain':
                        arguments += ['--seed', '0x2A' if family == 'deepseek' else '0x2B']
                    if kind == 'marked':
                        config = {'scheme': 'kgw', 'key': secrets.token_hex(32), 'delta': 3 if family == 'deepseek' else 5,
                                  'green_fraction': .25 if family == 'deepseek' else .75, 'context_width': 2}
                        path = root / (family + '-watermark.json')
                        private_json(path, config)
                        arguments += ['--watermark-file', str(path)]
                    record = cli(*arguments)
                    require(record['name'] == name, 'Profile name changed during creation')
                    require(record['underlying_model'] == underlying, 'Profile selected the wrong backend')
                    require(record['seed'] == (None if kind == 'plain' else 42 if family == 'deepseek' else 43), 'Seed changed')
                    require(record['seed_literal'] == (None if kind == 'plain' else '0x2A' if family == 'deepseek' else '0x2B'), 'Seed literal changed')
                    if kind == 'marked':
                        require(all(record.get('watermark', {}).get(k) == v for k, v in config.items()), 'Creation lost supplied watermark key/settings')
                    else:
                        require(record.get('watermark') is None, 'Plain/seeded creation inherited a watermark')
                    records[name] = record
            require(len({record['key'] for record in records.values()}) == 6, 'Profile IDs are not distinct')
            private_json(checkpoint, records)
            # Exercise legacy default loading in the next fresh process, preserving identity.
            path = root / 'harness/models.json'
            document = json.loads(path.read_text())
            for record in document['models']:
                if record['key'] == records['deepseek plain']['key']:
                    del record['underlying_model']
            private_json(path, document)
        else:
            records = json.loads(checkpoint.read_text())
        require(stored() == {record['key']: record for record in records.values()}, 'Fresh-process profile/configuration reload changed')
        require((root / 'harness/models.json').stat().st_mode & 0o777 == 0o600, 'Profiles are not private')

        if phase == 'reject':
            for family in FAMILIES:
                value = cli('complete', '--name', family + ' marked', '--prompt', 'probe', error=True)
                require('--' + family in value['error']['message'], 'Wrong-family stopped API guidance')
            return {'phase': phase, 'package': package, 'checked': 'generic default alias rejected without generation'}

        # Interleave marked/plain/seeded requests across both endpoints and return to the first profile.
        for name, scheme in [('deepseek marked', 'model'), ('qwen marked', 'model'), ('deepseek plain', 'model'),
                             ('qwen seeded', 'model'), ('qwen marked', 'none'), ('deepseek seeded', 'model'),
                             ('qwen plain', 'model'), ('deepseek marked', 'model')]:
            record = records[name]
            family = name.split()[0]
            prompt = name + '  \n'
            result = cli('complete', '--name', name, '--scheme', scheme, '--prompt', prompt, '--max-tokens', '2')
            require(result['status'] == 'complete' and result['model'] == record['key'], 'Completion lost selected identity')
            require(len(result['results']) == 2 and result['answer'] == ('D' if family == 'deepseek' else 'Q') * 2, 'Completion did not perform both fixture decisions')
            require(result['profile']['underlying_model'] == FAMILIES[family], 'Session snapshot lost backend')
            watermark = deepcopy(record.get('watermark')) if scheme == 'model' else None
            require(result['watermark'] == (None if watermark is None else {k: v for k, v in watermark.items() if k != 'key'}), 'Session inherited wrong settings')
            for index, generated in enumerate(result['results']):
                require(generated.get('fixture') is True, 'Fixture provenance missing')
                require(generated['model'] == FAMILIES[family], 'Completion result lost backend')
                require('key' not in json.dumps(generated), 'Public completion exposed a watermark key')
                expected.append({'family': family, 'prompt': prompt + ('D' if family == 'deepseek' else 'Q') * index,
                                 'seed': record['seed'], 'watermark': watermark})

        session_id = result['id']
        positional = {'scheme': 'exponential', 'key': records['qwen marked']['watermark']['key'],
                      'start_position': 7, 'sequence_len': 128}
        private_json(root / 'positional.json', positional)
        result = cli('complete', '--name', 'qwen marked', '--scheme', 'exponential',
                     '--watermark-file', str(root / 'positional.json'), '--prompt', 'position ', '--max-tokens', '2')
        require(result['status'] == 'complete' and result['profile']['underlying_model'] == 'Qwen3-8B', 'Positional override changed backend')
        require(len(result['results']) == 2 and result['answer'] == 'QQ', 'Positional override did not generate both decisions')
        for index, generated in enumerate(result['results']):
            config = {**positional, 'vocab_size': 151936, 'start_position': 7 + index}
            require(generated.get('fixture') is True, 'Override lost fixture provenance')
            expected.append({'family': 'qwen', 'prompt': 'position ' + 'Q' * index,
                             'seed': 43, 'watermark': config})

        before = stored()
        cli('models', 'create', '--name', 'invalid', '--underlying-model', 'unknown', error=True)
        cli('complete', '--name', 'unknown profile', '--prompt', 'probe', error=True)
        require(stored() == before, 'Rejected input changed the profile catalog')

        # Backend edits must preserve stable ID, seed, key/settings and prior session snapshots.
        record = records['deepseek marked']
        for family in ('qwen', 'deepseek'):
            updated = json_request(url + '/api/lab/models/' + record['key'], 'PATCH', {'underlying_model': family})
            require(updated == {**record, 'underlying_model': FAMILIES[family]}, 'Backend switch changed profile configuration')
            snapshot = cli('session', 'get', session_id)
            require(snapshot['profile']['underlying_model'] == 'DeepSeekR1', 'Backend edit rewrote an existing session snapshot')
            switched = cli('complete', '--name', record['name'], '--prompt', 'backend round trip ', '--max-tokens', '2')
            require(switched['profile']['underlying_model'] == FAMILIES[family] and len(switched['results']) == 2,
                    'Backend edit did not route new sessions to selected family')
            for index, generated in enumerate(switched['results']):
                require(generated.get('fixture') is True and generated['model'] == FAMILIES[family], 'Edited backend result identity differs')
                expected.append({'family': family, 'prompt': 'backend round trip ' + ('D' if family == 'deepseek' else 'Q') * index,
                                 'seed': record['seed'], 'watermark': record['watermark']})
        require(stored() == before, 'Backend round trip affected other profiles')
        # Each public scheme update retains profile identity/key and can restore exact settings.
        schemes = cli('schemes')
        for family in FAMILIES:
            record = records[family + ' marked']
            for scheme in schemes:
                updated = json_request(url + '/api/lab/models/' + record['key'], 'PATCH', {'scheme': scheme['id']})
                require(all(updated[field] == record[field] for field in ('key', 'name', 'seed', 'seed_literal', 'underlying_model')), 'Scheme update changed profile identity')
                require(updated['watermark']['scheme'] == scheme['id'] and updated['watermark']['key'] == record['watermark']['key'], 'Scheme update lost saved key')
            json_request(url + '/api/lab/models/' + record['key'], 'PATCH',
                         {'scheme': record['watermark']['scheme'], 'settings': record['watermark']})
        require(stored() == before, 'Scheme round trip affected saved settings or other profiles')
        require(len(expected) == 22, 'Checker did not exercise every intended generation decision')
        private_json(root / (phase + '-expected.json'), expected)
        require(not (root / '.models').exists(), 'Checker unexpectedly provisioned weights')
        require(not list(root.glob('.state/*server*.json')), 'Checker unexpectedly started native model processes')
        return {'phase': phase, 'package': package, 'profile_count': len(records), 'generation_requests': len(expected)}


def check(python):
    python = Path(python).absolute()
    require(python.is_file(), 'Installed Python executable does not exist')
    script = Path(__file__).resolve()
    with tempfile.TemporaryDirectory(prefix='ai-lab-cross-model-') as directory, fixtures() as (endpoints, events, health):
        root = Path(directory)
        fixture = root / 'fixture.json'
        private_json(fixture, {'version': 1, 'endpoints': endpoints})
        # Do not forward credentials, provider overrides, source imports or Herdr ownership.
        env = {k: os.environ[k] for k in ('PATH', 'HOME', 'LANG', 'LC_ALL', 'TMPDIR') if k in os.environ}
        env['AI_LAB_GENERATION_FIXTURE_FILE'] = str(fixture)
        phases = []
        for phase in ('create', 'reload', 'reject'):
            offset = len(events)
            health['valid'] = phase != 'reject'
            result = subprocess.run([str(python), '-I', str(script), '--probe', str(root), '--phase', phase],
                                    cwd=root, env=env, capture_output=True, text=True, timeout=180)
            if result.returncode:
                # Child errors contain only this checker's controlled messages or exception type.
                try:
                    reason = json.loads(result.stderr.splitlines()[-1])['error']
                except (ValueError, IndexError, KeyError):
                    reason = 'child output withheld to protect keys'
                raise RuntimeError('Installed ' + phase + ' phase failed: ' + reason)
            phases.append(json.loads(result.stdout))
            actual = events[offset:]
            expected = [] if phase == 'reject' else json.loads((root / (phase + '-expected.json')).read_text())
            require(len(actual) == len(expected), 'Unexpected generation requests, retry or fallback')
            for event, wanted in zip(actual, expected):
                body = event['body']
                require(event['family'] == wanted['family'] and event['path'] == '/v1/completions', 'Generation used wrong endpoint')
                require(body['model'] == 'default' and body['prompt'] == wanted['prompt'], 'Native alias or exact prefix changed')
                require(body.get('seed') == wanted['seed'], 'Seed leaked across profiles')
                require(body.get('watermark') == wanted['watermark'], 'Watermark key/settings leaked or changed')
        return {'status': 'passed', 'fixture': True, 'scope': 'installed CLI/API configuration and transport; synthetic traces, no native inference',
                'phases': phases, 'generation_requests': len(events), 'weights_downloaded': False,
                'native_processes_started': False, 'chat_own_mcp': 'checked separately by check_cross_model_chat.py'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python', help='Python interpreter of the installed AI Lab wheel')
    parser.add_argument('--probe', type=Path, help=argparse.SUPPRESS)
    parser.add_argument('--phase', choices=['create', 'reload', 'reject'], help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        if args.probe:
            value = probe(args.probe, args.phase)
        else:
            require(args.python is not None, '--python is required')
            value = check(args.python)
        print(json.dumps(value, indent=2))
    except Exception as error:
        # Assertion messages are controlled; suppress library/HTTP/CLI payloads containing keys.
        message = str(error) if type(error) is RuntimeError else type(error).__name__
        print(json.dumps({'status': 'failed', 'error': message}), file=sys.stderr)
        sys.exit(1)

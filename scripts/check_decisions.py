#!/usr/bin/env python3
"""Isolated wheel/sdist + mounted Decisions + real loopback HTTP fixture proof.

No model, native inference, SDK, Cargo, external network, or public CLI wiring.
Root/reviewer own the integrated public command check after cherry-picking.
"""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import threading
import zipfile


MODULES = ('decisions_terminal', 'decisions_client', 'decisions_request')
CHILD = r'''
import argparse,asyncio,hashlib,json,os,pathlib,sys
site,root,url,expected=sys.argv[1:]
sys.path.insert(0,site)
from ai_lab import decisions_terminal,decisions_client,decisions_request
from textual.widgets import TabbedContent,TextArea,Switch
hashes=json.loads(expected)
for module in (decisions_terminal,decisions_client,decisions_request):
    path=pathlib.Path(module.__file__)
    assert path.is_relative_to(site)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==hashes[module.__name__.split('.')[-1]]
parser=argparse.ArgumentParser()
decisions_terminal.add_parser(parser.add_subparsers(dest='command',required=True))
args=parser.parse_args(['decisions','--model','Laya (ONNX)'])
assert args.model=='laya' and args.mode=='ask' and not hasattr(args,'name')
async def check():
    client=decisions_client.DecisionsClient(root)
    assert not client.runtime.allow_start
    assert pathlib.Path(__import__('decisions').__file__).is_relative_to(site)
    assert client.runtime.laya_url==url
    app=decisions_terminal.DecisionsApp(client,model=args.model)
    async with app.run_test(size=(80,24)) as pilot:
        async def settle():
            async with asyncio.timeout(10):
                while app.busy or app.discovering: await asyncio.sleep(.01)
                await pilot.pause()
        await settle()
        assert app.selected_model=='laya'
        app.query_one('#state',TextArea).load_text('{"fixture": "built wheel"}')
        app.query_one('#state-json',Switch).value=True
        await pilot.press('ctrl+enter')
        await settle()
        assert app.last_error is None,app.last_error
        assert app.last_result.body['answers']['urgency']['noul']==.2372
        assert app.last_result.body['answers']['urgency']['rl_agent']['act_probability']==.99
        assert json.loads(app.query_one('#response-json',TextArea).text)==app.last_result.body
        await app.load_preset('bestofn')
        await pilot.press('ctrl+enter')
        await settle()
        assert app.last_error is None,app.last_error
        assert app.last_result.body['ranked'][0]['prob']==.8
    assert app.closed and client.closed and not list(pathlib.Path(root).iterdir())
    return {'ask':'passed','rank':'passed','mounted_terminal':[80,24],'shared_backend_from_wheel':True,
            'module_sha256':hashes,'model_starts_or_downloads':False,'owned_tasks_closed':True}
print(json.dumps(asyncio.run(check())))
'''


def check(wheel_path, sdist_path):
    required = {f'ai_lab/{name}.py' for name in MODULES}
    required.update({'ai_lab/_bundle/harness/decisions.py', 'ai_lab/_bundle/harness/clm_upstream.py'})
    with tarfile.open(sdist_path) as archive:
        names = archive.getnames()
        for name in MODULES:
            assert any(path.endswith(f'/ai_lab/{name}.py') for path in names), name
        assert any(path.endswith('/docs/ai-lab/decisions-terminal.md') for path in names)
        assert any(path.endswith('/packaging/check_decisions.py') for path in names)
    posts, gets = [], []

    class Provider(BaseHTTPRequestHandler):
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
            assert self.path == '/v1/models'
            assert self.headers.get('Authorization') is None
            gets.append(self.path)
            self.respond({'models': [{'name': 'laya'}]})

        def do_POST(self):
            assert self.path == '/v1/systemone'
            assert self.headers.get('Authorization') is None
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            posts.append(body)
            answers = {}
            for name, question in body['questions'].items():
                if question['type'] == 'noul':
                    answer = {'type': 'noul', 'noul': .2372}
                else:
                    count = len(question['criteria'])
                    keys = list(question['criteria']) if question['type'] == 'choice' else [str(i) for i in range(count)]
                    probs = {key: 0. for key in keys}
                    probs[keys[0]], probs[keys[-1]] = .2, .8
                    answer = {'type': question['type'], 'probabilities': probs, 'confidence': .2781}
                    if question['type'] == 'choice':
                        answer['choice'] = keys[-1]
                    else:
                        answer['score'] = .8 * (count - 1)
                answers[name] = {**answer, 'rl_agent': {'act_probability': .99}}
            self.respond({'model': 'laya', 'answers': answers, 'usage': {'input_tokens': 10}})

    with tempfile.TemporaryDirectory(prefix='decisions-package-') as folder:
        folder = Path(folder).resolve()
        site, root = folder / 'site', folder / 'data'
        root.mkdir()
        with zipfile.ZipFile(wheel_path) as wheel:
            assert required.issubset(wheel.namelist())
            hashes = {name: hashlib.sha256(wheel.read(f'ai_lab/{name}.py')).hexdigest() for name in MODULES}
            wheel.extractall(site)
        server = ThreadingHTTPServer(('127.0.0.1', 0), Provider)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f'http://127.0.0.1:{server.server_port}'
        environment = {key: value for key, value in os.environ.items()
                       if not key.startswith(('AI_LAB_', 'HERDR_')) and key not in {'JEV_API_KEY', 'TYPESAFE_API_KEY', 'HF_TOKEN', 'DEEPSEEK_ROOT'}}
        environment['AI_LAB_LAYA_URL'] = url
        try:
            result = subprocess.run([sys.executable, '-I', '-c', CHILD, str(site), str(root), url, json.dumps(hashes)],
                                    cwd=folder, env=environment, text=True, capture_output=True, timeout=40)
            if result.returncode:
                raise RuntimeError('Isolated Decisions fixture failed: ' + result.stderr)
            document = json.loads(result.stdout)
            assert len(posts) == 2 and len(gets) == 2
            assert posts[0]['state'] == {'fixture': 'built wheel'}
            assert all(post['model'] == 'laya' for post in posts)
            return {'status': 'passed', 'fixture': True, 'native_inference': False,
                    'transport': 'isolated extracted wheel + shared HTTP routes + actual loopback fake provider',
                    'wheel': str(wheel_path), 'wheel_sha256': hashlib.sha256(wheel_path.read_bytes()).hexdigest(),
                    'sdist': str(sdist_path), 'sdist_sha256': hashlib.sha256(sdist_path.read_bytes()).hexdigest(),
                    'provider_discovery_gets': len(gets), 'decision_posts': len(posts), 'details': document,
                    'public_command_wiring': 'root/reviewer pending integration',
                    'native_proof_attribution': 'No native/model claims; existing runtime artifacts unchanged.'}
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wheel', type=Path, required=True)
    parser.add_argument('--sdist', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(check(args.wheel, args.sdist), indent=2))

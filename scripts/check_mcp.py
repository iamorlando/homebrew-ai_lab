#!/usr/bin/env python3
"""Real packaged MCP stdio smoke in empty roots plus explicit HTTP fixtures.

Does not install user client configs, download models, or start native APIs.
The fixture phase is protocol/package proof, never native model evidence.
"""
import argparse
import asyncio
from contextlib import contextmanager
from datetime import timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@contextmanager
def model_fixture(family):
    requests = []
    class Model(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def respond(self, value):
            data = json.dumps(value).encode()
            self.send_response(200); self.send_header('Content-Type', 'application/json')
            self.end_headers(); self.wfile.write(data)
        def do_GET(self):
            assert self.path == '/v1/models'
            self.respond({'data': [{'id': 'ai-lab-fixture-' + family}]})
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            requests.append((self.path, body))
            assert body.get('model', body.get('input', {}).get('model')) == 'default'
            if self.path == '/v1/completions':
                self.respond({'choices': [{'text': family + ' fixture answer', 'finish_reason': 'stop'}],
                              'usage': {'completion_tokens': 3}})
            elif self.path == '/v1/watermark/detect':
                self.respond({'tokens_scored': 100, 'trials': 100, 'green_count': 75, 'z_score': 5})
            else: raise AssertionError(self.path)
    server = ThreadingHTTPServer(('127.0.0.1', 0), Model)
    worker = threading.Thread(target=server.serve_forever, daemon=True); worker.start()
    try: yield f'http://127.0.0.1:{server.server_port}', requests
    finally:
        server.shutdown(); server.server_close(); worker.join(timeout=2)


async def phase(root, entry, *, fixture=False):
    env = {**entry['env'], 'TYPESAFE_API_KEY': '', 'JEV_API_KEY': '',
           'AI_LAB_LAYA_URL': 'http://127.0.0.1:1', 'AI_LAB_DECISIONS_URL': 'http://127.0.0.1:1',
           'AI_LAB_CLM_UPSTREAM_URL': 'http://127.0.0.1:1',
           'UV_CACHE_DIR': str(Path(os.environ.get('UV_CACHE_DIR', root.parent / 'uv-cache'))),
           'UV_TOOL_DIR': str(root.parent / 'uv-tools')}
    if fixture: env['AI_LAB_GENERATION_FIXTURE_FILE'] = str(root / 'generation-fixture.json')
    async with stdio_client(StdioServerParameters(command=entry['command'], args=entry['args'], env=env)) as (read, write):
        async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=120)) as session:
            await session.initialize()
            catalog = await session.list_tools()
            names = {tool.name for tool in catalog.tools}
            assert {'generate_text', 'answer_decisions', 'detect_watermark', 'create_seeded_model',
                    'create_watermarked_model', 'update_watermarked_model', 'inspect_next_token'} <= names
            async def call(name, arguments=None, error=False):
                result = await session.call_tool(name, arguments or {})
                assert bool(result.isError) == error, (name, result)
                if error: return '\n'.join(getattr(item, 'text', '') for item in result.content)
                return result.structuredContent or json.loads(result.content[0].text)
            models = await call('list_models')
            assert {'jev', 'deepseek', 'contrastive'} == {r['name'] for r in models['models']}
            assert models['default_decision_model'] == 'jev'
            for tool in catalog.tools:
                assert 'qwen' not in json.dumps(tool.inputSchema).lower()
            await call('create_seeded_model', {'name': 'Unsupported Qwen', 'seed': 1, 'underlying_model': 'qwen'}, error=True)
            await call('download_models', {'models': ['qwen']}, error=True)
            for family in ('deepseek',):
                row = next(r for r in models['models'] if r['name'] == family)
                assert row['run_command'] == 'ai-lab web'
                assert row['install_command'] == f'ai-lab setup install {family} --yes'
            assert len((await call('explain_watermarks'))['schemes']) == 6
            seeded = await call('create_seeded_model', {'name': 'MCP seed', 'seed': '0x2A'})
            assert seeded['seed'] == 42 and seeded['underlying_model'] == 'DeepSeekR1'
            profiles = {}
            for family, canonical in [('deepseek', 'DeepSeekR1')]:
                wm = await call('create_watermarked_model', {'name': 'MCP '+family, 'scheme': 'kgw',
                    'seed': 42, 'underlying_model': family, 'key': '42'*32})
                profiles[family] = wm
                assert wm['underlying_model'] == canonical and wm['watermark']['has_key']
                assert '42'*32 not in json.dumps(wm)
                config = await call('get_model_config', {'model': wm['key'], 'include_watermark_key': True})
                assert config['watermark']['key'] == '42'*32
                updated = await call('update_watermarked_model', {'model': wm['key'], 'settings': {'delta': 4}})
                assert updated['watermark']['delta'] == 4 and '42'*32 not in json.dumps(updated)
                assert '42'*32 not in json.dumps(await call('get_model_config', {'model': wm['name']}))
                if fixture:
                    generated = await call('generate_text', {'model': wm['name'], 'prompt': 'Hello', 'max_tokens': 4})
                    assert generated['answer'] == family+' fixture answer' and generated['fixture'] is True
                    assert generated['underlying_model'] == canonical and generated['profile_key'] == wm['key']
                    assert generated['seed'] == 42 and generated['watermark']['delta'] == 4
                    assert '42'*32 not in json.dumps(generated)
                    override = await call('generate_text', {'model': wm['key'], 'prompt': 'Hello', 'key': '23'*32})
                    assert '23'*32 not in json.dumps(override)
                    off = await call('generate_text', {'model': wm['key'], 'prompt': 'Hello', 'scheme': 'none'})
                    assert off['watermark'] is None
                    config = await call('get_model_config', {'model': wm['key'], 'include_watermark_key': True})
                    assert config['watermark']['key'] == '42'*32
                    detected = await call('detect_watermark', {'text': 'External text', 'model': wm['key']})
                    assert detected['fixture'] is True and detected['underlying_model'] == canonical
                    assert detected['verdict'] == 'match' and '42'*32 not in json.dumps(detected)
                else:
                    for name, args in [('generate_text', {'prompt': 'Hello', 'model': wm['key']}),
                                       ('detect_watermark', {'text': 'External text', 'model': wm['key']}),
                                       ('inspect_next_token', {'prompt': 'Exact prefix', 'model': wm['key']})]:
                        assert 'ai-lab setup' in await call(name, args, error=True)
            assert root.joinpath('harness/models.json').stat().st_mode & 0o777 == 0o600
            assert 'ai-lab setup' in await call('answer_decisions', {'model': 'contrastive', 'state': 'test',
                     'questions': {'ok': {'type': 'noul'}}}, error=True)
            assert 'Jev needs' in await call('answer_decisions', {'state': 'test', 'questions': {'ok': {'type': 'noul'}}}, error=True)
            assert (await call('list_results'))['results'] == []
            assert not (root / '.models').exists()
            assert not list(root.glob('.state/*server*.json'))
            return names


async def check(executable=None):
    def entry(root):
        if executable:
            configured = subprocess.run([executable, '--root', str(root), 'mcp', 'config', '--codex', '--config-file', str(root.parent / (root.name + '-codex.toml')), '--json'],
                                        capture_output=True, text=True, check=True)
            return json.loads(configured.stdout)['entry']
        from ai_lab.mcp_install import launch_config
        return launch_config(root)
    with tempfile.TemporaryDirectory(prefix='ai-lab-mcp-check-') as folder:
        base = Path(folder).resolve(); empty = base / 'empty'; fixture = base / 'fixture'
        tools = await phase(empty, entry(empty))
        with model_fixture('deepseek') as (deepseek_url, deepseek_requests):
            fixture.mkdir()
            (fixture/'generation-fixture.json').write_text(json.dumps({'version': 1, 'endpoints': {
                'deepseek': deepseek_url}}))
            await phase(fixture, entry(fixture), fixture=True)
            for family, requests in [('deepseek', deepseek_requests)]:
                generations = [body for path, body in requests if path == '/v1/completions']
                assert len(generations) == 3
                assert generations[0]['watermark']['key'] == '42'*32
                assert generations[1]['watermark']['key'] == '23'*32
                assert 'watermark' not in generations[2]
                assert '<think>' in generations[0]['prompt']
    return {'status': 'passed', 'transport': 'real stdio', 'launcher': 'uvx', 'tool_count': len(tools),
            'tools': sorted(tools), 'fixture': True, 'native_inference_proof': False,
            'checked': ['empty-workspace no-download/no-start', 'DeepSeek catalog and standalone Qwen rejection',
                        'generation and detector family routing', 'private keys and explicit key retrieval',
                        'saved inheritance and unsaved override/disable', 'both missing-backend setup instructions']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable', help='Exercise an installed ai-lab CLI and its packaged installer')
    args = parser.parse_args()
    print(json.dumps(asyncio.run(check(args.executable)), indent=2))

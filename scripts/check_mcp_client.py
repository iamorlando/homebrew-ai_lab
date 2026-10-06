#!/usr/bin/env python3
"""Prove the built wheel's own MCP connector against a local HTTP fixture.

This is package + real MCP protocol proof, not native decision/model inference.
The default extracts the wheel; --installed verifies a separately installed
copy under this interpreter against the same wheel bytes. This probe itself
installs nothing and needs no model download/start, hosted key or user config.
"""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import threading
import zipfile


CLIENT = '''
import asyncio, hashlib, json, pathlib, sys
site, root, url, connector_hash, schema_hash = sys.argv[1:]
if site: sys.path.insert(0, site)
import ai_lab.mcp_client as connector
import ai_lab.mcp_schema as schemas
from jsonschema import Draft202012Validator
if site:
    assert pathlib.Path(connector.__file__).is_relative_to(site)
    assert pathlib.Path(schemas.__file__).is_relative_to(site)
assert hashlib.sha256(pathlib.Path(connector.__file__).read_bytes()).hexdigest()==connector_hash
assert hashlib.sha256(pathlib.Path(schemas.__file__).read_bytes()).hexdigest()==schema_hash
async def check():
    async with connector.ai_lab_client(root, allow_tools=('answer_decisions',),
            env={'AI_LAB_LAYA_URL':url}) as client:
        catalog = client.catalog()
        functions = [t['function'] for t in client.model_tools()]
        assert len(catalog)==len(functions)==15
        assert all(f['strict'] is True for f in functions)
        assert {f['name'] for f in functions}=={t['name'] for t in catalog}
        # Match the pinned native json_body_schema envelope: local pointers
        # originally resolved against its root instead of nested arguments.
        native = Draft202012Validator({'anyOf':[{'type':'object','properties':{
            'name':{'const':f['name']}, 'arguments':f['parameters']},
            'required':['name','arguments']} for f in functions]})
        tool = next(t for t in catalog if t['tool']=='answer_decisions')
        assert tool['inputSchema']['properties']['questions']['additionalProperties']=={'$ref':'#/$defs/DecisionQuestion'}
        original = Draft202012Validator(tool['inputSchema'])
        valid = {'model':'laya', 'state':'package fixture', 'questions':{'ok':{'type':'noul'}}}
        accepted = [valid, {**valid,'questions':{'任意/key~':{'type':'choice','instructions':None,
                     'criteria':{'one':'first','two':'second'}}}}]
        rejected = [{**valid,'questions':json.dumps(valid['questions'])+'"'},
            {**valid,'questions':{'ok':{'type':'unknown'}}},
            {**valid,'questions':{'ok':{}}},
            {**valid,'questions':{'ok':{'type':'noul','extra':True}}},
            {**valid,'questions':{'ok':{'type':'noul','criteria':'text'}}},
            {**valid,'model':'jev'}, {k:v for k,v in valid.items() if k!='model'}]
        for expected, values in ((True,accepted),(False,rejected)):
            for args in values:
                assert original.is_valid(args)==expected
                assert native.is_valid({'name':tool['name'],'arguments':args})==expected
        for args in rejected:
            invalid=await client.call_tool(tool['name'],args)
            assert invalid['error']['code']=='invalid_arguments'
        result = await client.call_tool(tool['name'], valid)
        assert result['status']=='ok', result
        data = result['structuredContent'] or json.loads(result['content'][0]['text'])
        assert data['provider']=='laya' and data['answers']['ok']['noul']==0.8
        denied = await client.call_tool(tool['name'], {'state':'must not default to hosted',
                'questions':{'ok':{'type':'noul'}}})
        assert denied['error']['code']=='invalid_arguments'
        return {'tool_count':len(catalog), 'strict_functions':len(functions),
                'original_vs_native_schema_cases':len(accepted)+len(rejected),
                'invalid_calls_rejected_before_dispatch':len(rejected)+1,
                'provider':'laya', 'noul':data['answers']['ok']['noul']}
print(json.dumps(asyncio.run(check())))
'''


def check(wheel_path, sdist_path=None, *, installed=False):
    import hashlib
    posts = []
    class Provider(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def respond(self, data):
            payload = json.dumps(data).encode()
            self.send_response(200); self.send_header('Content-Type', 'application/json')
            self.end_headers(); self.wfile.write(payload)
        def do_GET(self):
            assert self.path == '/v1/models'
            self.respond({'models': [{'name': 'laya'}]})
        def do_POST(self):
            assert self.path == '/v1/systemone'
            data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            posts.append((data, self.headers.get('Authorization')))
            self.respond({'model': 'laya', 'answers': {'ok': {'type': 'noul', 'noul': .8}},
                          'usage': {'input_tokens': 3}})

    if sdist_path:
        with tarfile.open(sdist_path) as archive:
            assert any(p.endswith('/ai_lab/mcp_client.py') for p in archive.getnames())
            assert any(p.endswith('/ai_lab/mcp_schema.py') for p in archive.getnames())
            assert any(p.endswith('/docs/ai-lab/mcp-client.md') for p in archive.getnames())
    with tempfile.TemporaryDirectory(prefix='ai-lab-packaged-client-') as folder:
        base = Path(folder).resolve(); site, root = base / 'site', base / 'empty-data'
        with zipfile.ZipFile(wheel_path) as wheel:
            assert 'ai_lab/mcp_client.py' in wheel.namelist()
            assert 'ai_lab/mcp_schema.py' in wheel.namelist()
            connector_hash = hashlib.sha256(wheel.read('ai_lab/mcp_client.py')).hexdigest()
            schema_hash = hashlib.sha256(wheel.read('ai_lab/mcp_schema.py')).hexdigest()
            metadata_name = next(n for n in wheel.namelist() if n.endswith('.dist-info/METADATA'))
            metadata = wheel.read(metadata_name).decode()
            requirements = [line for line in metadata.splitlines() if line.startswith('Requires-Dist:')]
            assert 'Requires-Dist: mcp==1.30.0' in requirements
            assert 'Requires-Dist: jsonschema==4.26.0' in requirements
            assert 'Provides-Extra: mcp' in metadata
            assert not any('/.state/' in n or '/.models/' in n or 'test-private-credential' in n
                           for n in wheel.namelist())
            wheel.extractall(site)
        server = ThreadingHTTPServer(('127.0.0.1', 0), Provider)
        worker = threading.Thread(target=server.serve_forever, daemon=True); worker.start()
        try:
            environment = {**os.environ, 'JEV_API_KEY': '', 'TYPESAFE_API_KEY': ''}
            result = subprocess.run([sys.executable, '-I', '-c', CLIENT, '' if installed else str(site), str(root),
                                     f'http://127.0.0.1:{server.server_port}', connector_hash, schema_hash], cwd=base,
                                    env=environment, capture_output=True, text=True, timeout=30)
            if result.returncode:
                raise RuntimeError('Packaged MCP client check failed: ' + result.stderr)
            evidence = json.loads(result.stdout)
            assert len(posts) == 1 and posts[0][0]['model'] == 'laya' and posts[0][1] is None
            assert not (root / '.models').exists()
            assert not list(root.glob('.state/*server*.json'))
            return {'status': 'passed', 'transport': 'real stdio',
                    'client': 'installed built wheel' if installed else 'extracted built wheel',
                    'model_provider': 'local HTTP fixture (not native inference)',
                    'hosted_key_required': False, 'model_downloads_or_starts': False,
                    'source_package_checked': sdist_path is not None, **evidence}
        finally:
            server.shutdown(); server.server_close(); worker.join(timeout=2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wheel', required=True, type=Path)
    parser.add_argument('--sdist', type=Path)
    parser.add_argument('--installed', action='store_true', help='Verify installed modules match the supplied wheel')
    args = parser.parse_args()
    print(json.dumps(check(args.wheel, args.sdist, installed=args.installed), indent=2))

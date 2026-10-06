#!/usr/bin/env python3
"""Offline extracted/installed wheel proof: mounted Textual + actual shared routes.

Detector HTTP is MockTransport with explicit fixture endpoints and synthetic
statistics. This is package/terminal/route proof, never native inference proof.
No installation, sockets, SDK, model hashing, downloads or starts occur here.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import zipfile

MODULES = ['ai_lab/decoder_terminal.py', 'ai_lab/decoder_app.py', 'ai_lab/decoder_service.py',
           'ai_lab/decoder_evidence.py', 'ai_lab/_bundle/harness/detection_lab.py']
CLIENT = r'''
import argparse, asyncio, hashlib, json, pathlib, shutil, sys
from unittest.mock import patch
site, folder, hashes_json = sys.argv[1:]
if site: sys.path.insert(0, site)
import ai_lab.decoder_terminal as terminal
import ai_lab.decoder_app as ui
import ai_lab.decoder_service as service_module
import ai_lab.decoder_evidence as evidence
from ai_lab.paths import RESOURCES, load_backend
load_backend(RESOURCES)
import detection_lab
from model_profiles import ModelProfiles, profile_values
from watermarks import validate_watermark
from watermark_runtime import WatermarkRuntime
from textual import events
from textual.widgets import Button, Input, Select, TextArea
import httpx
modules = [terminal, ui, service_module, evidence, detection_lab]
for module, (name, expected) in zip(modules, json.loads(hashes_json).items()):
    path=pathlib.Path(module.__file__).resolve()
    if site: assert path.is_relative_to(pathlib.Path(site))
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, name
root=pathlib.Path(folder)/'data'; root.mkdir(); (root/'harness').mkdir()
shutil.copyfile(RESOURCES/'sources.json',root/'sources.json')
key='42'*32
registry=ModelProfiles(root)
registry.path.write_text(json.dumps(registry.document({
    'deep':profile_values('Exact DeepSeek',42,'deepseek',validate_watermark({'scheme':'synthid','key':key,'depth':6})),
    'qwen':profile_values('Exact Qwen',None,'qwen',validate_watermark({'scheme':'kgw','key':key,'context_width':3}))})))
before={p:p.read_bytes() for p in root.rglob('*') if p.is_file()}
calls=[]
def respond(request):
    family='deepseek' if request.url.port==18885 else 'qwen'
    if request.method=='GET': return httpx.Response(200,json={'data':[{'id':'ai-lab-fixture-'+family}]})
    assert request.url.path=='/v1/watermark/detect'
    body=json.loads(request.content); calls.append((family,body))
    assert body['watermark']['key']==key
    return httpx.Response(200,json={'tokens_scored':3 if body['input']['text']=='SHORT' else 100,
        'mean_g_value':.8,'z_score':6,'green_count':80,'key':key})
async def check():
    runtime=WatermarkRuntime(allow_start=False, fixture_endpoints={'deepseek':'http://127.0.0.1:18885','qwen':'http://127.0.0.1:18886'},transport=httpx.MockTransport(respond))
    parser=argparse.ArgumentParser(); parser.add_argument('--json',action='store_true')
    terminal.add_parser(parser.add_subparsers(dest='command'))
    assert parser.parse_args(['decoder']).name is None
    for argv in (['--json','decoder'],['decoder','--json'],['decoder']):
        try: terminal.run(parser.parse_args(argv),root)
        except ValueError: pass
        else: raise AssertionError('must reject JSON/nonTTY before startup')
    with patch('ai_lab.mcp_tools.prepare',side_effect=AssertionError('no provisioning')), \
         patch('watermark_runtime.inference.start',side_effect=AssertionError('no start')), \
         patch('watermark_runtime.inference.sha256',side_effect=AssertionError('no model hashing')), \
         patch('ai_lab.mcp_tools.install',side_effect=AssertionError('no download')):
        service=service_module.DecoderService(root,runtime=runtime)
        app=ui.DecoderApp(service,name='Exact DeepSeek')
        async with app.run_test(size=(110,38)) as pilot:
            await pilot.pause(); await app.workers.wait_for_complete(); await pilot.pause()
            assert not calls and app.profile()['id']=='deep' and app.query_one('#field-depth',Input).value=='6'
            text='  Package fixture text\n'
            editor=app.query_one('#text',TextArea); editor.load_text(text)
            await pilot.pause()
            app.action_decode(); app.action_cancel()
            assert not app._busy and not app.query_one('#decode',Button).disabled
            await pilot.pause(); await app.workers.wait_for_complete(); await pilot.pause()
            assert not calls and editor.text==text
            app.query_one('#decode',Button).focus(); await pilot.pause()
            dispatch=app.run_worker; entry_gate=asyncio.Event()
            def queued_dispatch(work,**kwargs):
                if kwargs.get('group')=='detect':
                    async def queued():
                        await entry_gate.wait()
                        return await work()
                    return dispatch(queued,**kwargs)
                return dispatch(work,**kwargs)
            with patch.object(app,'run_worker',side_effect=queued_dispatch):
                app.post_message(events.Key('ctrl+d',None)); app.post_message(events.Key('escape',None))
                await pilot.pause(); await app.workers.wait_for_complete(); await pilot.pause()
            assert not app._busy and not calls and editor.text==text
            editor.focus(); await pilot.pause(); await pilot.press('ctrl+d')
            await app.workers.wait_for_complete(); await pilot.pause()
            assert editor.text==text and len(calls)==1 and calls[0][1]['input']['text']==text
            assert app.last_result['verdict']=='match' and app.last_result['fixture'] is True
            assert app.last_result['confidence']==1-app.last_result['p_value']
            assert key not in app.query_one('#raw',TextArea).text
            app.query_one('#model',Select).value='qwen'; await pilot.pause()
            assert app.query_one('#text',TextArea).text=='  Package fixture text\n'
            assert app.query_one('#field-context_width',Input).value=='3'
            app.action_decode(); await app.workers.wait_for_complete(); await pilot.pause()
            assert calls[-1][0]=='qwen'
            app.query_one('#text',TextArea).load_text('SHORT'); await pilot.pause()
            app.action_decode(); await app.workers.wait_for_complete(); await pilot.pause()
            assert app.last_result['verdict']=='insufficient'
            assert app.last_result['confidence'] is None and app.last_result['p_value'] is None
            assert '<svg' in app.export_screenshot()
            await pilot.press('ctrl+q')
        assert service.closed
        await service.app.state.decoder_tools.close()
    assert all(p.read_bytes()==value for p,value in before.items())
    assert not (root/'.models').exists()
    assert {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}=={
        'harness/models.json','sources.json','.state/ai-lab/configuration.lock'}
    return {'profiles':2,'backends':['deepseek','qwen'],'mounted':True,'detector_posts':len(calls),
        'pre_entry_cancel_retry':True,'focused_editor_shortcut':True,
        'insufficient_confidence':None,'profiles_unchanged':True,'models_started_or_downloaded':False}
print(json.dumps(asyncio.run(check())))
'''


def check(wheel_path, sdist_path=None, *, installed=False):
    if sdist_path:
        with tarfile.open(sdist_path) as archive:
            names = archive.getnames()
            for suffix in ('/ai_lab/decoder_terminal.py', '/ai_lab/decoder_app.py',
                           '/docs/ai-lab/decoder.md', '/packaging/check_decoder.py'):
                assert any(name.endswith(suffix) for name in names), suffix
    with tempfile.TemporaryDirectory(prefix='packaged-decoder-') as folder:
        folder = Path(folder).resolve()
        site = folder / 'site'
        with zipfile.ZipFile(wheel_path) as wheel:
            hashes = {name: hashlib.sha256(wheel.read(name)).hexdigest() for name in MODULES}
            assert not any('/.state/' in name or '/.models/' in name for name in wheel.namelist())
            wheel.extractall(site)
        environment = {k: v for k, v in os.environ.items() if not k.startswith(('HERDR_', 'AI_LAB_', 'DEEPSEEK_', 'JEV_', 'TYPESAFE_'))}
        process = subprocess.run([sys.executable, '-I', '-c', CLIENT, '' if installed else str(site), str(folder), json.dumps(hashes)],
                                 cwd=folder, env=environment, capture_output=True, text=True, timeout=40)
        if process.returncode:
            raise RuntimeError('Packaged decoder check failed: ' + process.stderr)
        return {'status': 'passed', 'package': 'installed wheel' if installed else 'extracted wheel',
                'isolated_python': True, 'source_distribution_checked': sdist_path is not None,
                'attribution': 'Actual ASGI routes and native HTTP adapter; CPU fake detector statistics, not native inference',
                **json.loads(process.stdout)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wheel', required=True, type=Path)
    parser.add_argument('--sdist', type=Path)
    parser.add_argument('--installed', action='store_true')
    args = parser.parse_args()
    print(json.dumps(check(args.wheel, args.sdist, installed=args.installed), indent=2))

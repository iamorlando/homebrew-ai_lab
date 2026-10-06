#!/usr/bin/env python3
"""Built-package UI/native-wire/own-MCP fixtures; this is not native inference."""
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


CHILD = r'''
import asyncio,contextlib,hashlib,io,json,pathlib,sys
site,root,deepseek_url,qwen_url,laya_url=sys.argv[1:]
sys.path.insert(0,site)
from ai_lab.agent_backend import AgentBackend
from ai_lab.agent_tui import AgentChatApp,ApprovalScreen
from ai_lab.herdr import HerdrReporter
from ai_lab.native_chat import NativeChat
from ai_lab.cli import main
assert pathlib.Path(__import__('ai_lab.agent_backend',fromlist=['']).__file__).is_relative_to(site)
with contextlib.redirect_stdout(io.StringIO()) as out:
    assert main(['help','--json'])==0
    commands=json.loads(out.getvalue())['commands']
    assert 'agent' in commands and 'agent-prompt' in commands
async def check():
    results=[]
    for family,expected in [('deepseek','DeepSeekR1'),('qwen','Qwen3-8B')]:
        chat=NativeChat(root,family,seed=42,fixture_endpoints={'deepseek':deepseek_url,'qwen':qwen_url})
        backend=AgentBackend(root,chat=chat,self_mcp=True,
                             mcp_env={'AI_LAB_LAYA_URL':laya_url})
        assert (chat.temperature,chat.max_tokens,chat.timeout)==(.8,1024,180)
        assert backend.timeout==180
        app=AgentChatApp(backend,profile_label=backend.profile_label,backend_label=backend.backend_label,
                         reporter=HerdrReporter('package-fixture-'+family,environment={}),
                         close_callback=backend.aclose)
        async with app.run_test(size=(80,18)) as pilot:
            client=await backend._connect()
            catalog=client.catalog()
            tools=client.model_tools()
            assert len(catalog)==len(tools)==15
            assert all(tool['function']['strict'] is True for tool in tools)
            assert {tool['function']['name'] for tool in tools}=={tool['name'] for tool in catalog}
            tools_hash=hashlib.sha256(json.dumps(tools,sort_keys=True).encode()).hexdigest()
            assert app.tool_choice=='auto'
            if family=='deepseek':
                await pilot.press('ctrl+t')
                assert app.tool_choice=='required'
            async def settle():
                async with asyncio.timeout(30):
                    while app.busy:
                        if isinstance(app.screen,ApprovalScreen):
                            await pilot.pause()
                            assert 'ai-lab: answer_decisions' in app.screen.message and '"laya"' in app.screen.message
                            screen=app.screen
                            assert await pilot.click('#allow')
                            while app.screen is screen and app.busy: await asyncio.sleep(.01)
                        else:
                            await asyncio.sleep(.01)
                assert app.last_error is None
            await pilot.press(*list('first packaged turn'),'enter')
            await settle()
            assert app.history[-1]['role']=='assistant' and 'fixture continuation' in app.history[-1]['content']
            assert [m['role'] for m in app.history]==['user','assistant','tool','assistant']
            first_history=list(app.history)
            if family=='deepseek':
                await pilot.press('ctrl+t')
                assert app.tool_choice=='auto'
            await app.send_prompt('second packaged turn')
            await settle()
            assert app.history[:len(first_history)]==first_history
            assert len(app.history)==8 and app.history[-1]['role']=='assistant'
            assert backend.selection['underlying_model']==expected and backend.last_result['fixture']
            assert backend.selection['seed']==42
            results.append({'family':family,'underlying_model':expected,'turns':2,
                            'history_messages':len(app.history),'fixture':True,
                            'discovered_tools':len(catalog),'tools_sha256':tools_hash,
                            'first_user_turn_choice':'required' if family=='deepseek' else 'auto',
                            'second_user_turn_choice':'auto', 'mounted_public_allow':True,
                            'shipped_defaults':{'temperature':chat.temperature,'max_tokens':chat.max_tokens,
                                                'timeout':chat.timeout}})
        assert backend._closed and backend._client is None and chat._closed
    assert not (pathlib.Path(root)/'.models').exists()
    return results
print(json.dumps(asyncio.run(check())))
'''


def check(wheel_path, sdist_path):
    required={'ai_lab/agent.py','ai_lab/agent_backend.py','ai_lab/agent_tui.py',
              'ai_lab/agent_channel.py','ai_lab/agent_prompt.py','ai_lab/herdr.py',
              'ai_lab/native_chat.py','ai_lab/mcp_client.py','ai_lab/mcp_schema.py'}
    with tarfile.open(sdist_path) as archive:
        names=archive.getnames()
        for path in required:
            assert any(name.endswith('/'+path) for name in names),path
    decisions,requests=[],[]
    class Provider(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def respond(self,value):
            data=json.dumps(value).encode();self.send_response(200)
            self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(data)
        def do_GET(self): self.respond({'models':[{'name':'laya'}]})
        def do_POST(self):
            body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            decisions.append(body);assert self.headers.get('Authorization') is None
            self.respond({'model':'laya','answers':{'ok':{'type':'noul','noul':.8}},'usage':{'input_tokens':3}})
    def generation(family):
        class Generation(BaseHTTPRequestHandler):
            def log_message(self,*args): pass
            def respond(self,value):
                data=json.dumps(value).encode();self.send_response(200)
                self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(data)
            def do_GET(self): self.respond({'data':[{'id':'ai-lab-fixture-'+family}]})
            def do_POST(self):
                import hashlib
                body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                requests.append({'family':family,'messages':body['messages'],'seed':body.get('seed'),
                    'tool_choice':body.get('tool_choice'),
                    'tools_sha256':hashlib.sha256(json.dumps(body['tools'],sort_keys=True).encode()).hexdigest()})
                assert self.path=='/v1/chat/completions' and body['model']=='default' and body['stream'] is False
                assert self.headers.get('Authorization') is None
                assert body['temperature']==.8 and body['max_tokens']==1024
                family_count=sum(request['family']==family for request in requests)
                assert body['tool_choice']==('required' if family=='deepseek' and family_count==1 else 'auto')
                assert len(body['tools'])==15 and all(t['function']['strict'] is True for t in body['tools'])
                if body['messages'][-1]['role']=='tool':
                    result=json.loads(body['messages'][-1]['content'])
                    assert result['status']=='ok'
                    message={'role':'assistant','content':'Packaged fixture continuation after actual own MCP local result.'}
                else:
                    tool=next(t for t in body['tools'] if 'answer_decisions' in t['function']['name'])
                    message={'role':'assistant','content':None,'tool_calls':[{'id':'fixture-'+family+'-'+str(len(requests)),
                        'type':'function','function':{'name':tool['function']['name'],'arguments':json.dumps({
                            'model':'laya','state':'package fixture','questions':{'ok':{'type':'noul'}}})}}]}
                self.respond({'choices':[{'message':message,'finish_reason':'stop'}],'usage':{'completion_tokens':4}})
        return Generation
    servers=[];threads=[]
    with tempfile.TemporaryDirectory(prefix='item1-packaged-fixture-') as folder:
        site=Path(folder)/'site';root=Path(folder)/'data'
        with zipfile.ZipFile(wheel_path) as wheel:
            assert required.issubset(wheel.namelist())
            wheel.extractall(site)
        try:
            for handler in (generation('deepseek'),generation('qwen'),Provider):
                server=ThreadingHTTPServer(('127.0.0.1',0),handler)
                thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
                servers.append(server);threads.append(thread)
            urls=[f'http://127.0.0.1:{s.server_port}' for s in servers]
            environment={key:value for key,value in os.environ.items()
                         if key not in {'AI_LAB_GENERATION_FIXTURE_FILE','JEV_API_KEY','TYPESAFE_API_KEY','HF_TOKEN'}}
            result=subprocess.run([sys.executable,'-I','-c',CHILD,str(site),str(root),*urls],
                                  cwd=folder,env=environment,capture_output=True,text=True,timeout=90)
            if result.returncode: raise RuntimeError('Packaged agent fixture failed: '+result.stderr)
            data=json.loads(result.stdout)
            assert len(decisions)==4 and all(d['model']=='laya' for d in decisions)
            assert len(requests)==8 and all(r['seed']==42 for r in requests)
            for family in ('deepseek','qwen'):
                family_requests=[r for r in requests if r['family']==family]
                assert len(family_requests[-1]['messages'])==8
                actual=next(row for row in data if row['family']==family)
                assert all(r['tools_sha256']==actual['tools_sha256'] for r in family_requests)
                assert [r['tool_choice'] for r in family_requests]==(['required','auto','auto','auto'] if family=='deepseek' else ['auto']*4)
            return {'status':'passed','fixture':True,'native_inference':False,'wheel':str(wheel_path),
                    'sdist':str(sdist_path),'modules_checked':sorted(required),'families':data,
                    'transport':'actual built wheel UI + HTTP model fixtures + own stdio MCP + local HTTP decision fixture',
                    'actual_mcp_decision_calls':len(decisions),'model_wire_requests':len(requests),
                    'full_catalog_strict_wire_verified':True,
                    'explicit_required_first_then_auto_fixture_verified':True,
                    'shipped_defaults':{'temperature':.8,'max_tokens':1024,'timeout':180,'tool_choice':'auto'},
                    'hosted_key_required':False,'model_downloads_or_starts':False,'owned_children_closed':True}
        finally:
            for server in servers: server.shutdown();server.server_close()
            for thread in threads: thread.join(timeout=2)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wheel',type=Path,required=True)
    parser.add_argument('--sdist',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(check(args.wheel,args.sdist),indent=2))

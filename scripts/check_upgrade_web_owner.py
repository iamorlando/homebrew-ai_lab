"""Keep an actual prior web owner across an installation, then restart the candidate.

Only owned loopback Python providers are used; no native runtime or model request.
Run with an installed Python outside the checkout. The command after -- performs
an authorized upgrade in the same installation, preserving the supplied data root.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import time
from urllib.request import ProxyHandler, build_opener

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--executable', required=True)
p.add_argument('--root', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--web-checker', type=Path, required=True)
p.add_argument('command', nargs=argparse.REMAINDER)
a = p.parse_args(); command = a.command[1:] if a.command[:1] == ['--'] else a.command
assert command, 'An explicit upgrade command is required'
root = a.root.resolve(); out = a.output.resolve(); out.mkdir(parents=True, exist_ok=False)
spec = importlib.util.spec_from_file_location('installed_web_checker', a.web_checker)
checker = importlib.util.module_from_spec(spec); spec.loader.exec_module(checker)
env = {k:v for k,v in os.environ.items() if not k.startswith(('AI_LAB_','JEV_','TYPESAFE_')) and k not in ('PYTHONPATH','PYTHONHOME')}
http = build_opener(ProxyHandler({})); events=[]
before = (root/'harness/models.json').read_bytes()
with socket.socket() as sock: sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]
base = 'http://127.0.0.1:' + str(port)
argv = [a.executable,'--root',str(root),'web','--port',str(port),'--no-browser','--json']

def call(path):
    with http.open(base+path,timeout=5) as r:return r.read()
def version():return subprocess.check_output([a.executable,'--version'],cwd=out,env=env,text=True).strip()
def start(label):
    log=(out/(label+'.log')).open('w')
    process=subprocess.Popen(argv,cwd=out,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=log)
    deadline=time.monotonic()+60
    try:
        while time.monotonic()<deadline:
            assert process.poll() is None, (out/(label+'.log')).read_text()
            try:
                body=json.loads(call('/api/workspace'))
                assert body['root']==str(root) and body['runtime_mode']=='fixture'
                events.append(dict(event=label,pid=process.pid));return process,log
            except OSError:time.sleep(.1)
        raise TimeoutError(label+' readiness')
    except BaseException:
        stop(process,log);raise

def stop(process,log):
    if process.poll() is None:
        process.send_signal(signal.SIGINT)
        try:process.wait(timeout=20)
        except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=10)
    log.close()
    with socket.socket() as s:assert s.connect_ex(('127.0.0.1',port))!=0, 'Owned web socket leaked'

try:
    assert version()=='AI Lab 0.1.15'
    with checker.owned_api_fixtures(out) as (endpoints,providers):
        fixture=out/'generation.json';fixture.write_text(json.dumps({'version':1,'endpoints':{'deepseek':endpoints['deepseek']}}))
        env.update(AI_LAB_GENERATION_FIXTURE_FILE=str(fixture),AI_LAB_DECISIONS_URL=endpoints['contrastive'])
        old,oldlog=start('prior-owner')
        try:
            completed=subprocess.run(command,cwd=out,env=os.environ.copy(),capture_output=True,text=True,timeout=1200)
            (out/'upgrade.log').write_text(completed.stdout+completed.stderr)
            events.append(dict(event='literal-upgrade',command=command,exit=completed.returncode))
            assert completed.returncode==0
            assert version()=='AI Lab 0.1.16'
            assert old.poll() is None
            assert json.loads(call('/api/workspace'))['root']==str(root)
            reused=subprocess.run(argv,cwd=out,env=env,capture_output=True,text=True,timeout=30)
            assert reused.returncode==0 and json.loads(reused.stdout)['existing'] is True
            events.append(dict(event='retained-prior-owner',pid=old.pid,existing=True))
            assert all(process.poll() is None for process in providers.values())
        finally:stop(old,oldlog)
        new,newlog=start('candidate-owner')
        try:
            assert b'textgrain.js' in call('/pair-assets/completion-watermark.js')
            assert all(process.poll() is None for process in providers.values())
            assert (root/'harness/models.json').read_bytes()==before
        finally:stop(new,newlog)
    result=dict(status='PASS',events=events,prior_version='0.1.15',version='0.1.16',profiles_preserved=True,owned_sockets_released=True,native_starts=0)
except BaseException as error:
    result=dict(status='FAIL',events=events,error=repr(error));raise
finally:
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))

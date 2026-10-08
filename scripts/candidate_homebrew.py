"""Install an unchanged candidate formula from staged bytes; no model starts."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('action', choices=('download', 'install'))
p.add_argument('--release-id')
p.add_argument('--mode', choices=('clean', 'upgrade'))
p.add_argument('--directory', type=Path, required=True)
p.add_argument('--evidence', type=Path, required=True)
a = p.parse_args()
a.directory = a.directory.resolve(); a.evidence = a.evidence.resolve()
a.evidence.mkdir(parents=True, exist_ok=True)
binding = json.loads((a.directory / 'release-binding.json').read_text())
records = []
env = {k: v for k, v in os.environ.items() if k not in ('PYTHONPATH', 'PYTHONHOME')}
env.update(HOMEBREW_NO_AUTO_UPDATE='1', HOMEBREW_NO_INSTALL_CLEANUP='1',
           HOMEBREW_CACHE=str(a.evidence / 'brew-cache'), PYTHONDONTWRITEBYTECODE='1')
root = a.evidence / 'retained-data'
env['AI_LAB_ROOT'] = str(root)
report = a.evidence / (a.action + '.json')

def digest(path):
    with path.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()

def run(label, argv, timeout=600):
    started = time.monotonic()
    result = subprocess.run(argv, cwd=a.evidence, env=env, text=True,
                            capture_output=True, timeout=timeout)
    (a.evidence / (label + '.log')).write_text(result.stdout + result.stderr)
    row = dict(label=label, command=argv, exit=result.returncode,
               seconds=round(time.monotonic() - started, 3))
    records.append(row); report.write_text(json.dumps(records, indent=2) + '\n')
    print(json.dumps(row), flush=True)
    if result.returncode: raise RuntimeError(label + ' failed; see log')
    return result.stdout.strip()

name = 'ai_lab-' + binding['version'] + '.tar.gz'
archive = a.evidence / name
expected = binding['sdist_sha256']
formula = 'iamorlando/ai_lab/ai_lab'
if a.action == 'download':
    assert a.release_id and a.release_id.isdecimal()
    assets = json.loads(run('draft-assets', ['gh', 'api', 'repos/iamorlando/homebrew-ai_lab/releases/' + a.release_id + '/assets']))
    asset = next(x for x in assets if x['name'] == name)
    command = ['gh', 'api', '-H', 'Accept: application/octet-stream', 'repos/iamorlando/homebrew-ai_lab/releases/assets/' + str(asset['id'])]
    with archive.open('wb') as f:
        r = subprocess.run(command, env=env, stdout=f, stderr=subprocess.PIPE, timeout=120)
    assert r.returncode == 0, 'Draft asset transfer failed'
    assert digest(archive) == expected and archive.stat().st_size == asset['size']
    (a.evidence/'asset.json').write_text(json.dumps(dict(id=asset['id'], size=asset['size'], sha256=expected, transport='authenticated unpublished draft'), indent=2)+'\n')
    sys.exit(0)
assert a.mode and digest(archive) == expected
# Only a fresh, owned formula installation is permitted.
installed = subprocess.run(['brew','list','--versions','ai_lab'], env=env, capture_output=True, text=True)
assert not installed.stdout.strip(), 'Refusing to replace an existing AI Lab installation'
run('tap', ['brew', 'tap', 'iamorlando/ai_lab'])
tap = Path(run('tap-path', ['brew', '--repository', 'iamorlando/ai_lab']))
path = tap / 'Formula/ai_lab.rb'; before_formula = path.read_bytes()
try:
    if a.mode == 'upgrade':
        run('prior-tap-fetch', ['git', '-C', str(tap), 'fetch', 'origin', binding['prior_tap_sha']])
        old = run('old-formula', ['git', '-C', str(tap), 'show', binding['prior_tap_sha'] + ':Formula/ai_lab.rb'])
        path.write_text(old + '\n')
        run('old-trust', ['brew','trust','--formula',formula])
        run('install-prior', ['brew', 'install', '--build-from-source', formula], timeout=1200)
        prefix = Path(run('old-prefix', ['brew','--prefix','ai_lab']))
        old_python = str(prefix/'libexec/venv/bin/python')
        old_exe = str(prefix/'bin/ai-lab')
        assert run('literal-before', [old_exe,'--version']) == 'AI Lab 0.1.15'
        old_cache = Path(run('old-cache', ['brew','--cache','--build-from-source',formula]))
        assert digest(old_cache) == binding['prior_sdist_sha256']
        run('seed-prior', [old_python,'-I',str(a.directory/'scripts/check_release_data.py'),'seed','--root',str(root),'--record',str(a.evidence/'data-before.json')])
    path.write_bytes((a.directory/'Formula/ai_lab.rb').read_bytes())
    run('candidate-trust', ['brew','trust','--formula',formula])
    cache = Path(run('candidate-cache', ['brew','--cache','--build-from-source',formula]))
    cache.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(archive, cache)
    assert digest(cache) == expected
    upgrade_command = ['brew', 'upgrade' if a.mode == 'upgrade' else 'install', '--build-from-source', formula]
    if a.mode == 'upgrade':
        upgrade_command = [old_python, '-I', str(a.directory/'scripts/check_upgrade_web_owner.py'),
                           '--executable', old_exe, '--root', str(root), '--output', str(a.evidence/'retained-owner'),
                           '--web-checker', str(a.directory/'scripts/check_web.py'), '--', *upgrade_command]
    run('candidate-install', upgrade_command, timeout=1500)
    prefix = Path(run('candidate-prefix', ['brew','--prefix','ai_lab']))
    python = str(prefix/'libexec/venv/bin/python'); exe = str(prefix/'bin/ai-lab')
    assert run('literal-after', [exe,'--version']) == 'AI Lab ' + binding['version']
    if a.mode == 'clean':
        run('seed-clean', [python,'-I',str(a.directory/'scripts/check_release_data.py'),'seed','--root',str(root),'--record',str(a.evidence/'data-before.json')])
    run('brew-test', ['brew','test',formula])
    run('brew-linkage', ['brew','linkage','--test',formula])
    run('installed-cli', [python,str(a.directory/'scripts/check_cli.py'),exe])
    run('installed-web', [python,str(a.directory/'scripts/check_web.py'),exe,'--root',str(root)])
    run('installed-web-jev', [python,str(a.directory/'scripts/check_web.py'),exe,'--root',str(root),'--jev-configured'])
    run('installed-mcp', [python,str(a.directory/'scripts/check_mcp.py'),'--executable',exe])
    run('preserved-data', [python,'-I',str(a.directory/'scripts/check_release_data.py'),'verify','--root',str(root),'--record',str(a.evidence/'data-before.json'),'--binding',str(a.directory/'release-binding.json')])
    (a.evidence/'result.json').write_text(json.dumps(dict(status='PASS', installation=a.mode, version=binding['version'], source_sha=binding['source_sha'], tap_sha=run('tap-candidate-sha',['git','-C',str(a.directory),'rev-parse','HEAD']), python=python, executable=exe, archive_sha256=expected, native_starts=0),indent=2)+'\n')
finally:
    path.write_bytes(before_formula)

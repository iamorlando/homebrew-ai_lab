#!/usr/bin/env python3
"""Check the installed web and service command surface without downloads or model starts."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

PUBLIC = {'web', 'mcp', 'setup', 'services'}
REMOVED = ('weights', 'models', 'apis', 'chat', 'agent', 'decisions', 'completion',
           'decoder', 'skills', 'completions', 'setup-python-experiments',
           'downloads', 'server', 'complete', 'layout', '_workspace')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    executable = str(args.executable.resolve())
    checks = []
    result = {'status': 'FAIL', 'checks': checks}
    try:
        with tempfile.TemporaryDirectory(prefix='ailab-web-cli-') as directory:
            root = Path(directory).resolve() / 'data'
            env = {k: v for k, v in os.environ.items() if k != 'PYTHONPATH' and not k.startswith(('AI_LAB_', 'JEV_', 'TYPESAFE_'))}
            def run(label, argv, code=0):
                completed = subprocess.run([executable, '--root', str(root), *argv], env=env,
                    cwd=directory, capture_output=True, text=True, timeout=30)
                checks.append({'case': label, 'returncode': completed.returncode})
                assert completed.returncode == code, (label, completed.stdout, completed.stderr)
                return completed.stdout + completed.stderr
            run('version', ['--version'])
            run('help', ['--help'])
            discovery = json.loads(run('discovery', ['--json']))
            assert set(discovery['commands']) == PUBLIC
            guide = run('guide', ['--skill'])
            assert all('ai-lab ' + name in guide for name in PUBLIC)
            for shell in ('bash', 'zsh', 'fish'):
                script = run('shell-' + shell, ['--completions', shell])
                assert all(name in script for name in PUBLIC) and 'ai-lab' in script
                path = Path(directory) / ('completion.' + shell)
                path.write_text(script)
                interpreter = shutil.which(shell)
                if interpreter:
                    syntax = subprocess.run([interpreter, '-n', str(path)], capture_output=True, text=True)
                    assert syntax.returncode == 0, (shell, syntax.stderr)
            assert 'invalid choice' in run('invalid-shell', ['--completions', 'invalid'], 2)
            for name in sorted(PUBLIC):
                run(name + '-help', [name, '--help'])
            for name in REMOVED:
                assert 'invalid choice' in run('removed-' + name, [name, '--help'], 2)
            for action in ('list', 'install', 'download', 'repair', 'repair-runtime', 'doctor'):
                run('setup-' + action + '-help', ['setup', action, '--help'])
            run('setup-list', ['setup', 'list', '--json'])
            selected = json.loads(run('setup-qwen38-list', ['setup', 'list', 'qwen38', '--json']))
            assert [row['name'] for row in selected] == ['qwen38']
            diagnosis = json.loads(run('doctor-qwen38', ['setup', 'doctor', '--model', 'qwen38', '--json']))
            assert diagnosis['name'] == 'qwen38'
            assert 'Use --action list, start, stop, restart, or interrupt.' in run('services-needs-action', ['services', '--json'], 1)
            for action in ('config', 'install', 'serve'):
                run('mcp-' + action + '-help', ['mcp', action, '--help'])
            preview = json.loads(run('mcp-preview', ['mcp', 'config', '--codex', '--config-file', str(Path(directory) / 'codex.toml'), '--json']))
            assert 'entry' in preview
            assert not (root / '.models').exists(), 'CLI inspection must not download weights'
            assert not list(root.glob('.state/*server*.json')), 'CLI inspection must not start APIs'
            result.update(status='PASS', checks_run=len(checks), model_downloads=0, native_starts=0)
    finally:
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result))


if __name__ == '__main__':
    main()

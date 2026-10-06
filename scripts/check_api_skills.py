#!/usr/bin/env python3
"""Check an installed API/skills package in a detached scratch workspace.

--canonical additionally requires final public CLI wiring and canonical guide
examples. Without it, the result is explicitly a preliminary module/installer
proof because this lane's exact base retains the CLI builder's older guide.
No model, provider, SDK, network, download or real user configuration is used.
"""
import argparse
import asyncio
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from unittest.mock import patch


PUBLIC = {'weights', 'models', 'apis', 'chat', 'decisions', 'completion',
          'services', 'decoder', 'skills', 'mcp', 'completions', 'web', 'setup-python-experiments'}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def worker(canonical):
    import ai_lab
    from ai_lab import api_manager, cli, skills
    from textual.widgets import Button, Static

    package = Path(ai_lab.__file__).resolve()
    require(package.is_relative_to(Path(sys.prefix).resolve()), 'AI Lab was not imported from the selected installed environment')
    require((package.parent / '_bundle/harness/generation_models.py').is_file(), 'Packaged generation metadata is missing')
    root = Path.cwd() / 'workspace-never-created'
    home = Path(os.environ['HOME'])
    project = Path.cwd() / 'project'
    project.mkdir(mode=0o700)

    def capture(function, *args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            require(function(*args) == 0, 'Runner did not return success')
        return json.loads(output.getvalue())

    # Include first authoritative import under the tripwires.
    with patch('subprocess.Popen', side_effect=AssertionError('Unexpected process start')), \
            patch('httpx.AsyncClient', side_effect=AssertionError('Unexpected provider client')), \
            patch('urllib.request.urlopen', side_effect=AssertionError('Unexpected network request')):
        snapshot = api_manager.connections(root)
        rows = {row['name']: row for row in snapshot['connections']}
        require(set(rows) == {'deepseek', 'qwen', 'contrastive', 'clm-upstream', 'laya', 'jev'}, 'Connection inventory changed')
        require(not rows['jev']['configured'], 'Unset fixture key unexpectedly configured Jev')
        require(not root.exists(), 'API inventory created workspace state')
        os.environ['JEV_API_KEY'] = 'fixture-key-never-export'
        os.environ['AI_LAB_LAYA_API_KEY'] = 'fixture-local-key-never-export'
        os.environ['AI_LAB_LAYA_URL'] = 'http://user:fixture-url-secret@localhost:12345?key=fixture-query-secret'
        snapshot = api_manager.connections(root)
        text = json.dumps(snapshot) + api_manager.describe(snapshot)
        require(snapshot['connections'][-1]['configured'], 'Jev alias key was not recognized')
        laya = next(row for row in snapshot['connections'] if row['name'] == 'laya')
        require(laya['endpoint'] is None and not laya['endpoint_valid'], 'Invalid URL override was not withheld')
        require(not any(secret in text for secret in ['fixture-key-never-export', 'fixture-local-key-never-export',
                'fixture-url-secret', 'fixture-query-secret']), 'API export exposed fixture credentials')

        async def mounted():
            app = api_manager.api_app(root)
            async with app.run_test(size=(52, 18)) as pilot:
                require({button.id for button in app.query(Button)} == {'refresh', 'exit'}, 'Screen has unexpected actions')
                await pilot.press('r')
                require('fixture-key-never-export' not in str(app.query_one('#connections', Static).render()),
                        'Mounted screen exposed a key')
                await pilot.press('escape')
            require(app.return_value == 0 and app._exception is None, 'Mounted screen failed')
        asyncio.run(mounted())

        document, guide_sha = skills.skill_document()
        require(guide_sha == hashlib.sha256(cli.SKILL.encode()).hexdigest(), 'Guide provenance does not match shipped SKILL')
        metadata, body = document.decode().split('---\n', 2)[1:]
        require('name: ai-lab\n' in metadata and 'description:' in metadata, 'Skill metadata missing')
        require(body.lstrip() == cli.SKILL.strip() + '\n', 'Installed guide diverged from central SKILL')
        installed = []
        for agent, directory in [('codex', '.agents'), ('claude', '.claude')]:
            for scope, base in [('project', project), ('user', home)]:
                result = skills.install_skill(agent, scope, project=project if scope == 'project' else None)
                path = base / directory / 'skills/ai-lab/SKILL.md'
                require(result['path'] == str(path), 'Installer reported incorrect exact path')
                require(path.read_bytes() == document and path.stat().st_mode & 0o777 == 0o600, 'Installed skill bytes/mode differ')
                require(skills.install_skill(agent, scope, project=project if scope == 'project' else None)['status'] == 'unchanged',
                        'Identical installer is not idempotent')
                installed.append({'agent': agent, 'scope': scope, 'status': result['status']})
        custom = Path.cwd() / 'custom'
        result = skills.install_skill('codex', 'project', path=custom)
        target = Path(result['path'])
        sibling = custom / 'owner-reference.md'
        sibling.write_text('owner reference')
        target.write_text('owner skill')
        try:
            skills.install_skill('codex', 'project', path=custom)
        except ValueError:
            pass
        else:
            raise RuntimeError('Differing skill was replaced without force')
        require(target.read_text() == 'owner skill', 'Conflict changed owner bytes')
        require(skills.install_skill('codex', 'project', path=custom, force=True)['status'] == 'replaced', 'Force failed')
        require(sibling.read_text() == 'owner reference', 'Force changed sibling bytes')
        outside = Path.cwd() / 'outside.md'
        outside.write_text('owner outside')
        target.unlink()
        target.symlink_to(outside)
        try:
            skills.install_skill('codex', 'project', path=custom, force=True)
        except ValueError:
            pass
        else:
            raise RuntimeError('Installer followed symlink with force')
        require(outside.read_text() == 'owner outside', 'Symlink boundary changed owner bytes')

        # Preliminary source does not pretend the central CLI has been integrated.
        module_parser = argparse.ArgumentParser()
        module_parser.add_argument('--json', action='store_true')
        subs = module_parser.add_subparsers(dest='command')
        api_manager.add_parser(subs)
        skills.add_parser(subs)
        capture(api_manager.run, module_parser.parse_args(['--json', 'apis']), root)
        canonical_examples = 0
        if canonical:
            discovery = capture(cli.main, ['--json'])
            require(set(discovery['commands']) == PUBLIC, 'Public CLI surfaces do not match the exact thirteen contract')
            commands = set(re.findall(r'\bai-lab\s+([a-z][\w-]*)', cli.SKILL))
            require(commands == PUBLIC, 'Central guide contains stale commands or omits a canonical surface')
            for flag in ['--self-mcp', '--allow-tool', '--tool-choice', '--session-action', '--revision', '--view', '--layout', '--pane']:
                require(flag in cli.SKILL, 'Central guide is missing an advanced contract flag')
            parser = cli.parser()
            examples = [
                ['chat', '--name', 'Exact saved name', '--self-mcp'],
                ['chat', '--pane', 'PANE', '--prompt', 'Continue', '--wait', '--json'],
                ['completion', '--session-action', 'create', '--name', 'Exact saved name', '--scheme', 'synthid', '--json'],
                ['completion', '--session', 'SESSION', '--prompt', 'the quick brown', '--no-wait', '--json'],
                ['completion', '--session-action', 'get', '--session', 'SESSION', '--json'],
                ['completion', '--view', 'tournament', '--session', 'SESSION'],
                ['completion', '--layout', 'herdr', '--session', 'SESSION', '--launch'],
                ['completion', '--session-action', 'select', '--session', 'SESSION', '--step', '0', '--token-id', '17', '--revision', '1', '--json'],
                ['completion', '--session-action', 'append', '--session', 'SESSION', '--revision', '1', '--json']]
            for example in examples:
                parser.parse_args(example)
            canonical_examples = len(examples)
            capture(cli.main, ['--root', str(root), 'apis', '--json'])
            public = capture(cli.main, ['--root', str(root), 'skills', 'install', '--agent', 'codex',
                                      '--scope', 'project', '--path', str(Path.cwd() / 'public-skill'), '--json'])
            require(public['guide_sha256'] == guide_sha, 'Public installer guide provenance differs')
        require(not root.exists(), 'Module/public dispatch created runtime workspace state')
        require(not (home / '.codex/config.toml').exists() and not (home / '.claude.json').exists(), 'Installer wrote client configuration')
    return {'status': 'PASS', 'proof_scope': 'canonical-public-cli' if canonical else 'preliminary-installed-modules',
            'final_integrated_cli_gate': canonical, 'package': str(package), 'python': sys.version.split()[0],
            'connections': sorted(rows), 'reachability': 'not_checked', 'provider_requests': 0, 'model_starts': 0,
            'skill_installs': installed, 'guide_source': 'ai_lab.cli.SKILL', 'guide_sha256': guide_sha,
            'canonical_examples_parsed': canonical_examples, 'mounted_terminal_size': [52, 18],
            'checks': ['env-unset/set', 'URL/auth-redaction', 'mounted-refresh/exit', 'scratch-targets/scopes',
                       'metadata/provenance', 'idempotence', 'conflict/force', 'symlink-boundary', 'no-config/runtime-writes']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python', help='Python in the detached installed AI Lab environment')
    parser.add_argument('--canonical', action='store_true', help='Require final integrated canonical CLI and guide')
    parser.add_argument('--output', type=Path, help='Save the JSON proof')
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(args.canonical), indent=2))
        return 0
    if not args.python:
        parser.error('--python is required')
    with tempfile.TemporaryDirectory(prefix='ai-lab-api-skills-', dir='/private/tmp' if Path('/private/tmp').is_dir() else None) as folder:
        scratch = Path(folder).resolve()
        home = scratch / 'home'
        home.mkdir(mode=0o700)
        env = {key: value for key, value in os.environ.items()
               if not key.endswith(('_KEY', '_TOKEN', '_PASSWORD', '_SECRET'))
               and key not in {'PYTHONPATH', 'PYTHONHOME', 'DEEPSEEK_ROOT'}
               and not key.startswith('AI_LAB_')}
        env.update(HOME=str(home), AI_LAB_HOME=str(scratch / 'unused-data'), DEEPSEEK_ROOT=str(scratch / 'unused-backend'),
                   PYTHONDONTWRITEBYTECODE='1')
        command = [str(Path(args.python).absolute()), '-I', '-B', str(Path(__file__).resolve()), '--worker']
        if args.canonical:
            command.append('--canonical')
        result = subprocess.run(command, cwd=scratch, env=env, capture_output=True, text=True, timeout=45)
        if result.returncode:
            print(result.stderr.strip(), file=sys.stderr)
            return result.returncode
        proof = json.loads(result.stdout)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(proof, indent=2) + '\n')
    print(json.dumps(proof, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

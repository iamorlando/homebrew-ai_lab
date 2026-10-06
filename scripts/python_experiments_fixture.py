"""Real checkout/file boundaries with fake dependency tools; no provider calls."""
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from ai_lab import experiments_setup
from ai_lab.cli import PUBLIC_COMMANDS, discovery, main, parser, shell_completion
from ai_lab.client import Client, LabError

PROJECT = '''[project]
name = "d"
requires-python = ">=3.14"
[tool.poetry]
package-mode = false
[tool.poetry.dependencies]
ipykernel = "^7.4.0"
typesafe-sdk = "^0.7.2"
[build-system]
requires = ["poetry-core>=2,<3"]
build-backend = "poetry.core.masonry.api"
'''


class Fixture:
    def __init__(self, directory):
        self.root = Path(directory).resolve()
        self.source = self.root / 'upstream'
        self.location = self.root / 'chosen checkout'
        self.workspace = self.root / 'cli workspace'
        self.git = shutil.which('git')
        self.calls = []
        self.failure = None
        self.prefix = None
        self.poetry_path = None
        self.poetry = True
        self.real_run = subprocess.run
        self.source.mkdir()
        (self.source / 'pyproject.toml').write_text(PROJECT)
        (self.source / 'notebook.ipynb').write_text('user notebook bytes\n')
        self.git_call('init', str(self.source))
        self.git_call('-C', str(self.source), 'add', '.')
        self.git_call('-C', str(self.source), '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                      'commit', '-m', 'fixture')

    def git_call(self, *args):
        return self.real_run([self.git, *args], capture_output=True, text=True, check=True)

    def which(self, name, **kwargs):
        return self.git if name == 'git' else '/fixture/uv' if name == 'uv' else '/fixture/poetry' if name == 'poetry' and self.poetry else None

    def run(self, command, **kwargs):
        self.calls.append((command[:], kwargs))
        if self.failure and self.failure(command):
            return subprocess.CompletedProcess(command, 9, 'fixture-private-provider-key',
                'https://credential:fixture-private-provider-key@example.invalid/private')
        if command[0] == self.git:
            if command[1] == 'clone':
                result = self.real_run([self.git, 'clone', '--', str(self.source), command[-1]], **kwargs)
                if result.returncode == 0:
                    self.git_call('-C', command[-1], 'remote', 'set-url', 'origin', experiments_setup.REPOSITORY)
                return result
            return self.real_run(command, **kwargs)
        venv = self.location / '.venv'
        if 'venv' in command and command[0] == '/fixture/uv':
            venv.mkdir()
            (venv / 'bin').mkdir()
            (venv / 'bin/python').write_text('fake interpreter; no SDK execution\n')
            (venv / 'pyvenv.cfg').write_text('include-system-site-packages = false\n')
        if command[0] == str(venv / 'bin/python'):
            return subprocess.CompletedProcess(command, 0, json.dumps([self.prefix or str(venv), '/fixture/base-python']), '')
        if command[-3:] == ['env', 'info', '--path']:
            return subprocess.CompletedProcess(command, 0, str(self.poetry_path or venv) + '\n', '')
        return subprocess.CompletedProcess(command, 0, '', '')

    @contextlib.contextmanager
    def tools(self, **env):
        with patch.dict(os.environ, env, clear=True), \
                patch('ai_lab.experiments_setup.shutil.which', side_effect=self.which), \
                patch('ai_lab.experiments_setup.subprocess.run', side_effect=self.run):
            yield

    def clone(self):
        self.git_call('clone', '--', str(self.source), str(self.location))
        self.git_call('-C', str(self.location), 'remote', 'set-url', 'origin', experiments_setup.REPOSITORY)


class ExperimentsSetupTests(unittest.TestCase):
    def test_parser_discovery_guide_completion_and_early_dispatch(self):
        self.assertEqual(len(PUBLIC_COMMANDS), 13)
        command = discovery(parser())['commands']['setup-python-experiments']
        self.assertTrue(next(option for option in command['options'] if '--location' in option['flags'])['required'])
        for shell in ('bash', 'zsh', 'fish'):
            self.assertIn('setup-python-experiments', shell_completion(shell))
            self.assertIn('location', shell_completion(shell))
        with patch('ai_lab.experiments_setup.run', return_value=0) as run, \
                patch.object(Client, 'connect', side_effect=AssertionError('no daemon')), \
                patch('ai_lab.setup.setup', side_effect=AssertionError('no native setup')):
            self.assertEqual(main(['--json', 'setup-python-experiments', '--location', 'exact folder']), 0)
            self.assertEqual(run.call_args.args[0].location, 'exact folder')
            self.assertTrue(run.call_args.args[0].json)
        for argv in (['--json', 'setup-python-experiments'], ['--json', 'setup-python-experiments', '--loc', 'folder']):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                main(argv)
            self.assertEqual(error.exception.code, 2)

    def test_clone_poetry_only_dependencies_private_keys_and_no_foreign_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(directory)
            foreign = Path(directory) / 'foreign environment'
            foreign.mkdir()
            sentinel = foreign / 'sentinel'
            sentinel.write_text('preserve foreign\n')
            keydir = fixture.workspace / '.state/ai-lab'
            keydir.mkdir(parents=True)
            (keydir / 'jev-api-key').write_text('fixture-private-provider-key\n')
            with fixture.tools(PATH=f'{foreign}/bin:/fixture/bin', VIRTUAL_ENV=str(foreign),
                    POETRY_VIRTUALENVS_IN_PROJECT='false', POETRY_VIRTUALENVS_CREATE='false',
                    POETRY_VIRTUALENVS_OPTIONS_SYSTEM_SITE_PACKAGES='true', UV_PROJECT_ENVIRONMENT=str(foreign),
                    PYTHONHOME=str(foreign), PYTHONPATH=str(foreign), PIP_TARGET=str(foreign),
                    CLM_API_KEY='fixture-private-clm-key', TYPESAFE_API_KEY='lower-priority-key'):
                with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
                    self.assertEqual(main(['--root', str(fixture.workspace), 'setup-python-experiments',
                                          '--location', str(fixture.location), '--json']), 0, err.getvalue())
                result = json.loads(out.getvalue())
                self.assertEqual(result['checkout'], 'cloned')
                self.assertEqual(result['manager'], 'poetry')
                self.assertEqual(result['requires_python'], '>=3.14')
                self.assertEqual(result['notebooks'], 'not_started')
                self.assertTrue(all(key['present'] and key['added'] for key in result['environment_keys']))
                self.assertNotIn('fixture-private', out.getvalue() + err.getvalue())
                for command, options in fixture.calls:
                    child = options['env']
                    self.assertNotIn(str(foreign) + '/bin', child['PATH'])
                    for name in ('UV_PROJECT_ENVIRONMENT', 'PIP_TARGET', 'PYTHONHOME', 'PYTHONPATH', *experiments_setup.KEY_NAMES):
                        self.assertNotIn(name, child)
                    if 'VIRTUAL_ENV' in child:
                        self.assertEqual(child['VIRTUAL_ENV'], str(fixture.location / '.venv'))
                    self.assertEqual(child['POETRY_VIRTUALENVS_IN_PROJECT'], 'true')
                    self.assertEqual(child['POETRY_VIRTUALENVS_CREATE'], 'true')
                    self.assertEqual(child['POETRY_VIRTUALENVS_OPTIONS_SYSTEM_SITE_PACKAGES'], 'false')
                commands = [command for command, _ in fixture.calls]
                self.assertIn([fixture.git, 'clone', '--', experiments_setup.REPOSITORY, str(fixture.location)], commands)
                self.assertIn(['/fixture/uv', '--no-config', 'venv', '--python', '>=3.14', str(fixture.location / '.venv')], commands)
                self.assertIn(['/fixture/poetry', 'install', '--no-root', '--no-interaction'], commands)
                self.assertFalse(any('sync' in command or 'jupyter' in command for command in commands))
            env = fixture.location / '.env'
            self.assertEqual(stat.S_IMODE(env.stat().st_mode), 0o600)
            self.assertIn('TYPESAFE_API_KEY="fixture-private-provider-key"', env.read_text())
            self.assertIn('CLM_API_KEY="fixture-private-clm-key"', env.read_text())
            self.assertEqual((fixture.location / 'pyproject.toml').read_text(), PROJECT)
            self.assertEqual(sentinel.read_text(), 'preserve foreign\n')
            self.assertEqual(fixture.git_call('-C', str(fixture.location), 'status', '--porcelain').stdout, '')

    def test_reuse_preserves_notebook_env_comments_empty_values_and_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(directory)
            fixture.clone()
            fixture.git_call('-C', str(fixture.location), 'remote', 'set-url', 'origin',
                             'git@github.com-iamorlando:iamorlando/ai_experiments.git')
            notebook = fixture.location / 'notebook.ipynb'
            notebook.write_text('edited notebook bytes\n')
            env = fixture.location / '.env'
            env.write_bytes(b'# user comment\r\nexport TYPESAFE_API_KEY=\r\nOTHER="keep me"')
            env.chmod(0o644)
            with fixture.tools(PATH='/fixture/bin', JEV_API_KEY='do-not-replace-empty',
                               CLM_API_KEY='a"b\\c\nsecret'):
                first = experiments_setup.setup(fixture.workspace, str(fixture.location))
                old = env.read_bytes()
                second = experiments_setup.setup(fixture.workspace, str(fixture.location))
            self.assertEqual(env.read_bytes(), old)
            self.assertTrue(old.startswith(b'# user comment\r\nexport TYPESAFE_API_KEY=\r\nOTHER="keep me"\n'))
            self.assertNotIn(b'do-not-replace-empty', old)
            self.assertEqual(stat.S_IMODE(env.stat().st_mode), 0o600)
            self.assertEqual(notebook.read_text(), 'edited notebook bytes\n')
            self.assertEqual((first['checkout'], second['checkout']), ('reused', 'reused'))
            self.assertEqual(first['environment_keys'][0]['added'], False)
            self.assertTrue(first['environment_keys'][1]['added'])
            self.assertFalse(any(key['added'] for key in second['environment_keys']))
            self.assertFalse(any(any(operation in command for operation in ('clone', 'pull', 'fetch', 'reset')) for command, _ in fixture.calls))

    def test_clone_and_install_failures_have_clean_secret_safe_json_and_no_key_write(self):
        for step in ('clone', 'install'):
            with self.subTest(step=step), tempfile.TemporaryDirectory() as directory:
                fixture = Fixture(directory)
                fixture.failure = lambda command: step in command
                with fixture.tools(PATH='/fixture/bin', TYPESAFE_API_KEY='fixture-private-provider-key'), \
                        contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
                    self.assertEqual(main(['setup-python-experiments', '--location', str(fixture.location), '--json']), 1)
                self.assertEqual(out.getvalue(), '')
                error = json.loads(err.getvalue())['error']
                self.assertEqual(error['code'], 'experiments_setup')
                self.assertIn('exit 9', error['message'])
                self.assertNotIn('fixture-private', err.getvalue())
                self.assertFalse((fixture.location / '.env').exists())

    def test_unrelated_directory_and_wrong_origin_do_no_setup(self):
        for kind in ('unrelated', 'wrong-origin', 'location-link'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                fixture = Fixture(directory)
                if kind == 'unrelated':
                    fixture.location.mkdir()
                    (fixture.location / 'sentinel').write_text('private owner bytes')
                elif kind == 'wrong-origin':
                    fixture.clone()
                    fixture.git_call('-C', str(fixture.location), 'remote', 'set-url', 'origin', 'https://github.com/other/ai_experiments.git')
                else:
                    fixture.location.symlink_to(fixture.source, target_is_directory=True)
                with fixture.tools(PATH='/fixture/bin'), self.assertRaises(LabError) as error:
                    experiments_setup.setup(fixture.workspace, str(fixture.location))
                self.assertEqual(error.exception.code, 'unsafe_location')
                self.assertTrue(all(command[0] == fixture.git for command, _ in fixture.calls))
                self.assertFalse((fixture.location / '.env').exists())

    def test_managed_write_links_and_hardlinks_leave_external_files_unchanged(self):
        for target, kind in (('.env', 'symlink'), ('.env', 'hardlink'), ('.venv', 'symlink'),
                             ('pyproject.toml', 'symlink'), ('poetry.lock', 'hardlink'), ('.git/info/exclude', 'symlink')):
            with self.subTest(target=target, kind=kind), tempfile.TemporaryDirectory() as directory:
                fixture = Fixture(directory)
                fixture.clone()
                outside = Path(directory) / 'foreign'
                if target == '.venv':
                    outside.mkdir()
                    (outside / 'sentinel').write_text('owner bytes')
                else:
                    outside.write_text('owner bytes')
                path = fixture.location / target
                path.unlink(missing_ok=True)
                if kind == 'hardlink':
                    os.link(outside, path)
                else:
                    path.symlink_to(outside, target_is_directory=target == '.venv')
                with fixture.tools(PATH='/fixture/bin', TYPESAFE_API_KEY='fixture-private-provider-key'), self.assertRaises(LabError):
                    experiments_setup.setup(fixture.workspace, str(fixture.location))
                self.assertEqual((outside / 'sentinel').read_text() if outside.is_dir() else outside.read_text(), 'owner bytes')
                self.assertFalse(any('install' in command for command, _ in fixture.calls))

    def test_poetry_unavailable_uses_isolated_uv_and_resets_tool_virtualenv(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(directory)
            fixture.poetry = False
            with fixture.tools(PATH='/fixture/bin'):
                result = experiments_setup.setup(fixture.workspace, str(fixture.location))
            self.assertEqual(result['poetry_tool'], 'isolated_uv_tool')
            installs = [command for command, _ in fixture.calls if 'install' in command]
            self.assertEqual(len(installs), 1)
            command = installs[0]
            self.assertEqual(command[:9], ['/fixture/uv', '--no-config', 'tool', 'run', '--isolated', '--no-env-file', '--from', 'poetry', 'python'])
            self.assertIn("os.environ['VIRTUAL_ENV']=sys.argv.pop(1)", command[10])
            self.assertEqual(command[11], str(fixture.location / '.venv'))
            self.assertEqual(command[-3:], ['install', '--no-root', '--no-interaction'])

    def test_foreign_prefix_or_poetry_environment_is_refused_before_install(self):
        for selector in ('prefix', 'poetry_path'):
            with self.subTest(selector=selector), tempfile.TemporaryDirectory() as directory:
                fixture = Fixture(directory)
                setattr(fixture, selector, str(Path(directory) / 'foreign'))
                with fixture.tools(PATH='/fixture/bin'), self.assertRaises(LabError) as error:
                    experiments_setup.setup(fixture.workspace, str(fixture.location))
                self.assertEqual(error.exception.code, 'unsafe_location')
                self.assertFalse(any('install' in command for command, _ in fixture.calls))
                self.assertFalse((fixture.location / '.env').exists())

    def test_read_only_private_env_is_preserved_and_missing_additions_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Fixture(directory)
            fixture.clone()
            path = fixture.location / '.env'
            content = '# user choice\nTYPESAFE_API_KEY=\nCLM_API_KEY=\n'
            path.write_text(content)
            path.chmod(0o400)
            with fixture.tools(PATH='/fixture/bin', TYPESAFE_API_KEY='fixture-private-provider-key'):
                result = experiments_setup.setup(fixture.workspace, str(fixture.location))
            self.assertFalse(any(key['added'] for key in result['environment_keys']))
            self.assertEqual(path.read_text(), content)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o400)
            path.chmod(0o600)
            path.write_text('# private readonly\n')
            path.chmod(0o400)
            with fixture.tools(PATH='/fixture/bin', TYPESAFE_API_KEY='fixture-private-provider-key'), self.assertRaises(LabError):
                experiments_setup.setup(fixture.workspace, str(fixture.location))
            self.assertEqual(path.read_text(), '# private readonly\n')
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o400)

    def test_bash_location_completion_preserves_directory_spaces_and_stays_offline(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            chosen = root / 'chosen checkout'
            chosen.mkdir()
            script = root / 'completion.bash'
            script.write_text(shell_completion('bash'))
            import shlex
            command = f'''ai-lab() {{ return 99; }}
source {shlex.quote(str(script))}
COMP_WORDS=(ai-lab setup-python-experiments --location {shlex.quote(str(root / 'chosen'))}); COMP_CWORD=3
_ai_lab
printf '<%s>\\n' "${{COMPREPLY[@]}}"
'''
            result = subprocess.run(['bash', '-c', command], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), f'<{chosen}>')

    def test_tracked_private_files_and_git_negation_refused_before_dependencies(self):
        for kind in ('tracked', 'negated'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                fixture = Fixture(directory)
                fixture.clone()
                if kind == 'tracked':
                    (fixture.location / '.env').write_text('USER=kept\n')
                    fixture.git_call('-C', str(fixture.location), 'add', '.env')
                else:
                    (fixture.location / '.gitignore').write_text('!.env\n')
                with fixture.tools(PATH='/fixture/bin'), self.assertRaises(LabError) as error:
                    experiments_setup.setup(fixture.workspace, str(fixture.location))
                self.assertEqual(error.exception.code, 'unsafe_location')
                self.assertFalse(any('venv' in command for command, _ in fixture.calls))


if __name__ == '__main__':
    unittest.main()

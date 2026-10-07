#!/usr/bin/env python3
"""Public CLI subprocess/PTY + real owned CPU session API checks.

This bounded checker is NOT the full docs/tests.md release gate. It never invokes
model generation, native services, downloads, hosted SDKs or notebook cells.
Use --mode discovery for a read-only surface check before dependencies land.
Every app operation executes the supplied console entrypoint, never cli.main().
"""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import pty
import re
import select
import shutil
import signal
import struct
import subprocess
import tempfile
import termios
import time

# Resolve the sibling helper by file, also when imported by a detached harness.
_spec = importlib.util.spec_from_file_location('upgrade_checker_support', Path(__file__).with_name('check_upgrade.py'))
owned = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(owned)

PUBLIC = ('weights', 'models', 'apis', 'chat', 'decisions', 'completion',
          'services', 'decoder', 'skills', 'mcp', 'completions', 'web',
          'setup-python-experiments')
ACTIONS = {'weights': {'list', 'install', 'offer'},
           'models': {'list', 'create', 'update', 'delete'},
           'skills': {'install'}, 'mcp': {'install', 'config', 'serve'}}
CHOICES = {
    ('completion', '--view'): {'all', 'chat', 'tournament', 'probabilities', 'tokens'},
    ('completion', '--layout'): {'tmux', 'herdr'},
    ('completion', '--session-action'): {'create', 'list', 'get', 'wait', 'stop', 'append', 'select'},
    ('completion', '--service-action'): {'status', 'start', 'stop', 'run'},
    ('services', '--action'): {'list', 'start', 'stop', 'restart', 'interrupt'},
    ('services', '--model'): {'deepseek', 'qwen', 'contrastive', 'laya', 'jev'},
    ('chat', '--tool-choice'): {'auto', 'required'},
    ('decisions', '--mode'): {'ask', 'rank'},
    ('completions', 'shell'): {'bash', 'zsh', 'fish'},
    ('skills install', '--agent'): {'codex', 'claude'},
    ('skills install', '--scope'): {'user', 'project'},
    ('weights install', 'models'): {'deepseek', 'qwen', 'clm', 'laya'},
    ('models create', '--underlying-model'): {'deepseek', 'qwen', 'DeepSeekR1', 'Qwen3-8B'},
    ('models update', '--underlying-model'): {'deepseek', 'qwen', 'DeepSeekR1', 'Qwen3-8B'},
    ('mcp config', '--scope'): {'user', 'project'},
    ('mcp install', '--scope'): {'user', 'project'},
}
COMMON_SELECTION = '--model --name --scheme --watermark-file --temperature --session-name'
MCP_FLAGS = '--codex --claude --claude-desktop --cursor --opencode --scope --config-file --package --force'
FLAGS = {
    '': '--root --version --skill',
    'weights': '--doctor --setup --yes --use-local-source --build-from-source --with-models --no-models',
    'weights list': '', 'weights install': 'models --yes', 'weights offer': '--yes',
    'models': '', 'models list': '',
    'models create': '--name --underlying-model --seed --watermark-file',
    'models update': 'key --underlying-model --scheme --watermark-file',
    'models delete': 'key --name',
    'apis': '',
    'chat': COMMON_SELECTION + ' --self-mcp --mcp-config --tool-choice --allow-tool --seed --max-tokens --timeout --herdr-tab --pane --session-id --prompt --prompt-file --wait',
    'decisions': '--model --mode',
    'completion': COMMON_SELECTION + ' --session --view --layout --session-action --schemes --api-schema --api-snapshot --api-call --service-action --prompt --prompt-file --body-file --max-tokens --no-wait --timeout --revision --step --token-id --layer --launch',
    'services': '--action --name --model', 'decoder': '--name',
    'skills': '', 'skills install': '--agent --scope --project --path --force',
    'mcp': '', 'mcp config': MCP_FLAGS, 'mcp install': MCP_FLAGS, 'mcp serve': '',
    'completions': 'shell',
    'web': '--with-models --no-models --port --browser --no-browser --yes --no-setup',
    'setup-python-experiments': '--location',
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


class Check:
    def __init__(self, args, scratch):
        self.args, self.scratch = args, scratch
        self.root = scratch / 'owned root'
        self.root.mkdir(mode=0o700)
        self.home = scratch / 'private-home'
        self.home.mkdir(mode=0o700)
        self.executable = str(Path(args.executable).absolute())
        # Do not inherit keys, provider endpoints, active Python env or Herdr state.
        # HOME is isolated only in the child environment; the caller is unchanged.
        self.env = {'PATH': str(Path(self.executable).parent) + os.pathsep + os.defpath,
                    'HOME': str(self.home), 'XDG_CONFIG_HOME': str(self.home / 'config'),
                    'XDG_CACHE_HOME': str(self.home / 'cache'), 'TERM': 'xterm-256color',
                    'LANG': 'en_US.UTF-8', 'PYTHONDONTWRITEBYTECODE': '1',
                    'PYTHONUNBUFFERED': '1', 'NO_COLOR': '1',
                    'AI_LAB_SERVER': 'http://127.0.0.1:0'}
        self.records, self.blocked = [], []
        self.api = None
        self.api_log = None
        self.api_identity = self.socket_identity = None
        self.api_bridge = None
        self.socket = self.root / '.state/ai-lab/api.sock'
        require(len(os.fsencode(self.socket)) < 100, 'Choose a shorter checker scratch path.')
        self.secrets = ['check-cli-' + os.urandom(16).hex() for _ in range(3)]

    def redact(self, text):
        for value in self.secrets:
            text = text.replace(value, '<redacted-sentinel>')
        return text

    def run(self, argv, *, code=0, structured=False, stdin=None, env=None, case='CLI/CPU'):
        command = [self.executable, '--root', str(self.root), *argv]
        if self.api is not None:
            self.owner()
        result = self.process(command, code=code, structured=structured, stdin=stdin,
                              env={**(env or {}), 'AI_LAB_SERVER': self.env['AI_LAB_SERVER']}, case=case)
        if self.api is not None:
            self.owner()
        return result

    def process(self, command, *, code=0, structured=False, stdin=None, env=None, case, timeout=40):
        started = time.monotonic()
        try:
            result = subprocess.run(command, input=stdin, text=True, capture_output=True,
                                    cwd=self.scratch, env={**self.env, **(env or {})}, timeout=timeout)
        except subprocess.TimeoutExpired as error:
            stdout = owned.diagnostic_text(error.stdout)
            stderr = owned.diagnostic_text(error.stderr)
            self.records.append({'case': case, 'command': [self.redact(v) for v in command],
                                 'exit': None, 'expected_exit': code, 'timed_out': True,
                                 'timeout_seconds': timeout, 'seconds': round(time.monotonic() - started, 3),
                                 'stdout': self.redact(stdout), 'stderr': self.redact(stderr),
                                 'sentinel_leaked': any(v in stdout + stderr for v in self.secrets)})
            raise RuntimeError(f'{case}: subprocess timed out; sanitized partial output retained in report.') from None
        leaked = any(value in result.stdout + result.stderr for value in self.secrets)
        record = {'case': case, 'command': [self.redact(v) for v in command], 'exit': result.returncode,
                  'expected_exit': code, 'seconds': round(time.monotonic() - started, 3),
                  'stdout': self.redact(result.stdout), 'stderr': self.redact(result.stderr),
                  'sentinel_leaked': leaked}
        self.records.append(record)
        print(f'{case}: exit {result.returncode}', flush=True)
        require(not leaked, 'Synthetic credential appeared in subprocess output (redacted in report).')
        require(result.returncode == code, f'{case}: unexpected exit {result.returncode}; see report.')
        if structured:
            return json.loads(result.stdout if code == 0 else result.stderr)
        return result.stdout

    def discovery(self):
        version = self.run(['--version'], case='CLI-01.version').strip()
        require(version == f'AI Lab {self.args.expected_version}', 'Installed version does not match requested version.')
        data = self.run(['--json'], structured=True, case='CLI-01.discovery')
        require(set(data['commands']) == set(PUBLIC), 'Public command set changed; reconcile docs/tests.md.')

        def walk(node, path=()):
            label = ' '.join(path)
            require(label in FLAGS, f'Unmapped command {label}; reconcile matrix.')
            expected = set(FLAGS[label].split()) | {'-h', '--help', '--json'}
            actual = {flag for option in node['options'] for flag in option['flags']}
            require(actual <= expected, f'Unmapped options in {label}: {sorted(actual - expected)}')
            for option in node['options']:
                for flag in option['flags']:
                    if option['choices'] is not None:
                        require((label, flag) in CHOICES, f'Unmapped choices for {label} {flag}.')
                    if (label, flag) in CHOICES:
                        require(set(option['choices'] or []) == CHOICES[label, flag],
                                f'Choices changed for {label} {flag}; reconcile matrix.')
            require(set(node['commands']) == ACTIONS.get(label, set()) if path else True,
                    f'Public actions changed in {label}; reconcile matrix.')
            self.run([*path, '--help'], case='CLI-01.help.' + (label or 'root'))
            for name, child in node['commands'].items():
                walk(child, (*path, name))
        walk(data)
        require(self.run([], case='CLI-01.bare'), 'Empty root help.')
        require('ai-lab' in self.run(['--skill'], case='CLI-01.skill'), 'Empty skill guide.')
        self.run(['completion', '--api-schema'], structured=True, case='CPL-08.schema')
        self.run(['completion', '--schemes', '--json'], structured=True, case='CPL-08.schemes')
        for argv in (['not-a-command'], ['models', 'not-an-action'],
                     ['completions', 'not-a-shell'], ['models', 'create'],
                     ['completion', '--name', 'x', '--model', 'x']):
            error = self.run(['--json', *argv], code=2, structured=True, case='CLI-02.usage')
            require(error.get('ok') is False and error['error']['code'] == 'usage', 'Bad usage error shape.')
        for argv in (['completion'], ['models'], ['chat'], ['decoder'], ['decisions']):
            error = self.run(['--json', *argv], code=1, structured=True, case='CLI-02.non-tty')
            require(error.get('ok') is False, 'Interactive-only command did not produce structured error.')
        info = self.run(['apis', '--json'], structured=True, case='API-01.redaction', env={
            'JEV_API_KEY': self.secrets[0], 'AI_LAB_LAYA_API_KEY': self.secrets[1],
            'AI_LAB_LAYA_URL': 'http://user:' + self.secrets[2] + '@localhost:12345'})
        require(info.get('informational') is True, 'APIs did not remain informational.')
        require(not any(self.root.rglob('*')), 'Read-only discovery mutated its empty root.')
        self.shells()
        return data

    def shells(self):
        for shell in ('bash', 'zsh', 'fish'):
            script = self.run(['completions', shell], case='SH-01.generate.' + shell)
            require(all(name in script for name in PUBLIC), 'Shell script lost public command.')
            path = self.scratch / ('completion.' + shell)
            path.write_text(script)
            binary = shutil.which(shell)
            if not binary:
                self.blocked.append({'case': 'SH-01.syntax.' + shell, 'reason': 'Shell executable unavailable'})
                continue
            self.process([binary, '-n', str(path)], case='SH-01.syntax.' + shell)
            # Real shell source, with completions initialization where required.
            source = {'bash': 'source "$1"; complete -p ai-lab',
                      'zsh': 'autoload -Uz compinit; compinit -D; source "$1"; print -r -- ${_comps[ai-lab]}',
                      'fish': 'source $argv[1]; complete -C "ai-lab "'}[shell]
            result = self.process([binary, '-c', source, *([] if shell == 'fish' else ['check-cli']), str(path)],
                                  case='SH-01.source.' + shell)
            require(bool(result.strip()), 'Shell completion did not register.')
        require(not any(self.root.rglob('*')), 'Shell discovery started or mutated workspace.')

    def owner(self):
        require(self.api is not None and self.api.poll() is None, 'Owned API exited; replacement startup is forbidden.')
        require(self.api_identity is not None and owned.process_identity(self.api.pid) == self.api_identity,
                'Owned API process identity changed.')
        require(owned.socket_record(self.socket) == self.socket_identity, 'Owned API socket changed.')

    def start_api(self):
        require(self.api is None, 'Owned API already running.')
        fd, log_path = tempfile.mkstemp(prefix='owned-api-', suffix='.log', dir=self.scratch)
        self.api_log = os.fdopen(fd, 'w+')
        self.api_log_path = log_path
        command = [self.executable, '--root', str(self.root), 'completion', '--service-action', 'run']
        self.api = subprocess.Popen(command, cwd=self.scratch, env=self.env,
                                    stdin=subprocess.DEVNULL, stdout=self.api_log,
                                    stderr=subprocess.STDOUT, start_new_session=True)
        direct_env = {k: v for k, v in self.env.items() if k != 'AI_LAB_SERVER'}
        deadline = time.monotonic() + 30
        ready = False
        while time.monotonic() < deadline and self.api.poll() is None:
            probe_command = [self.executable, '--root', str(self.root), 'completion',
                             '--service-action', 'status', '--json']
            probe_started = time.monotonic()
            try:
                probe = subprocess.run(probe_command, cwd=self.scratch, env=direct_env,
                                       capture_output=True, text=True, timeout=5)
            except subprocess.TimeoutExpired as error:
                self.records.append({'case': 'CPL-09.readiness-probe', 'command': probe_command,
                                     'owned_pid': self.api.pid, 'exit': None, 'timed_out': True,
                                     'timeout_seconds': 5, 'seconds': round(time.monotonic() - probe_started, 3),
                                     'stdout': self.redact(owned.diagnostic_text(error.stdout)),
                                     'stderr': self.redact(owned.diagnostic_text(error.stderr))})
                raise RuntimeError('Owned API readiness probe timed out; sanitized diagnostic retained.') from None
            if probe.returncode == 0:
                ready = True
                break
            time.sleep(.1)
        self.records.append({'case': 'CPL-09.foreground-run', 'command': command,
                             'owned_pid': self.api.pid, 'ready': ready})
        require(ready, 'Owned CPU session API failed to start.')
        self.api_identity = owned.process_identity(self.api.pid)
        require(self.api_identity is not None and self.api_identity['uid'] == os.getuid()
                and self.api_identity['pgid'] == self.api.pid
                and self.api_identity['command'].endswith(' '.join(command)), 'Unexpected owned API identity.')
        self.socket_identity = owned.socket_record(self.socket)
        owned.socket_owner(self.api.pid, self.socket)
        self.api_bridge = owned.forwarding_bridge(self.socket, self.owner)
        self.env['AI_LAB_SERVER'] = self.api_bridge.__enter__()
        self.owner()

    def signal_api(self, sig):
        """Re-attest the exact child before each bounded shutdown signal."""
        process = self.api
        require(process is not None and process.poll() is None, 'Owned API is no longer running.')
        identity = owned.process_identity(process.pid)
        require(identity is not None and identity['uid'] == os.getuid()
                and identity['pgid'] == process.pid
                and identity['command'].endswith(' '.join(process.args)), 'API shutdown refuses an unverified process.')
        if self.api_identity is not None:
            require(identity == self.api_identity, 'API shutdown refuses a changed process identity.')
        else:
            # Startup can fail before readiness. The unreaped Popen still owns
            # this child; attest its launch command before retaining identity.
            self.api_identity = identity
        if self.socket.exists() or self.socket.is_symlink():
            current = owned.socket_record(self.socket)
            if self.socket_identity is not None:
                require(current == self.socket_identity, 'API shutdown refuses a replaced socket.')
            owned.socket_owner(process.pid, self.socket)
            self.socket_identity = current
        process.send_signal(sig)

    def stop_api(self, *, via_cli=False):
        if self.api is None:
            return
        process = self.api
        started = time.monotonic()
        live_on_entry = process.poll() is None
        record = {'case': 'CPL-09.cleanup', 'owned_pid': process.pid,
                  'log_path': self.api_log_path, 'timeouts': [], 'signals': [],
                  'live_on_entry': live_on_entry, 'public_stop_requested': via_cli,
                  'shutdown_initiated': False}
        cleanup_complete = False
        shutdown_error = None
        try:
            if live_on_entry:
                if via_cli:
                    self.owner()
                    # Direct stop cannot auto-start: connect(start=False), then
                    # one POST. Still clean the owner if this command fails.
                    try:
                        self.process([self.executable, '--root', str(self.root), 'completion',
                                      '--service-action', 'stop', '--json'],
                                     env={'AI_LAB_SERVER': ''}, structured=True, case='CPL-09.stop')
                        record['shutdown_initiated'] = True
                    except (Exception, KeyboardInterrupt) as error:
                        shutdown_error = error
                        record['shutdown_error'] = self.redact(str(error))
                else:
                    self.signal_api(signal.SIGINT)
                    record['signals'].append('SIGINT')
                    record['shutdown_initiated'] = True
                for seconds, next_signal in ((10, signal.SIGTERM), (5, signal.SIGKILL), (5, None)):
                    try:
                        process.wait(timeout=seconds)
                        break
                    except subprocess.TimeoutExpired:
                        record['timeouts'].append({'stage': 'API exit', 'seconds': seconds})
                        require(next_signal is not None, 'Owned API did not exit after bounded SIGKILL.')
                        self.signal_api(next_signal)
                        record['signals'].append(next_signal.name)
            if self.socket.exists() or self.socket.is_symlink():
                require(self.socket_identity is not None and self.api_identity is not None,
                        'Cleanup refuses a socket without original ownership evidence.')
                owned.remove_stale_socket(self.socket, self.socket_identity, self.api_identity)
            require(not self.socket.exists() and not self.socket.is_symlink(), 'Owned API socket remains.')
            if self.api_bridge is not None:
                self.api_bridge.__exit__(None, None, None)
                self.api_bridge = None
            self.env['AI_LAB_SERVER'] = 'http://127.0.0.1:0'
            cleanup_complete = True
            if shutdown_error is not None:
                raise shutdown_error
            require(process.returncode == 0, 'Owned API did not exit cleanly (owned resources cleaned).')
            require(live_on_entry, 'Owned API exited before checker shutdown (owned resources cleaned).')
            require(record['shutdown_initiated'], 'Checker did not initiate the owned API shutdown.')
            require(not record['timeouts'], 'Owned API shutdown timed out (owned resources cleaned).')
        except (Exception, KeyboardInterrupt) as error:
            record['error'] = self.redact(str(error))
            raise
        finally:
            record.update(exit=process.poll(), process_exited=process.returncode is not None,
                          socket_removed=not self.socket.exists() and not self.socket.is_symlink(),
                          cleanup_complete=cleanup_complete, timed_out=bool(record['timeouts']),
                          seconds=round(time.monotonic() - started, 3))
            try:
                self.api_log.seek(0)
                record['log'] = self.redact(self.api_log.read())
            except Exception as error:
                record['log_error'] = type(error).__name__
            self.records.append(record)
            if cleanup_complete:
                self.api_log.close()
                self.api = self.api_log = None
                self.api_identity = self.socket_identity = None
            # An attestation/cleanup failure keeps the handle and private
            # scratch/logs available; it never clears unverified resources.

    def cpu(self):
        self.start_api()
        before = self.api.pid
        self.run(['completion', '--service-action', 'start', '--json'], structured=True, case='CPL-09.reuse')
        require(self.api.poll() is None and self.api.pid == before, 'API reuse lost owned process.')
        profiles = []
        for family in ('deepseek', 'qwen'):
            created = self.run(['models', 'create', '--name', f'CLI [{family}] with spaces',
                                '--underlying-model', family, '--seed', '0x2a', '--json'],
                               structured=True, case='MOD-02.create.' + family)
            profiles.append(created)
        listed = self.run(['models', 'list', '--json'], structured=True, case='MOD-01.list')
        require(all(any(p['key'] == q['key'] for q in listed['models']) for p in profiles), 'Created model missing.')
        first = profiles[0]
        self.run(['models', 'update', first['key'], '--underlying-model', 'qwen', '--json'],
                 structured=True, case='MOD-03.update')
        session = self.run(['completion', '--session-action', 'create', '--name', first['name'],
                            '--session-name', 'CPU persisted session', '--json'], structured=True,
                           case='CPL-04.create')
        sid = session['id']
        for action in ('list', 'get', 'wait', 'stop'):
            argv = ['completion', '--session-action', action]
            if action != 'list':
                argv += ['--session', sid]
            self.run([*argv, '--json'], structured=True, case='CPL-04.' + action)
        self.run(['completion', '--api-snapshot', '--json'], structured=True, case='CPL-08.snapshot')
        self.run(['completion', '--api-call', 'GET', '/api/lab/models', '--json'],
                 structured=True, case='CPL-08.api-get')
        self.run(['models', 'delete', first['key'], '--json'], structured=True, case='MOD-04.delete-id')
        remaining = self.run(['models', 'list', '--json'], structured=True, case='MOD-04.verify')
        require(first['key'] not in {p['key'] for p in remaining['models']}, 'Deleted profile still listed.')
        self.run(['completion', '--session-action', 'get', '--session', sid, '--json'],
                 structured=True, case='MOD-04.session-preserved')
        self.stop_api(via_cli=True)
        self.start_api()
        after = self.run(['models', 'list', '--json'], structured=True, case='PKG-07.registry-reload')
        require(after == remaining, 'Registry changed after actual process restart.')
        restored = self.run(['completion', '--session-action', 'get', '--session', sid, '--json'],
                            structured=True, case='PKG-07.session-reload')
        require(restored['id'] == sid, 'Session identity not persisted.')
        self.installers()
        if not self.args.no_terminal:
            self.terminals(profiles[1])
        self.stop_api(via_cli=True)

    def installers(self):
        for agent in ('codex', 'claude'):
            for scope in ('project', 'user'):
                dest = self.scratch / f'skill-{agent}-{scope}'
                argv = ['skills', 'install', '--agent', agent, '--scope', scope, '--path', str(dest), '--json']
                result = self.run(argv, structured=True, case=f'SKL-01.{agent}.{scope}')
                require(result['status'] == 'installed' and (dest / 'SKILL.md').is_file(), 'Skill not written.')
                require(self.run(argv, structured=True, case='SKL-01.idempotent')['status'] == 'unchanged', 'Skill changed.')
                (dest / 'SKILL.md').write_text('owned conflict\n')
                self.run(argv, code=1, structured=True, case='SKL-01.conflict')
                require((dest / 'SKILL.md').read_text() == 'owned conflict\n', 'Conflicting skill overwritten.')
                require(self.run([*argv, '--force'], structured=True, case='SKL-01.force')['status'] == 'replaced',
                        'Explicit skill replacement failed.')
        for client in ('codex', 'claude', 'claude-desktop', 'cursor', 'opencode'):
            for scope in ('project', 'user'):
                config = self.scratch / f'mcp-{client}-{scope}.config'
                original = 'unrelated = true\n' if client == 'codex' else '{"unrelated": true}\n'
                config.write_text(original)
                options = ['--' + client, '--scope', scope, '--config-file', str(config),
                           '--package', f'ai-lab=={self.args.expected_version}', '--json']
                preview = self.run(['mcp', 'config', *options], structured=True, case=f'MCP-01.config.{client}.{scope}')
                require(config.read_text() == original and preview['status'] == 'planned', 'MCP preview changed config.')
                self.run(['mcp', 'install', *options], structured=True, case=f'MCP-01.install.{client}.{scope}')
                require('unrelated' in config.read_text(), 'MCP install lost unrelated config.')
                repeat = self.run(['mcp', 'install', *options], structured=True, case='MCP-01.idempotent')
                require(repeat['status'] == 'already_configured', 'MCP reinstall changed config.')

    def terminals(self, profile):
        # Smoke only: no Run/Send/Download/Start actions. Feature owner checkers
        # provide the joined actions specified in docs/tests.md.
        cases = [(['weights'], 'WEIGHTS', b'r\x11'),
                 (['models'], 'SAVED MODELS', b'\x11'),
                 (['apis'], 'API CONNECTIONS', b'r\x11'),
                 (['chat'], 'CHOOSE', b'\x1b'),
                 (['decisions'], 'DECISIONS', b'\x11'),
                 (['decoder'], 'Decode', b'\x11'),
                 (['completion', '--name', profile['name']], 'COMPLETION', b'\x11')]
        for columns, rows in ((120, 40), (80, 24)):
            for argv, marker, keys in cases:
                self.terminal(argv, marker, keys, columns, rows)

    def terminal(self, argv, marker, keys, columns, rows):
        self.owner()
        started = time.monotonic()
        command = [self.executable, '--root', str(self.root), *argv]
        master = slave = process = None
        captured = bytearray()
        sent, seen = False, False
        primary_error = cleanup_error = None
        record = {'case': 'PTY.entrypoint-smoke', 'command': [self.redact(v) for v in command],
                  'size': [columns, rows], 'expected_marker': marker, 'keys_hex': keys.hex(),
                  'timeouts': [], 'signals': []}

        def read_available():
            # Also drain bytes buffered during shutdown, without blocking on a
            # still-live child if cleanup failed. Bound retained diagnostics.
            while master is not None and select.select([master], [], [], 0)[0]:
                try:
                    chunk = os.read(master, 65536)
                except OSError:
                    break
                if not chunk:
                    break
                remaining = 2_000_000 - len(captured)
                captured.extend(chunk[:remaining])
                if len(chunk) > remaining:
                    record['transcript_truncated'] = True
                    break

        try:
            master, slave = pty.openpty()
            fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', rows, columns, 0, 0))
            # Ctrl+Q must reach Textual rather than software flow control.
            attrs = termios.tcgetattr(slave)
            attrs[0] &= ~(termios.IXON | termios.IXOFF)
            termios.tcsetattr(slave, termios.TCSANOW, attrs)
            process = subprocess.Popen(command, cwd=self.scratch, env=self.env, stdin=slave,
                                       stdout=slave, stderr=slave, start_new_session=True)
            os.close(slave)
            slave = None
            deadline = time.monotonic() + 18
            while time.monotonic() < deadline:
                if select.select([master], [], [], .1)[0]:
                    try:
                        chunk = os.read(master, 65536)
                    except OSError:
                        break
                    if not chunk:
                        break
                    remaining = 2_000_000 - len(captured)
                    captured.extend(chunk[:remaining])
                    record['transcript_truncated'] = len(chunk) > remaining
                    require(not record['transcript_truncated'], 'Terminal emitted excessive output.')
                    if marker.casefold() in captured.decode(errors='replace').casefold() and not sent:
                        seen = True
                        time.sleep(.3)
                        os.write(master, keys)
                        sent = True
                if process.poll() is not None:
                    break
            if process.poll() is None:
                if time.monotonic() >= deadline:
                    record['timeouts'].append({'stage': 'PTY interaction', 'seconds': 18})
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    record['timeouts'].append({'stage': 'PTY exit grace', 'seconds': 2})
                    process.terminate()
                    record['signals'].append('SIGTERM')
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        record['timeouts'].append({'stage': 'PTY SIGTERM exit', 'seconds': 5})
                        raise RuntimeError(f'PTY {argv[0]} timed out after SIGTERM; see report.') from None
            self.owner()
            require(not record['timeouts'], f'PTY {argv[0]} timed out; see report.')
            require(seen and sent and process.returncode == 0, f'PTY {argv[0]} did not render/exit cleanly; see report.')
            require('Traceback (most recent call last)' not in captured.decode(errors='replace'), 'Terminal traceback.')
        except (Exception, KeyboardInterrupt) as error:
            primary_error = error
        finally:
            try:
                if process is not None and process.poll() is None:
                    # This unreaped, directly created session owns its PGID.
                    os.killpg(process.pid, signal.SIGKILL)
                    record['signals'].append('SIGKILL')
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        record['timeouts'].append({'stage': 'PTY SIGKILL exit', 'seconds': 5})
                        raise RuntimeError('Owned PTY did not exit after bounded SIGKILL.') from None
            except (Exception, KeyboardInterrupt) as error:
                cleanup_error = error
            finally:
                try:
                    read_available()
                except Exception as error:
                    record['drain_error'] = type(error).__name__
                if primary_error is None and 'Traceback (most recent call last)' in captured.decode(errors='replace'):
                    primary_error = RuntimeError('Terminal traceback.')
                record.update(marker_seen=seen, keys_sent=sent,
                              owned_pid=process.pid if process is not None else None,
                              exit=process.poll() if process is not None else None,
                              process_exited=process is not None and process.returncode is not None,
                              seconds=round(time.monotonic() - started, 3),
                              timed_out=bool(record['timeouts']), transcript=self.redact(captured.decode(errors='replace')))
                if primary_error is not None:
                    record['error'] = self.redact(str(primary_error))
                if cleanup_error is not None:
                    record['cleanup_error'] = self.redact(str(cleanup_error))
                self.records.append(record)
                if master is not None:
                    os.close(master)
                if slave is not None:
                    os.close(slave)
        if primary_error is not None:
            raise primary_error
        if cleanup_error is not None:
            raise RuntimeError('Owned PTY cleanup failed; see retained report.') from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable', required=True, help='Absolute installed ai-lab console script')
    parser.add_argument('--expected-version', default='0.1.15')
    parser.add_argument('--source-sha', required=True, help='Caller-supplied exact source SHA; artifact provenance is verified separately')
    parser.add_argument('--wheel', type=Path, help='Optional immutable artifact to hash; this checker does not install it')
    parser.add_argument('--mode', choices=('discovery', 'cpu'), default='cpu')
    parser.add_argument('--context', choices=('installed', 'source-development'), default='installed',
                        help='Evidence label; source-development never counts as installed-package proof')
    parser.add_argument('--no-terminal', action='store_true', help='Omit PTY smoke; explicitly reported as not run')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch('[0-9a-f]{40}', args.source_sha):
        parser.error('source-sha must be a full commit ID')
    scope = 'public CLI subprocess discovery'
    if args.mode == 'cpu':
        scope += ' + real owned CPU API/installers'
        if not args.no_terminal:
            scope += ' + PTY entrypoint smoke'
    report = {'status': 'NOT_RUN', 'scope': scope,
              'checker_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'source_sha_supplied': args.source_sha, 'executable': str(Path(args.executable).absolute()),
              'expected_version': args.expected_version, 'mode': args.mode, 'context': args.context,
              'native_inference': False, 'full_release_pass': False,
              'terminal_requested': args.mode == 'cpu' and not args.no_terminal,
              'not_covered': ['clean installation', 'literal upgrade', 'persistent 0.1.13 API',
                              'feature-complete terminal actions', 'native generation/decisions/detection',
                              'hosted SDK', 'real downloads/builds', 'notebook execution',
                              'real browser/Herdr launch', 'dynamic shell selection flows']}
    if args.wheel:
        report['wheel'] = str(args.wheel.absolute())
        report['wheel_sha256'] = hashlib.sha256(args.wheel.read_bytes()).hexdigest()
    # Keep failed-run diagnostics and ownership evidence. Delete only after a
    # successful cleanup and a successfully written report.
    scratch = Path(tempfile.mkdtemp(prefix='acl-', dir='/tmp')).resolve()
    check = Check(args, scratch)
    try:
        report['discovery'] = check.discovery()
        if args.mode == 'cpu':
            check.cpu()
        report['status'] = 'BLOCKED_INPUT' if check.blocked else 'PASS'
    except (Exception, KeyboardInterrupt) as error:
        report.update(status='FAIL', error=check.redact(str(error)))
    finally:
        try:
            check.stop_api()
        except (Exception, KeyboardInterrupt) as error:
            report.update(status='FAIL', cleanup_error=check.redact(str(error)))
        report['checks'], report['blocked_inputs'] = check.records, check.blocked
    report['scratch_retained'] = report['status'] == 'FAIL'
    report['scratch_path'] = str(scratch)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    owned.write_json(args.output, report)
    if not report['scratch_retained']:
        shutil.rmtree(scratch)
    print(json.dumps({k: report[k] for k in ('status', 'scope', 'context', 'mode', 'source_sha_supplied', 'native_inference', 'full_release_pass')} |
                     {'checks': len(check.records), 'blocked_inputs': check.blocked, 'report': str(args.output)}))
    return 0 if report['status'] == 'PASS' else 2 if report['status'] == 'BLOCKED_INPUT' else 1


if __name__ == '__main__':
    raise SystemExit(main())

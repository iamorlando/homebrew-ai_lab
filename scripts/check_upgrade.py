#!/usr/bin/env python3
"""Two-phase 0.1.13 -> 0.1.14 CLI/data proof retaining the actual old API.

The caller runs Homebrew between before/after. This script never installs,
upgrades, downloads, generates tokens, starts native backends or invokes SDKs.
Tiny inert sentinels prove file-preservation mechanics, not valid model weights.
Use cleanup with the original root/state after an interrupted CI run.
"""
import argparse
from contextlib import contextmanager
import copy
import errno
import fcntl
import hashlib
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import stat
import subprocess
import threading
import time
import uuid

FORMAT = 'ai-lab-owned-upgrade-v1'
MARKER = '.upgrade-checker/owner.json'
OWNER_MOMENTS = ('primary_before_cleanup', 'internal_cleanup', 'explicit_cleanup', 'late_observation')
OWNER_FIELDS = ('pid', 'uid', 'pgid', 'started', 'command')


def require(value, message):
    if not value:
        raise RuntimeError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def object_hash(value):
    return digest(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())


def absolute(value):
    path = Path(value)
    require(path.is_absolute() and '..' not in path.parts and not any(c in str(path) for c in '\r\n\0'),
            'Use an absolute path without traversal or control characters.')
    return path


def data_path(value):
    path = absolute(value)
    # System /tmp is an alias on macOS; user-controlled links are not accepted.
    if str(path).startswith('/tmp/'):
        path = Path('/tmp').resolve() / path.relative_to('/tmp')
    require(path == path.resolve(), 'Data/state paths must not traverse symlinks; use a canonical owned path.')
    return path


def regular(path, private=False):
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_uid == os.getuid(),
            'Refusing a linked, foreign or nonregular managed file.')
    if private:
        require(stat.S_IMODE(info.st_mode) == 0o600, 'State/ownership files must have mode 0600.')
    return info


def directory(path, *, private=True):
    info = path.lstat()
    mode = stat.S_IMODE(info.st_mode)
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
            and (mode == 0o700 if private else mode & 0o022 == 0),
            'Use an owned 0700 data root; state/report parents must not be writable by other users.')
    return {'dev': info.st_dev, 'ino': info.st_ino, 'uid': info.st_uid}


def file_record(path):
    require(path == path.resolve(), 'Refusing a managed file through linked parent paths.')
    info = regular(path)
    return {'sha256': digest(path.read_bytes()), 'bytes': info.st_size, 'mtime_ns': info.st_mtime_ns,
            'mode': stat.S_IMODE(info.st_mode), 'uid': info.st_uid, 'gid': info.st_gid,
            'dev': info.st_dev, 'ino': info.st_ino}


def create_file(path, data):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def write_json(path, value):
    if path.exists() or path.is_symlink():
        regular(path, private=True)
    temporary = path.with_name('.' + path.name + '.' + uuid.uuid4().hex)
    try:
        create_file(temporary, (json.dumps(value, indent=2) + '\n').encode())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def read_state(path):
    regular(path, private=True)
    require(path.stat().st_size <= 4_000_000, 'State file exceeds the checker limit.')
    return json.loads(path.read_text())


def minimal_environment(root):
    home = root / '.upgrade-checker/home'
    home.mkdir(exist_ok=True, mode=0o700)
    directory(home)
    return {'PATH': os.defpath, 'HOME': str(home), 'XDG_CONFIG_HOME': str(home / 'config'),
            'XDG_CACHE_HOME': str(home / 'cache'), 'LANG': 'C', 'LC_ALL': 'C',
            'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONUNBUFFERED': '1', 'NO_COLOR': '1'}


def process_identity(pid):
    require(type(pid) is int and pid > 1, 'Invalid owned PID.')
    result = subprocess.run(['/bin/ps', '-ww', '-p', str(pid), '-o', 'uid=', '-o', 'pgid=',
                             '-o', 'stat=', '-o', 'lstart=', '-o', 'command='],
                            capture_output=True, text=True, timeout=5,
                            env={'PATH': os.defpath, 'LC_ALL': 'C'})
    if result.returncode == 1 and not result.stdout.strip():
        return None
    require(result.returncode == 0, 'Process identity inspection failed; no process action is allowed.')
    fields = result.stdout.strip().split(None, 8)
    require(len(fields) == 9, 'Unrecognized process identity; refusing process action.')
    if fields[2].startswith('Z'):
        return None
    return {'pid': pid, 'uid': int(fields[0]), 'pgid': int(fields[1]),
            'started': ' '.join(fields[3:8]), 'command': fields[8]}


def socket_record(path):
    info = path.lstat()
    require(stat.S_ISSOCK(info.st_mode) and info.st_uid == os.getuid(), 'Refusing a foreign or non-socket API path.')
    return {'dev': info.st_dev, 'ino': info.st_ino, 'uid': info.st_uid}


def socket_owner(pid, path):
    binary = shutil.which('lsof') or '/usr/sbin/lsof'
    result = subprocess.run([binary, '-nP', '-a', '-p', str(pid), '-U', '-Fn'],
                            capture_output=True, text=True, timeout=8,
                            env={'PATH': os.defpath, 'LC_ALL': 'C'})
    require(result.returncode == 0 and any(line == 'n' + str(path) or line.startswith('n' + str(path) + ' type=')
            for line in result.stdout.splitlines()), 'Recorded process does not own the API socket; refusing action.')


def remove_stale_socket(path, identity, owner):
    """Remove only the attested socket of an exited owner, never a replacement."""
    require(process_identity(owner['pid']) is None, 'Stale cleanup refuses a live/reused PID.')
    require(socket_record(path) == identity, 'Stale cleanup refuses a replaced socket.')
    binary = shutil.which('lsof') or '/usr/sbin/lsof'
    # Select this path across all PIDs, not just the departed owner.
    probe = subprocess.run([binary, '-nP', '-a', '-U', str(path)], capture_output=True,
                           text=True, timeout=8, env={'PATH': os.defpath, 'LC_ALL': 'C'})
    require(probe.returncode == 1 and not probe.stdout.strip() and not probe.stderr.strip(),
            'Stale cleanup could not prove absence of a socket holder.')
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(1)
        try:
            client.connect(str(path))
        except OSError as error:
            require(error.errno == errno.ECONNREFUSED, 'Stale socket probe was inconclusive.')
        else:
            raise RuntimeError('Stale cleanup refuses a listening socket.')
    # Recheck both identities immediately before the only unlink operation.
    require(process_identity(owner['pid']) is None and socket_record(path) == identity,
            'Stale socket or PID changed during inspection.')
    path.unlink()


def diagnostic_text(value):
    text = value.decode(errors='replace') if isinstance(value, bytes) else (value or '')
    # Only checker-generated keys enter the minimal child environment/data root.
    for key in ('11' * 32, '22' * 32):
        text = text.replace(key, '<redacted-sentinel>')
    return text


class UnixHTTP(HTTPConnection):
    def __init__(self, path):
        super().__init__('localhost', timeout=10)
        self.path = path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(str(self.path))


def api_request(path, method, route, body=None):
    connection = UnixHTTP(path)
    try:
        connection.request(method, route, body=body, headers={'Content-Type': 'application/json'})
        response = connection.getresponse()
        data = response.read(2_000_001)
        require(len(data) <= 2_000_000, 'API response exceeded the checker limit.')
        return response.status, data
    finally:
        connection.close()


def package_record(executable):
    candidates = list((executable.parent.parent / 'lib').glob('python*/site-packages/ai_lab'))
    require(len(candidates) == 1, 'Old entrypoint must belong to a retained installed venv, not a checkout/wrapper.')
    package = candidates[0]
    require(package.resolve() == package and package.is_dir(), 'Retained ai_lab package must not be a linked checkout.')
    entries = []
    for path in sorted(package.rglob('*')):
        if '__pycache__' in path.parts or path.suffix == '.pyc' or path.is_dir():
            continue
        require(path.is_file() and not path.is_symlink(), 'Retained package contains an unsupported link.')
        entries.append([str(path.relative_to(package)), digest(path.read_bytes())])
    require(entries, 'Retained package is empty.')
    return {'path': str(package), 'sha256': object_hash(entries), 'files': len(entries)}


def interpreter_binding(executable):
    """Bind this retained venv's launcher and its concrete Framework exec target.

    This is not a prefix allowlist: every accepted complete command is derived
    from these existing files before Popen and includes the exact launch argv.
    """
    first = executable.read_bytes().splitlines()[0].decode()
    launcher = executable.parent / 'python'
    require(first == '#!' + str(launcher), 'Retained entrypoint must use its own venv/bin/python shebang.')
    resolved = launcher.resolve(strict=True)
    paths = [str(launcher), str(resolved)]
    physical = {str(resolved): file_record(resolved)}
    # CPython's macOS framework launcher execs this sibling binary. Derive
    # only from the physical launcher path, never from observed ps text.
    if (resolved.parent.name == 'bin' and resolved.parent.parent.parent.name == 'Versions'
            and resolved.parent.parent.parent.parent.name == 'Python.framework'):
        framework = resolved.parent.parent / 'Resources/Python.app/Contents/MacOS/Python'
        require(framework == framework.resolve(strict=True), 'Framework interpreter must have a physical path.')
        physical[str(framework)] = file_record(framework)
        paths.append(str(framework))
    return {'launcher': str(launcher), 'resolved_launcher': str(resolved),
            'command_interpreters': list(dict.fromkeys(paths)), 'files': physical}


def startup_identity_matches(saved, observed, argv, binding):
    if (not isinstance(observed, dict) or set(observed) != set(OWNER_FIELDS)
            or any(observed[key] != saved[key] for key in ('pid', 'uid', 'pgid', 'started'))):
        return False
    return observed['command'] in [path + ' ' + ' '.join(argv) for path in binding['command_interpreters']]


def keg(executable, version):
    parts = executable.parts
    require('Cellar' in parts, 'Homebrew context requires a stable versioned Cellar path; supplemental envs use --context isolated-env.')
    index = parts.index('Cellar')
    require(len(parts) > index + 3 and re.fullmatch(re.escape(version) + r'(?:_\d+)?', parts[index + 2]),
            'Cellar keg does not match the literal expected release.')
    return {'cellar': str(Path(*parts[:index + 1])), 'formula': parts[index + 1], 'keg': parts[index + 2]}


@contextmanager
def forwarding_bridge(path, verify, records=None):
    """Forward real CPU API requests; explicit server selection disables auto-start."""
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def dispatch(self):
            try:
                verify()
                require(self.path.startswith('/api/lab/') and not any(
                    part in self.path.split('?')[0].split('/') for part in ('complete', 'append', 'shutdown')),
                    'Generation/lifecycle route is outside this bridge scope.')
                length = int(self.headers.get('Content-Length', '0'))
                require(0 <= length <= 100_000, 'Bridge body exceeds the checker limit.')
                body = self.rfile.read(length) if length else None
                status, data = api_request(path, self.command, self.path, body)
                verify()
                if records is not None:
                    records.append({'case': 'retained-api-wire', 'method': self.command,
                                    'path': self.path, 'http_status': status,
                                    'body_sha256': digest(body or b'')})
            except Exception:
                status, data = 503, b'{"detail":"Retained API ownership or transport check failed"}'
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        do_GET = do_POST = do_PATCH = do_DELETE = dispatch

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}'
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        require(not thread.is_alive(), 'Owned forwarding bridge did not stop.')


class Upgrade:
    def __init__(self, args, state):
        self.args, self.state = args, state
        self.root, self.state_path = data_path(args.root), data_path(args.state)
        self.socket = self.root / '.state/ai-lab/api.sock'
        self.bridge_url = None
        self.child = None
        self.records = []
        self.owner_diagnostics = copy.deepcopy(state.get('owner_diagnostics', {'schema': 1, 'events': []}))
        require(isinstance(self.owner_diagnostics, dict) and self.owner_diagnostics.get('schema') == 1
                and isinstance(self.owner_diagnostics.get('events'), list) and len(self.owner_diagnostics['events']) <= 4
                and len(json.dumps(self.owner_diagnostics).encode()) <= 65536,
                'Invalid private owner diagnostic structure.')
        self.diagnostic_started = time.monotonic()
        self.phase = getattr(args, 'phase', 'cleanup')
        self.validate_paths()
        self.env = minimal_environment(self.root)

    def save(self):
        self.state['last_checks'] = self.records
        write_json(self.state_path, self.state)

    def validate_paths(self):
        s = self.state
        require(s.get('format') == FORMAT and s.get('uid') == os.getuid()
                and s.get('root') == str(self.root) and s.get('state_path') == str(self.state_path),
                'State/root/UID does not match this checker invocation.')
        require(directory(self.root) == s['root_identity'], 'Owned root was replaced.')
        directory(self.root / '.upgrade-checker')
        marker_path = self.root / MARKER
        regular(marker_path, private=True)
        marker = json.loads(marker_path.read_text())
        require(marker == {k: s[k] for k in ('format', 'uid', 'root', 'state_path', 'nonce')},
                'Ownership marker does not match the original state.')
        require(s.get('socket_path') == str(self.socket), 'Refusing a substituted API socket path.')

    def early_ownership_receipt(self):
        path = self.root / '.upgrade-checker/process-owner.json'
        regular(path, private=True)
        require(json.loads(path.read_text()) == {
            'nonce': self.state['nonce'], 'owner': self.state.get('startup_owner', self.state['owner']),
            'server_argv': self.state['server_argv'], 'root': str(self.root),
            'state_path': str(self.state_path)}, 'Process receipt refuses a substituted PID/state/command.')
        if 'startup_owner' in self.state:
            self.interpreter_receipt()

    def ownership_receipt(self):
        self.early_ownership_receipt()
        if 'startup_owner' in self.state:
            ready = self.root / '.upgrade-checker/ready-owner.json'
            require(type(self.state.get('ready_owner_bound')) is bool
                    and self.state['ready_owner_bound'] == (ready.exists() or ready.is_symlink()),
                    'Ready binding phase disagrees with its immutable receipt.')
            if self.state.get('ready_owner_bound'):
                regular(ready, private=True)
                require(json.loads(ready.read_text()) == {'nonce': self.state['nonce'], 'owner': self.state['owner'],
                        'startup_owner': self.state['startup_owner'], 'server_argv': self.state['server_argv']},
                        'Ready receipt refuses a substituted owner.')
            else:
                require(self.state['owner'] == self.state['startup_owner'], 'Unready owner must match its early receipt.')

    def recover_ready_publication(self):
        """Resolve only our recorded publication transaction, before owner checks.

        A receipt/flag disagreement without this exact journal still fails.
        This method never probes, signals or adopts a process.
        """
        folder = self.root / '.upgrade-checker'
        journal_path = folder / 'ready-publication.json'
        if not journal_path.exists() and not journal_path.is_symlink():
            return
        self.validate_paths()
        self.early_ownership_receipt()
        journal_identity = file_record(journal_path)
        regular(journal_path, private=True)
        require(journal_identity['bytes'] <= 65536, 'Readiness publication journal exceeds its limit.')
        journal = json.loads(journal_path.read_text())
        require(set(journal) == {'binding_sha256', 'prior_state_sha256', 'ready_state_sha256', 'stage', 'files'}
                and journal['binding_sha256'] == object_hash({key: self.state[key]
                    for key in ('nonce', 'root', 'state_path', 'startup_owner', 'server_argv')}),
                'Readiness publication journal binding changed.')
        require(set(journal['stage']) == {'name', 'identity'}
                and re.fullmatch(r'ready-stage-[0-9a-f]{32}', journal['stage']['name']),
                'Readiness publication stage is not an owned child path.')
        stage = folder / journal['stage']['name']
        require(directory(stage) == journal['stage']['identity'], 'Readiness publication stage was replaced.')
        require(set(journal['files']) == {'ready-owner.json', 'socket-owner.json'},
                'Readiness publication receipt names changed.')
        persisted = read_state(self.state_path)
        committed = object_hash(persisted) == journal['ready_state_sha256']
        require(committed or object_hash(persisted) == journal['prior_state_sha256'],
                'Readiness publication state is neither the recorded prior nor ready state.')

        def verify(path, record):
            info = path.lstat()
            require(stat.S_ISREG(info.st_mode) and info.st_nlink in (1, 2)
                    and (info.st_dev, info.st_ino, info.st_uid, stat.S_IMODE(info.st_mode))
                    == (record['dev'], record['ino'], os.getuid(), 0o600)
                    and info.st_size == record['bytes'] and digest(path.read_bytes()) == record['sha256'],
                    'Readiness publication refuses an unverified or replaced receipt.')

        # Validate every path before removing any exact-owned alias. Linking
        # uses exclusive destination creation; a foreign receipt is never replaced.
        removals = []
        for name, record in journal['files'].items():
            staged, published = stage / name, folder / name
            if staged.exists() or staged.is_symlink():
                verify(staged, record)
                if committed:
                    removals.append((staged, record))
            if published.exists() or published.is_symlink():
                verify(published, record)
                if not committed:
                    removals.append((published, record))
            else:
                require(not committed, 'Committed readiness receipt is missing.')
        for path, record in removals:
            verify(path, record)
            path.unlink()
        self.state.clear()
        self.state.update(persisted)
        self.ownership_receipt()  # The original strict flag/receipt rules apply.
        require(file_record(journal_path) == journal_identity, 'Readiness publication journal was replaced.')
        journal_path.unlink()

    def publish_ready_owner(self, ready):
        """Stage receipts, publish exclusively, then atomically commit state."""
        folder = self.root / '.upgrade-checker'
        journal_path = folder / 'ready-publication.json'
        require(not journal_path.exists() and not journal_path.is_symlink(),
                'A readiness publication transaction already exists.')
        prior = read_state(self.state_path)
        require(prior == self.state and self.state['ready_owner_bound'] is False,
                'Readiness publication requires the exact persisted early state.')
        following = copy.deepcopy(prior)
        following.update(owner=ready, ready_owner_bound=True, socket_identity=socket_record(self.socket))
        receipts = {
            'ready-owner.json': {'nonce': self.state['nonce'], 'owner': ready,
                                'startup_owner': self.state['startup_owner'], 'server_argv': self.state['server_argv']},
            'socket-owner.json': {'nonce': self.state['nonce'], 'pid': ready['pid'],
                                 'socket_identity': following['socket_identity']}}
        stage = folder / ('ready-stage-' + uuid.uuid4().hex)
        stage.mkdir(mode=0o700)
        step = 'stage_receipts'
        try:
            for name, receipt in receipts.items():
                create_file(stage / name, json.dumps(receipt).encode())
            journal = {'binding_sha256': object_hash({key: self.state[key]
                       for key in ('nonce', 'root', 'state_path', 'startup_owner', 'server_argv')})}
            journal.update(prior_state_sha256=object_hash(prior), ready_state_sha256=object_hash(following),
                           stage={'name': stage.name, 'identity': directory(stage)},
                           files={name: file_record(stage / name) for name in receipts})
            step = 'write_journal'
            write_json(journal_path, journal)
            step = 'publish_receipts'
            for name in receipts:
                os.link(stage / name, folder / name)  # Never overwrite an existing receipt.
                (stage / name).unlink()
            step = 'commit_state'
            self.state.update(following)
            self.save()
            step = 'finish_journal'
            self.recover_ready_publication()
        except (Exception, KeyboardInterrupt) as error:
            record = {'case': 'before.ready-publication', 'status': 'FAIL', 'stage': step,
                      'error': type(error).__name__}
            try:
                self.recover_ready_publication()
            except (Exception, KeyboardInterrupt) as cleanup_error:
                record['cleanup_error'] = type(cleanup_error).__name__
            self.records.append(record)
            raise  # Preserve the actual publication error, independently of recovery.

    def interpreter_receipt(self):
        path = self.root / '.upgrade-checker/interpreter-owner.json'
        regular(path, private=True)
        require(json.loads(path.read_text()) == {'nonce': self.state['nonce'],
                'binding': self.state['interpreter_binding'], 'server_argv': self.state['server_argv']},
                'Interpreter receipt refuses substituted startup paths.')
        binding = self.state['interpreter_binding']
        require(str(Path(binding['launcher']).resolve(strict=True)) == binding['resolved_launcher'],
                'Retained interpreter launcher changed.')
        require(all(file_record(Path(path)) == record for path, record in binding['files'].items()),
                'Bound interpreter files changed.')

    def socket_receipt(self):
        saved = self.state['owner']
        receipt = self.root / '.upgrade-checker/socket-owner.json'
        regular(receipt, private=True)
        require(json.loads(receipt.read_text()) == {'nonce': self.state['nonce'], 'pid': saved['pid'],
                'socket_identity': self.state['socket_identity']}, 'Socket receipt does not match state.')

    def owner_evidence(self, moment, observed, *, inspection='PRESENT', socket_receipt_validated=False,
                       reason=None):
        """Private failure-time observations; never authorize a process action.

        The first event for each of four moments survives later phase reports.
        Only private state/--output reports contain these raw owner identities;
        the separate CI exporter must allowlist and hash commands before upload.
        """
        try:
            require(moment in OWNER_MOMENTS, 'Unknown owner diagnostic moment.')
            events = self.owner_diagnostics['events']
            if any(event.get('moment') == moment for event in events):
                return
            saved = self.state.get('owner')
            present = matches = None
            try:
                info = self.socket.lstat()
                present = True
                matches = (stat.S_ISSOCK(info.st_mode) and
                           {'dev': info.st_dev, 'ino': info.st_ino, 'uid': info.st_uid}
                           == self.state.get('socket_identity'))
            except FileNotFoundError:
                present = False
            except OSError:
                pass
            differing = ([key for key in OWNER_FIELDS if saved.get(key) != observed.get(key)]
                         if isinstance(saved, dict) and isinstance(observed, dict) else [])
            if isinstance(observed, dict) and set(observed) != set(OWNER_FIELDS):
                differing.append('unexpected_fields')
            cleanup = self.state.get('cleanup') or {}
            event = {'moment': moment, 'observation': 'late' if moment == 'late_observation' else 'at_failure',
                     'phase': self.phase,
                     'captured_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                     'elapsed_seconds': round(time.monotonic() - self.diagnostic_started, 6),
                     'process_status': inspection,
                     'reason': reason or ('IDENTITY_MISMATCH' if inspection == 'PRESENT' else
                                          'PROCESS_ABSENT' if inspection == 'ABSENT' else 'INSPECTION_ERROR'),
                     'expected': {key: saved.get(key) for key in OWNER_FIELDS} if saved is not None else None,
                     'observed': {key: observed.get(key) for key in OWNER_FIELDS} if observed is not None else None,
                     'differing_keys': differing, 'process_receipt_validated': True,
                     'socket_receipt_validated': socket_receipt_validated,
                     'socket_present': present, 'socket_identity_matches': matches,
                     'after_verified': self.state.get('after_verified') is True,
                     'state_phase': self.state.get('phase') if self.state.get('phase') in ('preparing', 'before_ready', 'cleaned') else 'UNKNOWN',
                     'process_exited': cleanup.get('process_exited') if type(cleanup.get('process_exited')) is bool else None,
                     'socket_removed': cleanup.get('socket_removed') if type(cleanup.get('socket_removed')) is bool else None,
                     'child_exit': self.child.poll() if self.child is not None else None}
            require(len(events) < 4 and len(json.dumps({'schema': 1, 'events': [*events, event]}).encode()) <= 65536,
                    'Private owner diagnostics exceed the bounded envelope.')
            events.append(copy.deepcopy(event))
            self.state['owner_diagnostics'] = copy.deepcopy(self.owner_diagnostics)
        except Exception:
            self.owner_diagnostics['capture_error'] = 'CAPTURE_ERROR'
            return
        try:
            self.save()
        except Exception:
            self.owner_diagnostics['capture_error'] = 'PERSISTENCE_ERROR'
            # The phase report still receives the captured event. Diagnostics
            # must not mask the original guard or skip its cleanup attempt.

    def observed_owner(self, moment, *, socket_receipt_validated=False, allow_startup=False):
        saved = self.state['owner']
        try:
            observed = process_identity(saved['pid'])
        except Exception:
            self.owner_evidence(moment, None, inspection='INSPECTION_ERROR',
                                socket_receipt_validated=socket_receipt_validated)
            raise
        matches = (startup_identity_matches(saved, observed, self.state['server_argv'], self.state['interpreter_binding'])
                   if allow_startup else observed == saved)
        if not matches:
            self.owner_evidence(moment, observed, inspection='PRESENT' if observed is not None else 'ABSENT',
                                socket_receipt_validated=socket_receipt_validated)
        return observed

    def owner(self, *, inspect_socket=True):
        self.validate_paths()
        self.ownership_receipt()
        self.socket_receipt()
        saved = self.state['owner']
        require(self.observed_owner('primary_before_cleanup', socket_receipt_validated=True) == saved,
                'Old API process identity changed or exited; never restart it to pass.')
        require(saved['uid'] == os.getuid() and saved['pgid'] == saved['pid']
                and saved['command'].endswith(' '.join(self.state['server_argv'])), 'Refusing an unverified PID/command.')
        require(socket_record(self.socket) == self.state['socket_identity'], 'Retained API socket was replaced.')
        if inspect_socket:
            socket_owner(saved['pid'], self.socket)

    def cli(self, executable, argv, case, *, code=0, structured=True, timeout=35):
        if self.bridge_url:
            self.owner(inspect_socket=False)
        env = {**self.env, **({'AI_LAB_SERVER': self.bridge_url} if self.bridge_url else {})}
        command = [str(executable), '--root', str(self.root), *argv]
        started = time.monotonic()
        try:
            result = subprocess.run(command, cwd=self.root, env=env, stdin=subprocess.DEVNULL,
                                    capture_output=True, timeout=timeout)
        except subprocess.TimeoutExpired as error:
            diagnostic = self.root / '.upgrade-checker' / ('timeout-' + uuid.uuid4().hex + '.json')
            payload = (json.dumps({'stdout': diagnostic_text(error.stdout),
                                  'stderr': diagnostic_text(error.stderr)}, indent=2) + '\n').encode()
            record = {'case': case, 'command': [diagnostic_text(v) for v in command],
                      'exit': None, 'expected_exit': code, 'timed_out': True,
                      'timeout_seconds': timeout, 'seconds': round(time.monotonic() - started, 3),
                      'diagnostic_path': str(diagnostic), 'diagnostic_sha256': digest(payload)}
            self.records.append(record)
            create_file(diagnostic, payload)
            raise RuntimeError(f'{case}: CLI timed out; sanitized private diagnostic retained.') from None
        self.records.append({'case': case, 'command': command, 'exit': result.returncode,
                             'expected_exit': code, 'stdout_sha256': digest(result.stdout),
                             'stderr_sha256': digest(result.stderr)})
        print(f'{case}: exit {result.returncode}', flush=True)
        require(result.returncode == code, f'{case}: unexpected CLI exit; raw output intentionally withheld.')
        if self.bridge_url:
            self.owner(inspect_socket=False)
        if structured:
            return json.loads(result.stdout if code == 0 else result.stderr)
        return result.stdout.decode().strip()

    @contextmanager
    def bridge(self):
        with forwarding_bridge(self.socket, lambda: self.owner(inspect_socket=False), self.records) as url:
            self.bridge_url = url
            try:
                yield
            finally:
                self.bridge_url = None

    def snapshots(self, relative_paths):
        return {name: file_record(self.root / name) for name in relative_paths}

    def verify_snapshots(self, records):
        require(self.snapshots(records) == records, 'Persisted file bytes or metadata changed unexpectedly.')

    def start_old(self, executable):
        argv = [str(executable), '--root', str(self.root), 'completion', '--service-action', 'run']
        self.state['server_argv'] = argv
        self.state['ready_owner_bound'] = False
        self.state['interpreter_binding'] = interpreter_binding(executable)
        create_file(self.root / '.upgrade-checker/interpreter-owner.json', json.dumps({
            'nonce': self.state['nonce'], 'binding': self.state['interpreter_binding'], 'server_argv': argv}).encode())
        self.save()
        log = self.root / '.upgrade-checker/old-api.log'
        create_file(log, b'')
        with log.open('ab') as stream:
            self.child = subprocess.Popen(argv, cwd=self.root, env=self.env, stdin=subprocess.DEVNULL,
                                          stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline and self.child.poll() is None:
            identity = (self.observed_owner('primary_before_cleanup', allow_startup=True)
                        if self.state.get('owner') else process_identity(self.child.pid))
            if self.state.get('owner'):
                if not startup_identity_matches(self.state['owner'], identity, argv, self.state['interpreter_binding']):
                    self.owner_evidence('primary_before_cleanup', identity,
                                        inspection='PRESENT' if identity is not None else 'ABSENT')
                    raise RuntimeError('Old API startup identity changed unexpectedly; refusing an unbound interpreter or process.')
            if identity and identity['command'] in [path + ' ' + ' '.join(argv)
                                                   for path in self.state['interpreter_binding']['command_interpreters']]:
                require(identity['uid'] == os.getuid() and identity['pgid'] == identity['pid'], 'Unexpected helper ownership.')
                if not self.state.get('owner'):
                    create_file(self.root / '.upgrade-checker/process-owner.json', json.dumps({
                        'nonce': self.state['nonce'], 'owner': identity, 'server_argv': argv,
                        'root': str(self.root), 'state_path': str(self.state_path)}).encode())
                    self.state['owner'] = identity
                    self.state['startup_owner'] = copy.deepcopy(identity)
                    self.save()  # Persist ownership before waiting for API readiness.
                if self.socket.exists():
                    try:
                        status, body = api_request(self.socket, 'GET', '/api/lab/health')
                        health = json.loads(body)
                    except (OSError, ValueError):
                        status, health = None, None
                    if status == 200 and health == {'application': 'ai-lab', 'api_version': 1, 'root': str(self.root)}:
                        self.ownership_receipt()
                        socket_owner(self.child.pid, self.socket)
                        ready = self.observed_owner('primary_before_cleanup', allow_startup=True)
                        require(startup_identity_matches(self.state['owner'], ready, argv, self.state['interpreter_binding']),
                                'Old API ready identity is not the bound startup process.')
                        self.publish_ready_owner(ready)
                        self.owner()
                        return
            time.sleep(.1)
        if self.state.get('owner'):
            observed = self.observed_owner('primary_before_cleanup', allow_startup=True)
            self.owner_evidence('primary_before_cleanup', observed,
                                inspection='PRESENT' if observed is not None else 'ABSENT',
                                reason='READINESS_TIMEOUT' if self.child.poll() is None else 'PROCESS_ABSENT')
        raise RuntimeError('Owned 0.1.13 API failed to start; raw log remains private in owned root.')

    def before(self, executable):
        require(self.cli(executable, ['--version'], 'before.version', structured=False) == 'AI Lab 0.1.13',
                'BEFORE requires literal AI Lab 0.1.13.')
        self.state['old_executable'] = {'path': str(executable), 'version': '0.1.13',
                                        'file': file_record(executable), 'package': package_record(executable)}
        if self.state['context'] == 'homebrew':
            self.state['old_keg'] = keg(executable, '0.1.13')
        self.save()
        self.start_old(executable)
        profiles, sessions = [], []
        with self.bridge():
            for index, family in enumerate(('deepseek', 'qwen')):
                settings = self.root / f'.upgrade-checker/{family}-settings.json'
                create_file(settings, json.dumps({'scheme': 'synthid', 'key': ('11' if index == 0 else '22') * 32,
                                                  'generation_policy': 'tournament', 'depth': 3 + index}).encode())
                profile = self.cli(executable, ['models', 'create', '--name', f'Upgrade [{family}] saved profile',
                                  '--underlying-model', family, '--seed', '0x2a' if index == 0 else '84',
                                  '--watermark-file', str(settings), '--json'], 'before.create.' + family)
                require(profile['underlying_model'] == ('DeepSeekR1' if index == 0 else 'Qwen3-8B')
                        and profile['watermark']['depth'] == 3 + index, 'Old profile backend/settings mismatch.')
                profiles.append({'key': profile['key'], 'name': profile['name'], 'sha256': object_hash(profile)})
                selector = ['--name', profile['name']] if index == 0 else ['--model', profile['key']]
                session = self.cli(executable, ['completion', '--session-action', 'create', *selector,
                                  '--session-name', 'Before ' + family, '--temperature', '.7', '--json'], 'before.session.' + family)
                require(session['model'] == profile['key'] and session['temperature'] == .7, 'Old session routing/settings mismatch.')
                sessions.append({'id': session['id'], 'model': profile['key'], 'sha256': object_hash(session)})
            catalog = self.cli(executable, ['models', 'list', '--json'], 'before.catalog')['models']
        self.state.update(profiles=profiles, sessions=sessions,
                          catalog={p['key']: object_hash(p) for p in catalog})
        sentinels = []
        for kind in ('weights', 'runtime'):
            folder = '.models' if kind == 'weights' else '.runtime'
            relative = f'{folder}/upgrade-checker/{kind}.sentinel'
            data = f'TINY INERT {kind} fixture: preservation mechanics only; never loaded or executed.\n'.encode()
            create_file(self.root / relative, data)
            receipt = relative + '.verified-mechanics.json'
            create_file(self.root / receipt, json.dumps({'fixture': True, 'native_validity': False,
                        'sha256': digest(data), 'bytes': len(data)}).encode())
            sentinels.extend([relative, receipt])
        self.state['sentinels'] = self.snapshots(sentinels)
        paths = ['harness/models.json', 'sources.json', 'deepseek-chat.jinja', 'qwen-chat.jinja', 'offline.sb']
        paths += [f'.state/ai-lab/sessions/{s["id"]}.json' for s in sessions]
        self.state['persistent_files'] = self.snapshots(paths)
        self.state['phase'] = 'before_ready'
        self.owner()
        self.save()

    def after(self, executable):
        require(self.state['phase'] == 'before_ready', 'AFTER requires the original successful BEFORE state.')
        self.owner()
        old = self.state['old_executable']
        require(file_record(Path(old['path'])) == old['file'] and package_record(Path(old['path'])) == old['package'],
                'Retained 0.1.13 executable/package changed or disappeared.')
        require(self.cli(Path(old['path']), ['--version'], 'after.retained-version', structured=False) == 'AI Lab 0.1.13',
                'Retained owner path no longer resolves to literal 0.1.13.')
        require(self.cli(executable, ['--version'], 'after.version', structured=False) == 'AI Lab 0.1.14',
                'AFTER requires literal AI Lab 0.1.14.')
        self.state['new_executable'] = {'path': str(executable), 'version': '0.1.14', 'file': file_record(executable)}
        if self.state['context'] == 'homebrew':
            new = keg(executable, '0.1.14')
            old_keg = self.state['old_keg']
            require(all(new[k] == old_keg[k] for k in ('cellar', 'formula')), 'Upgrade changed Homebrew Cellar/formula identity.')
            self.state['new_keg'] = new
        self.verify_snapshots(self.state['persistent_files'])
        self.verify_snapshots(self.state['sentinels'])
        with self.bridge():
            models = self.cli(executable, ['models', 'list', '--json'], 'after.catalog')['models']
            require({p['key']: object_hash(p) for p in models} == self.state['catalog'], 'Saved catalog did not survive upgrade.')
            for session in self.state['sessions']:
                current = self.cli(executable, ['completion', '--session-action', 'get', '--session', session['id'], '--json'],
                                   'after.old-session')
                require(object_hash(current) == session['sha256'], 'Saved session changed across upgrade.')
            profiles = self.state['profiles']
            expected = copy.deepcopy(next(p for p in models if p['key'] == profiles[1]['key']))
            settings = self.root / '.upgrade-checker/after-settings.json'
            create_file(settings, b'{"depth": 5}')
            changed = self.cli(executable, ['models', 'update', profiles[1]['key'], '--watermark-file', str(settings), '--json'],
                               'after.update-settings')
            expected['watermark']['depth'] = 5
            require(changed == expected, 'Explicit settings update changed unrelated saved profile fields.')
            added = self.cli(executable, ['models', 'create', '--name', 'After 14 saved profile', '--underlying-model', 'deepseek',
                                         '--seed', '7', '--json'], 'after.create-profile')
            created_sessions = []
            for index, profile in enumerate(profiles):
                selector = ['--name', profile['name']] if index == 0 else ['--model', profile['key']]
                created = self.cli(executable, ['completion', '--session-action', 'create', *selector,
                                   '--session-name', f'After switch {index}', '--temperature', '.8', '--json'],
                                   'after.switch-by-' + ('name' if index == 0 else 'id'))
                require(created['model'] == profile['key'] and created['profile']['name'] == profile['name']
                        and created['temperature'] == .8, 'New session selected an incorrect profile/settings.')
                expected_profile = changed if index == 1 else next(p for p in models if p['key'] == profile['key'])
                public_profile = copy.deepcopy({k: v for k, v in expected_profile.items() if k != 'key'})
                public_profile['watermark'].pop('key', None)
                require(created['profile'] == public_profile and created['watermark'] == public_profile['watermark'],
                        'New session lost saved settings or failed to redact its watermark key.')
                created_sessions.append(created['id'])
            require(len(set(created_sessions)) == 2, 'Model switch must use distinct persistent sessions.')
            self.cli(executable, ['completion', '--session-action', 'create', '--session', self.state['sessions'][0]['id'],
                                 '--name', profiles[1]['name'], '--json'], 'after.reject-existing-session-retarget', code=1)
            final = self.cli(executable, ['models', 'list', '--json'], 'after.verify-catalog')['models']
            expected_catalog = {**self.state['catalog'], changed['key']: object_hash(changed), added['key']: object_hash(added)}
            require({p['key']: object_hash(p) for p in final} == expected_catalog, 'Unrelated models changed during settings update.')
            for session in self.state['sessions']:
                current = self.cli(executable, ['completion', '--session-action', 'get', '--session', session['id'], '--json'],
                                   'after.verify-old-session')
                require(object_hash(current) == session['sha256'], 'Existing session was retargeted or changed.')
            # Prove file persistence, not just a response held in API memory.
            registry = json.loads((self.root / 'harness/models.json').read_text())
            require({p['key']: object_hash(p) for p in registry['models']} == expected_catalog,
                    'Updated catalog/settings differ from the actual persisted registry.')
            for sid in created_sessions:
                saved = json.loads((self.root / f'.state/ai-lab/sessions/{sid}.json').read_text())
                require(saved['id'] == sid and saved['model'] in {p['key'] for p in profiles}, 'New session not persisted.')
                persisted_profile = next(p for p in final if p['key'] == saved['model'])
                require(saved['profile'] == {k: v for k, v in persisted_profile.items() if k != 'key'}
                        and saved['watermark'] == persisted_profile['watermark'] and saved['temperature'] == .8,
                        'Full private session settings were not preserved on disk.')
            self.state['new_sessions'] = created_sessions
        preserved = {k: v for k, v in self.state['persistent_files'].items() if k != 'harness/models.json'}
        self.verify_snapshots(preserved)
        self.verify_snapshots(self.state['sentinels'])
        self.owner()
        self.state['after_verified'] = True
        self.state['source_sha_supplied'] = self.args.source_sha
        self.save()

    def cleanup(self):
        self.validate_paths()
        self.recover_ready_publication()
        saved = self.state.get('owner')
        if saved is None and 'server_argv' not in self.state:
            require(not self.socket.exists(), 'No recorded helper; refusing an unexpected socket.')
            self.state.update(phase='cleaned', cleanup={'no_helper_launched': True, 'socket_removed': True})
            self.save()
            return
        require(saved is not None, 'No recorded owned helper; no process action authorized.')
        self.ownership_receipt()
        startup = 'startup_owner' in self.state and not self.state.get('ready_owner_bound')
        observed = self.observed_owner('explicit_cleanup' if self.phase == 'cleanup' else 'internal_cleanup',
                                       allow_startup=startup)
        if observed is not None:
            require(startup_identity_matches(saved, observed, self.state['server_argv'], self.state['interpreter_binding'])
                    if startup else observed == saved, 'Cleanup refuses changed/foreign PID identity.')
            require(saved['uid'] == os.getuid() and saved['pgid'] == saved['pid'] and
                    saved['command'].endswith(' '.join(self.state['server_argv'])), 'Cleanup refuses unverified owner command.')
            if self.socket.exists():
                if 'socket_identity' in self.state:
                    self.socket_receipt()
                    require(socket_record(self.socket) == self.state['socket_identity'], 'Cleanup refuses replaced socket.')
                socket_owner(saved['pid'], self.socket)
                status, _ = api_request(self.socket, 'POST', '/api/lab/shutdown')
                require(status == 200, 'Owned API refused shutdown.')
            else:
                os.kill(saved['pid'], signal.SIGINT)
            deadline = time.monotonic() + 12
            while time.monotonic() < deadline:
                if self.child:
                    self.child.poll()
                current = self.observed_owner('explicit_cleanup' if self.phase == 'cleanup' else 'internal_cleanup',
                                              allow_startup=startup)
                if current is None:
                    break
                require(startup_identity_matches(saved, current, self.state['server_argv'], self.state['interpreter_binding'])
                        if startup else current == saved, 'Old API changed identity during cleanup.')
                time.sleep(.1)
            require(process_identity(saved['pid']) is None, 'Old API did not exit; refusing a replacement owner.')
        stale_removed = False
        if self.socket.exists() or self.socket.is_symlink():
            self.socket_receipt()
            remove_stale_socket(self.socket, self.state['socket_identity'], saved)
            stale_removed = True
        require(not self.socket.exists() and not self.socket.is_symlink(), 'API socket remains after owned cleanup.')
        self.state['cleanup'] = {'pid': saved['pid'], 'process_exited': True, 'socket_removed': True,
                                 'stale_socket_removed': stale_removed}
        self.state['phase'] = 'cleaned'
        self.save()
        self.owner_evidence('late_observation', None, inspection='ABSENT', reason='CLEANUP_COMPLETE',
                            socket_receipt_validated=stale_removed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', required=True, choices=('before', 'after', 'cleanup'))
    parser.add_argument('--executable', help='BEFORE: stable old keg/venv/bin/ai-lab; AFTER: final 0.1.14 entrypoint')
    parser.add_argument('--root', required=True, help='New empty private root for BEFORE; identical owned root later')
    parser.add_argument('--state', required=True, help='Private JSON outside the root, in an owned directory not writable by others')
    parser.add_argument('--source-sha', help='AFTER: full final source SHA supplied by root; artifact binding is external')
    parser.add_argument('--output', help='AFTER: new private JSON result; optional for BEFORE/CLEANUP')
    parser.add_argument('--context', choices=('homebrew', 'isolated-env'), default='homebrew',
                        help='BEFORE only: isolated-env is supplemental, never literal Homebrew evidence')
    args = parser.parse_args()
    if args.phase != 'cleanup' and not args.executable:
        parser.error('before/after require --executable')
    if args.phase == 'after' and (not args.output or not re.fullmatch('[0-9a-f]{40}', args.source_sha or '')):
        parser.error('after requires --output and a full --source-sha')
    report = {'phase': args.phase, 'status': 'FAIL', 'full_release_pass': False,
              'native_inference': False, 'sentinels': 'tiny inert mechanics fixtures only',
              'brew_execution_verified': False, 'artifact_binding': 'root/CI responsibility',
              'checker_sha256': digest(Path(__file__).read_bytes())}
    upgrade = None
    lock_fd = None
    output = None
    try:
        root, state_path = data_path(args.root), data_path(args.state)
        directory(state_path.parent, private=False)
        require(not state_path.is_relative_to(root), 'Keep state outside the data root.')
        require(len(os.fsencode(root / '.state/ai-lab/api.sock')) < 100,
                'Choose a shorter owned root; this checker intentionally avoids external socket fallback paths.')
        if args.output:
            candidate = data_path(args.output)
            directory(candidate.parent, private=False)
            require(not candidate.exists() and not candidate.is_symlink() and candidate != state_path
                    and not candidate.is_relative_to(root), 'Use a new output file outside root/state.')
            output = candidate
        lock_path = state_path.with_name(state_path.name + '.lock')
        if args.phase == 'before':
            require(not state_path.exists() and not state_path.is_symlink(), 'BEFORE refuses an existing state file.')
            require(not root.exists() or (directory(root) and not any(root.iterdir())), 'BEFORE requires a new or empty owned root.')
            lock_fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        else:
            regular(lock_path, private=True)
            lock_fd = os.open(lock_path, os.O_RDWR | os.O_NOFOLLOW)
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.phase == 'before':
            executable = absolute(args.executable)
            require(executable == executable.resolve(), 'BEFORE refuses opt/bin links; pass the stable retained keg/venv entrypoint.')
            if not root.exists():
                root.mkdir(mode=0o700)
            identity = directory(root)
            state = {'format': FORMAT, 'phase': 'preparing', 'uid': os.getuid(), 'root': str(root),
                     'state_path': str(state_path), 'root_identity': identity, 'nonce': uuid.uuid4().hex,
                     'context': args.context, 'socket_path': str(root / '.state/ai-lab/api.sock')}
            create_file(root / MARKER, json.dumps({k: state[k] for k in ('format', 'uid', 'root', 'state_path', 'nonce')}).encode())
            write_json(state_path, state)
        else:
            state = read_state(state_path)
            executable = absolute(args.executable).resolve() if args.executable else None
        upgrade = Upgrade(args, state)
        upgrade.validate_paths()
        report.update(context=state['context'], root=str(root), state=str(state_path),
                      source_sha_supplied=args.source_sha)
        if args.phase == 'before':
            upgrade.before(executable)
        elif args.phase == 'after':
            try:
                upgrade.after(executable)
            except (Exception, KeyboardInterrupt):
                try:
                    upgrade.cleanup()
                except (Exception, KeyboardInterrupt) as cleanup_error:
                    report['cleanup_error'] = (str(cleanup_error) if isinstance(cleanup_error, RuntimeError)
                                               else type(cleanup_error).__name__ + ' (details withheld)')
                raise  # Keep the original AFTER failure as the primary report error.
            else:
                try:
                    upgrade.cleanup()
                except (Exception, KeyboardInterrupt) as cleanup_error:
                    report['cleanup_error'] = (str(cleanup_error) if isinstance(cleanup_error, RuntimeError)
                                               else type(cleanup_error).__name__ + ' (details withheld)')
                    raise RuntimeError('AFTER proof completed but owned cleanup failed.') from None
        else:
            upgrade.cleanup()
        report.update(status='PASS', context=state['context'], root=str(root), state=str(state_path),
                      owner=state.get('owner'), old_executable=state.get('old_executable'),
                      new_executable=state.get('new_executable'), cleanup=state.get('cleanup'),
                      source_sha_supplied=state.get('source_sha_supplied'), after_verified=state.get('after_verified', False),
                      transport='owned loopback bridge forwards unchanged requests/responses to retained real 0.1.13 Unix API')
    except (Exception, KeyboardInterrupt) as error:
        # App subprocess output and arbitrary OSError filenames are withheld.
        report['error'] = str(error) if isinstance(error, RuntimeError) else type(error).__name__ + ' (details withheld)'
        if upgrade and args.phase == 'before' and upgrade.child is not None:
            try:
                if upgrade.state.get('owner'):
                    upgrade.cleanup()
                elif upgrade.child.poll() is None:
                    upgrade.child.terminate()
                    upgrade.child.wait(timeout=10)
            except Exception:
                report['cleanup_error'] = 'Retained helper cleanup needs the explicit cleanup phase with original state.'
    finally:
        if upgrade:
            report['checks'] = upgrade.records
            report['owner_diagnostics'] = upgrade.owner_diagnostics
            report.setdefault('cleanup', upgrade.state.get('cleanup'))
            report.setdefault('after_verified', upgrade.state.get('after_verified', False))
        if lock_fd is not None:
            os.close(lock_fd)
    if output is not None:
        try:
            create_file(output, (json.dumps(report, indent=2) + '\n').encode())
        except Exception:
            report['output_error'] = 'WRITE_ERROR'
            if report['status'] == 'PASS':
                report.update(status='FAIL', error='Private phase report could not be written; use retained state for cleanup.')
    print(json.dumps({k: report.get(k) for k in ('phase', 'status', 'context', 'after_verified', 'error', 'cleanup_error', 'output_error')} |
                     {'checks': len(report.get('checks', [])), 'state': args.state, 'output': str(output) if output else None}))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())

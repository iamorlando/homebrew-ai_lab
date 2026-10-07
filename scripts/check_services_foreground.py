"""Public foreground CLI proof using owned Python loopback processes, never models.

Only discovery, model prerequisites, and the runtime launcher are CPU fixtures.
The CLI parser, services _script/perform/_launch/_stop/close, process ownership
receipts, process groups, signals, child waits, and shutdown records are real.
"""
import argparse
import asyncio
from contextlib import ExitStack
from dataclasses import replace
import json
import os
from pathlib import Path
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import time
import uuid
from types import SimpleNamespace
from unittest.mock import patch
from urllib.request import urlopen


SERVER = '''import argparse, json, os, signal
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
parser = argparse.ArgumentParser()
parser.add_argument('-m')
parser.add_argument('--host')
parser.add_argument('-p', type=int)
parser.add_argument('--token-source')
args = parser.parse_args()
running = True
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/exit0':
            os._exit(0)
        body = json.dumps({'fixture': 'owned CPU loopback', 'pid': os.getpid()}).encode()
        self.send_response(200)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *args):
        pass
server = HTTPServer((args.host, args.p), Handler)
server.timeout = .05
def stop(sig, frame):
    global running
    if not Path('ignore-signal').exists():
        running = False
signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
while running:
    server.handle_request()
server.server_close()
'''


def require(value, message):
    if not value:
        raise RuntimeError(message)


def atomic(path, value):
    from ai_lab.service import atomic_json
    atomic_json(path, value)


def listening(port):
    with socket.socket() as client:
        client.settimeout(.15)
        return client.connect_ex(('127.0.0.1', port)) == 0


def wait_until(predicate, message, timeout=8):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(.015)
    raise RuntimeError(message)


def fixture_cli(root, port, role, action, mode):
    """A test-only launcher around the actual source or installed CLI entry point."""
    from ai_lab.paths import load_backend
    load_backend(root)
    from ai_lab import cli, decision_processes
    import ai_lab.service_manager as sm
    from ai_lab.service import atomic_json
    root = root.resolve()
    endpoint = f'http://127.0.0.1:{port}'
    ack_seconds = 2 if mode in {'durability-starter', 'post-replace-fsync-failure', 'post-replace-open-failure', 'backup-prepare-gate'} else .75
    events = {'reports': [], 'wait_codes': [], 'signals': [],
              'executable': sys.executable, 'package': str(Path(cli.__file__).resolve()),
              'argv': ['--root', str(root), 'services', '--action', action, '--model', 'contrastive', '--json'],
              'shutdown_ack_seconds_fixture': ack_seconds,
              'fixture_invocation': [sys.executable, *sys.argv]}
    report = root / (role + '.report.json')

    def save():
        atomic_json(report, events)

    class Reporter:
        def __init__(self, *_):
            pass

        async def report(self, state, **_):
            events['reports'].append(state)
            save()

        async def close(self):
            events['closed'] = True
            save()

    class Manager:
        def __init__(self):
            self.root = root
            self.decisions = SimpleNamespace(root=root, url=endpoint, process=None, log=None,
                                             process_state=None, laya_process=None, laya_log=None,
                                             upstream_process=None, upstream_log=None)

        async def start(self, names):
            require(names == ['contrastive'], 'Fixture permits only the selected CPU process')
            argv = decision_processes.command(root, endpoint)
            process = await asyncio.create_subprocess_exec(
                *argv, cwd=root, stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            self.decisions.process = process
            real_wait = process.wait

            async def child_wait():
                result = await real_wait()
                events['wait_codes'].append(result)
                save()
                (root / (role + '.waited')).touch()
                if mode == 'before-wait':
                    deadline = asyncio.get_running_loop().time() + 8
                    while not (root / 'release-wait').exists():
                        require(asyncio.get_running_loop().time() < deadline, 'Child wait gate timed out')
                        await asyncio.sleep(.01)
                return result
            process.wait = child_wait
            deadline = asyncio.get_running_loop().time() + 5
            while not await asyncio.to_thread(listening, port):
                require(process.returncode is None and asyncio.get_running_loop().time() < deadline,
                        'CPU listener did not become ready')
                await asyncio.sleep(.01)
            saved = await asyncio.to_thread(decision_processes.capture_process, root, endpoint, argv, process)
            self.decisions.process_state = saved
            decision_processes.record_state(root, saved)
            atomic_json(root / (role + '.launch.json'), saved)

    async def initialize(self):
        if self.manager is None:
            sm.safe_workspace(root)
            self.manager = Manager()
            self.decision_managers['contrastive'] = self.manager

    async def snapshot(self):
        await self._initialize()
        identity = await asyncio.to_thread(self._identity, 'contrastive')
        active = await asyncio.to_thread(listening, port)
        ownership = ('this manager' if self.created.get('contrastive') == identity else 'workspace') if identity else ('external' if active else 'none')
        return {'root': str(root), 'profiles': [], 'services': [{
            'name': 'contrastive', 'label': 'Owned CPU fixture',
            'status': 'running' if active else 'stopped', 'ownership': ownership,
            'endpoint': endpoint, 'detail': 'Owned CPU fixture', 'ready': True,
            'weights_present': True, 'actions': {
                'start': not active, 'stop': bool(identity), 'restart': bool(identity),
                'interrupt': bool(identity)}}]}

    original_publish = sm.NativeServices._publish_shutdown
    original_completed = sm.NativeServices._completed_shutdown
    original_perform = sm.NativeServices.perform

    async def cancellation_observer(self, action, name):
        current = asyncio.current_task()

        async def observe():
            while not current.cancelling():
                await asyncio.sleep(.005)
            events['cancellation_observed'] = True
            save()
            (root / (role + '.cancel-requested')).touch()

        monitor = asyncio.create_task(observe())
        try:
            return await original_perform(self, action, name)
        finally:
            monitor.cancel()
            await asyncio.gather(monitor, return_exceptions=True)
            events['cancel_settled_after_publication'] = (root / (role + '.published')).exists()
            events['receipt_retained_after_cancel'] = (root / '.state/decisions-mistral.json').exists()
            events['created_after_cancel'] = list(self.created)
            events['pending_after_cancel'] = list(self.pending)
            events['operation_lock_after_cancel'] = self.lock.locked()
            save()
            (root / (role + '.perform-settled')).touch()

    def completed(self, name, identity):
        value = original_completed(self, name, identity)
        (root / (role + '.completion-read')).touch()
        return value

    real_signal = os.killpg
    real_fsync = os.fsync
    real_open = os.open
    real_replace = Path.replace
    real_pid_exists = sm._pid_exists
    real_subprocess_run = subprocess.run

    def inspection_failure(argv, *args, **kwargs):
        if argv[0] == 'ps' and events['signals']:
            events['inspection_failed_after_dispatch'] = True
            save()
            return subprocess.CompletedProcess(argv, 1, stdout='', stderr='CPU fixture ps inspection failure')
        return real_subprocess_run(argv, *args, **kwargs)

    def delayed_existence_probe(pid):
        observed = real_pid_exists(pid)
        if observed and not events.get('present_then_absent_before_fingerprint'):
            # Retain an actual positive existence observation while the real
            # child exits and its original asyncio owner reaps it.
            wait_until(lambda: not real_pid_exists(pid), 'CPU child did not finish during existence probe')
            events['present_then_absent_before_fingerprint'] = True
            save()
        return observed

    def observe_replace(path, target):
        result = real_replace(path, target)
        if Path(target) == root / '.state/service-shutdown/contrastive.json':
            events['publication_replaced'] = True
            save()
        return result

    def open_directory(path, flags, *args, **kwargs):
        if (Path(path) == root / '.state/service-shutdown'
                and events.get('publication_replaced')):
            if (root / 'gate-open').exists():
                (root / (role + '.open-entered')).touch()
                wait_until(lambda: (root / 'release-open').exists(), 'Directory open failure gate timed out')
            events['post_replace_open_failed'] = True
            save()
            raise OSError('CPU fixture post-replace directory open failure')
        return real_open(path, flags, *args, **kwargs)

    def prepare_fsync(fd):
        info = os.fstat(fd)
        staged = root / '.state/service-shutdown/.contrastive.tmp'
        try:
            staged_info = staged.stat()
        except FileNotFoundError:
            staged_info = None
        if (not events.get('backup_prepare_entered') and stat.S_ISREG(info.st_mode)
                and staged_info is not None
                and (info.st_dev, info.st_ino) == (staged_info.st_dev, staged_info.st_ino)):
            events['backup_prepare_entered'] = True
            events['fixture_fsync_gate'] = 'first staged-file fsync before committed-backup publication'
            save()
            (root / (role + '.prepare-entered')).touch()
            wait_until(lambda: (root / 'release-prepare').exists(), 'Backup preparation gate timed out')
            events['backup_prepare_released'] = True
            save()
        return real_fsync(fd)

    def fsync(fd):
        if (stat.S_ISDIR(os.fstat(fd).st_mode)
                and events.get('publication_replaced')):
            (root / (role + '.fsync-entered')).touch()
            wait_until(lambda: (root / 'release-fsync').exists(), 'Directory fsync failure gate timed out')
            events['post_replace_fsync_failed'] = True
            save()
            raise OSError('CPU fixture post-replace directory fsync failure')
        return real_fsync(fd)

    def dispatch(pid, sig):
        if mode == 'dispatch-lookup':
            raise ProcessLookupError('fixture disappearance before dispatch')
        if mode == 'dispatch-denied':
            raise PermissionError('fixture refused dispatch')
        real_signal(pid, sig)
        events['signals'].append([pid, int(sig)])
        save()

    def publish(self, name, identity, sig):
        (root / (role + '.publish-entered')).touch()
        if mode in {'after-wait', 'after-timeout', 'cancel-publication'}:
            wait_until(lambda: (root / 'release-publish').exists(), 'Publication gate timed out')
        if mode == 'publish-failed':
            raise OSError('fixture publication failure')
        if mode in {'wrong-launch', 'malformed', 'deep-malformed', 'incomplete', 'empty'}:
            identity = replace(identity, state={**identity.state, 'started_at_ns': identity.state['started_at_ns'] + 1})
        elif mode == 'wrong-pid':
            identity = replace(identity, pid=identity.pid + 1000000)
        elif mode == 'wrong-fingerprint':
            identity = replace(identity, fingerprint=identity.fingerprint + ' changed')
        elif mode == 'wrong-backend':
            name = 'laya'
        elif mode == 'wrong-origin':
            identity = replace(identity, state={**identity.state, 'root': str(root / 'other-owned-origin')})
            (root / 'other-owned-origin').mkdir(exist_ok=True)
        if mode == 'stale':
            with patch('ai_lab.service_manager.time.time_ns', return_value=time.time_ns() - 3600 * 10**9):
                original_publish(self, name, identity, sig)
        else:
            original_publish(self, name, identity, sig)
        path = root / '.state/service-shutdown/contrastive.json'
        if mode == 'malformed':
            path.write_text('{')
        elif mode == 'deep-malformed':
            path.write_text('[' * 1200 + ']' * 1200)
            events['malformed_ack_bytes'] = path.stat().st_size
            save()
        elif mode == 'incomplete':
            path.write_text(json.dumps({'completed': False}))
        elif mode == 'empty':
            path.write_text('{}')
        (root / (role + '.published')).touch()

    with ExitStack() as stack:
        stack.enter_context(patch.object(sm.NativeServices, '_initialize', initialize))
        stack.enter_context(patch.object(sm.NativeServices, 'snapshot', snapshot))
        stack.enter_context(patch.object(sm.NativeServices, '_publish_shutdown', publish))
        stack.enter_context(patch.object(sm.NativeServices, '_completed_shutdown', completed))
        stack.enter_context(patch.object(sm, 'HerdrReporter', Reporter))
        stack.enter_context(patch.object(sm, 'SHUTDOWN_ACK_SECONDS', ack_seconds))
        stack.enter_context(patch('ai_lab.runtime.install_decisions', return_value={'cpu_fixture': True}))
        stack.enter_context(patch('ai_lab.paths.known_model_roots', return_value=[]))
        stack.enter_context(patch('ai_lab.decision_processes.listener_owner', return_value=None))
        stack.enter_context(patch('os.killpg', side_effect=dispatch))
        if mode == 'inspection-failed':
            stack.enter_context(patch('subprocess.run', side_effect=inspection_failure))
        if mode == 'exit-between-probes':
            stack.enter_context(patch.object(sm, '_pid_exists', side_effect=delayed_existence_probe))
        if mode in {'post-replace-open-failure', 'post-replace-fsync-failure'}:
            stack.enter_context(patch.object(Path, 'replace', observe_replace))
        if mode == 'post-replace-open-failure':
            stack.enter_context(patch('ai_lab.service_manager.os.open', side_effect=open_directory))
        if mode == 'post-replace-fsync-failure':
            stack.enter_context(patch('ai_lab.service_manager.os.fsync', side_effect=fsync))
        if mode == 'backup-prepare-gate':
            stack.enter_context(patch('ai_lab.service_manager.os.fsync', side_effect=prepare_fsync))
        if mode == 'cancel-publication':
            stack.enter_context(patch.object(sm.NativeServices, 'perform', cancellation_observer))
        if mode in {'dispatch-lookup', 'dispatch-denied', 'stop-timeout', 'exec-alive'}:
            stack.enter_context(patch.object(sm, 'STOP_SECONDS', .15))
        code = cli.main(['--root', str(root), 'services', '--action', action,
                         '--model', 'contrastive', '--json'])
    events['exit_code'] = code
    save()
    return code


class ForegroundProof:
    def __init__(self, root):
        self.root = root.resolve()
        self.children = []
        self.results = []
        self.environment = {key: value for key, value in os.environ.items()
                            if not key.startswith(('HERDR_', 'AI_LAB_', 'DEEPSEEK_', 'QWEN_'))}
        self.environment.update(AI_LAB_DECISIONS_BINARY=str(Path(sys.executable).resolve()),
                                PYTHONUNBUFFERED='1')
        # A source run names the checkout explicitly. Installed runs never add it.
        import ai_lab
        package = Path(ai_lab.__file__).resolve().parent
        if not (package / '_bundle').is_dir():
            self.environment['PYTHONPATH'] = str(package.parent)
        else:
            self.environment.pop('PYTHONPATH', None)
        self.package = str(package / '__init__.py')

    def start(self, root, port, role, action, mode='normal'):
        environment = {**self.environment, 'AI_LAB_DECISIONS_URL': f'http://127.0.0.1:{port}'}
        log = (root / (role + '.out')).open('w')
        error = (root / (role + '.err')).open('w')
        try:
            child = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--fixture-cli',
                                      str(root), str(port), role, action, mode],
                                     cwd=root, env=environment, stdin=subprocess.DEVNULL,
                                     stdout=log, stderr=error, start_new_session=True)
        finally:
            log.close()
            error.close()
        self.children.append(child)
        return child

    def ready(self, child, root, role):
        def running():
            if child.poll() is not None:
                raise RuntimeError(f'{root.name}: {role} failed before ready: ' + (root / (role + '.err')).read_text())
            path = root / (role + '.out')
            return path.exists() and '"status": "running"' in path.read_text()
        wait_until(running, f'{root.name}: {role} CLI did not report running')
        return json.loads((root / (role + '.launch.json')).read_text())

    def finish(self, child, root, role, expected):
        code = child.wait(timeout=10)
        require(code == expected, f'{root.name}: {role} returned {code}, expected {expected}: ' + (root / (role + '.err')).read_text())
        data = json.loads((root / (role + '.report.json')).read_text())
        require(data.get('closed'), f'{root.name}: reporter did not close')
        if expected == 0 or role == 'starter':
            require(data['reports'][-1] == 'idle', f'{root.name}: reporter did not settle')
        if data['argv'][4] in {'start', 'restart'} and expected in {0, 1}:
            require(data['wait_codes'], f'{root.name}: original child was not reaped')
            output = (root / (role + '.out')).read_text()
            error = (root / (role + '.err')).read_text()
            if expected == 0:
                require('"event": "service_stopped"' in output and 'invalid_request' not in error,
                        f'{root.name}: normal completion event missing')
            else:
                require('invalid_request' in error and '"event": "service_stopped"' not in output,
                        f'{root.name}: unexpected exit was hidden')
        return data

    def cleanup(self, root):
        from ai_lab.decision_processes import process_fingerprint
        for path in root.glob('*.launch.json'):
            state = json.loads(path.read_text())
            current = process_fingerprint(state['pid'])
            marker = root / 'exec-marker'
            known_exec = (marker.exists() and current and marker.read_text() in current
                          and current.split(None, 6)[:6] == state['fingerprint'].split(None, 6)[:6])
            if current == state['fingerprint'] or known_exec:
                os.killpg(state['pid'], signal.SIGKILL)
        for child in self.children:
            try:
                child.wait(timeout=3)  # Let its real asyncio handle reap the CPU child.
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=5)
        self.children.clear()

    def case(self, name, action='stop', mode='normal', crash=None):
        root = self.root / name
        verifications = {}
        root.mkdir(parents=True)
        server = SERVER
        if mode == 'exec-alive':
            marker = 'ai-lab-owned-cpu-exec-' + uuid.uuid4().hex
            (root / 'exec-marker').write_text(marker)
            code = 'import time; time.sleep(60) # ' + marker
            server = server.replace('import argparse, json, os, signal', 'import argparse, json, os, signal, sys')
            server = server.replace('running = False',
                                    f'os.execv(sys.executable, [sys.executable, \'-c\', {code!r}])')
        elif mode == 'exit-between-probes':
            server = server.replace('import argparse, json, os, signal', 'import argparse, json, os, signal, time')
            server = server.replace('running = False', 'time.sleep(.3)\n        running = False')
        (root / 'serve').write_text(server)
        with socket.socket() as reserve:
            reserve.bind(('127.0.0.1', 0))
            port = reserve.getsockname()[1]
        starter_mode = ('before-wait' if mode == 'before-wait' else
                        'durability-starter' if mode in {'post-replace-fsync-failure', 'post-replace-open-failure'} else 'normal')
        starter = self.start(root, port, 'starter', 'start', starter_mode)
        try:
            first = self.ready(starter, root, 'starter')
            if crash == 'zero':
                try:
                    urlopen(f'http://127.0.0.1:{port}/exit0', timeout=2).read()
                except OSError:
                    pass
                self.finish(starter, root, 'starter', 1)
            elif crash is not None:
                os.killpg(first['pid'], crash)
                data = self.finish(starter, root, 'starter', 1)
                if crash == signal.SIGKILL:
                    require(data['wait_codes'][0] == -signal.SIGKILL, 'Unhandled signal crash was not retained')
            elif action == 'ctrl-c':
                os.kill(starter.pid, signal.SIGINT)
                self.finish(starter, root, 'starter', 130)
            else:
                if mode in {'stop-timeout', 'inspection-failed'}:
                    (root / 'ignore-signal').touch()
                control = self.start(root, port, 'control', action, mode)
                if mode == 'before-wait':
                    wait_until(lambda: (root / 'control.published').exists(), 'Publication did not precede wait return')
                    (root / 'release-wait').touch()
                elif mode in {'after-wait', 'after-timeout'}:
                    wait_until(lambda: (root / 'starter.completion-read').exists() and (root / 'control.publish-entered').exists(),
                               'Child wait and deferred publication did not meet')
                    require(starter.poll() is None, 'Starter did not allow the completion publication race')
                    if mode == 'after-timeout':
                        self.finish(starter, root, 'starter', 1)
                    (root / 'release-publish').touch()
                elif mode == 'post-replace-fsync-failure':
                    wait_until(lambda: (root / 'control.fsync-entered').exists() and (root / 'starter.waited').exists(),
                               'Post-replace directory fsync and original child wait did not meet')
                    require((root / '.state/service-shutdown/contrastive.json').exists()
                            and not self.consumable(root, first)
                            and starter.poll() is None and control.poll() is None,
                            'Concurrent reader consumed completion before publication durability settled')
                    verifications['concurrent_reader_rejected_visible_uncommitted_ack'] = True
                    (root / 'release-fsync').touch()
                elif mode == 'cancel-publication':
                    wait_until(lambda: (root / 'control.publish-entered').exists(), 'Cancellation publication gate not entered')
                    os.kill(control.pid, signal.SIGINT)
                    wait_until(lambda: (root / 'control.cancel-requested').exists(), 'Public Ctrl+C cancellation was not observed')
                    require(control.poll() is None and not (root / 'control.perform-settled').exists()
                            and not (root / 'control.published').exists(),
                            'Cancellation escaped while the publication worker was outstanding')
                    verifications['cancellation_deferred_with_worker_outstanding'] = True
                    (root / 'release-publish').touch()
                invalid = mode in {'malformed', 'deep-malformed', 'incomplete', 'empty', 'stale', 'wrong-launch',
                                   'wrong-pid', 'wrong-fingerprint', 'wrong-backend', 'wrong-origin', 'publish-failed', 'after-timeout', 'post-replace-fsync-failure', 'post-replace-open-failure'}
                failed = mode in {'dispatch-lookup', 'dispatch-denied', 'stop-timeout'}
                if mode == 'exec-alive':
                    self.finish(control, root, 'control', 1)
                    from ai_lab.decision_processes import process_fingerprint
                    current = process_fingerprint(first['pid'])
                    require(current and current != first['fingerprint'] and marker in current
                            and current.split(None, 6)[:6] == first['fingerprint'].split(None, 6)[:6],
                            'Owned child did not exec under its original PID and process group')
                    require(starter.poll() is None and not (root / 'control.publish-entered').exists()
                            and not self.consumable(root, first),
                            'Stop acknowledged a live process after its fingerprint changed')
                    verifications.update(same_pid_exec_still_alive_after_stop=True,
                                         original_foreground_still_waiting=True,
                                         live_exec_ack_consumable=False)
                    os.killpg(first['pid'], signal.SIGKILL)  # Only the exact test-owned exec marker above.
                    data = self.finish(starter, root, 'starter', 1)
                    require(data['wait_codes'][0] == -signal.SIGKILL, 'Original foreground did not reap its exec child')
                elif mode == 'inspection-failed':
                    data = self.finish(control, root, 'control', 1)
                    from ai_lab.decision_processes import process_fingerprint
                    require(data.get('inspection_failed_after_dispatch')
                            and process_fingerprint(first['pid']) == first['fingerprint']
                            and listening(port) and starter.poll() is None
                            and not (root / 'control.publish-entered').exists()
                            and not self.consumable(root, first),
                            'Inspection failure acknowledged or stopped a still-live owned child')
                    verifications.update(inspection_failed_only_after_signal_dispatch=True,
                                         original_identity_and_listener_still_live=True,
                                         inspection_failure_ack_consumable=False)
                    os.killpg(first['pid'], signal.SIGKILL)  # Parent verified the exact original identity above.
                    data = self.finish(starter, root, 'starter', 1)
                    require(data['wait_codes'][0] == -signal.SIGKILL, 'Original foreground did not reap inspected child')
                elif mode == 'cancel-publication':
                    data = self.finish(control, root, 'control', 130)
                    require(data['cancellation_observed'] and data['cancel_settled_after_publication']
                            and not data['receipt_retained_after_cancel']
                            and not data['created_after_cancel'] and not data['pending_after_cancel']
                            and not data['operation_lock_after_cancel'],
                            'Cancellation surfaced before publication and owned cleanup completed')
                    self.finish(starter, root, 'starter', 0)
                    require(self.consumable(root, first), 'Completed cancellation cleanup lacked acknowledgement')
                    verifications['publication_and_cleanup_completed_before_cancellation_surfaced'] = True
                elif failed:
                    self.finish(control, root, 'control', 1)
                    require(not (root / 'control.publish-entered').exists(), 'Failed/absent signal published acknowledgement')
                    require(starter.poll() is None and listening(port), 'Failed stop killed the original owned service')
                    (root / 'ignore-signal').unlink(missing_ok=True)
                    os.killpg(first['pid'], signal.SIGTERM)
                    self.finish(starter, root, 'starter', 1)
                elif action == 'restart':
                    replacement = self.ready(control, root, 'control')
                    require(replacement['pid'] != first['pid'], 'Restart did not create a distinct child')
                    self.finish(starter, root, 'starter', 0)
                    from ai_lab.decision_processes import process_fingerprint
                    require(control.poll() is None and listening(port)
                            and process_fingerprint(replacement['pid']) == replacement['fingerprint']
                            and json.loads((root / '.state/decisions-mistral.json').read_text()) == replacement,
                            'Original foreground cleanup disturbed the replacement')
                    stop = self.start(root, port, 'replacement-stop', 'stop')
                    self.finish(stop, root, 'replacement-stop', 0)
                    self.finish(control, root, 'control', 0)
                else:
                    data = self.finish(control, root, 'control', 1 if mode in {'publish-failed', 'post-replace-fsync-failure', 'post-replace-open-failure'} else 0)
                    if mode == 'exit-between-probes':
                        require(data.get('present_then_absent_before_fingerprint'),
                                'Real exit did not occur between the existence and fingerprint probes')
                        verifications['exit_between_existence_and_fingerprint_completed'] = True
                    if mode in {'post-replace-fsync-failure', 'post-replace-open-failure'}:
                        require(data.get('post_replace_fsync_failed' if mode == 'post-replace-fsync-failure' else 'post_replace_open_failed')
                                and not self.consumable(root, first),
                                'Failed post-replace publication left a consumable acknowledgement')
                        verifications['post_replace_failure_ack_consumable'] = False
                    if mode == 'deep-malformed':
                        require(data['malformed_ack_bytes'] <= 16384, 'Malformed fixture exceeded the bounded reader size')
                        verifications['deep_malformed_ack_bytes'] = data['malformed_ack_bytes']
                    self.finish(starter, root, 'starter', 1 if invalid else 0)
            wait_until(lambda: not listening(port), f'{name}: CPU socket leaked')
            from ai_lab.decision_processes import process_fingerprint
            require(process_fingerprint(first['pid']) is None, f'{name}: original child leaked')
            self.results.append({'case': name, 'status': 'PASS', 'port_released': True,
                                 'original_child_reaped': True, 'verifications': verifications,
                                 'cli_processes': {p.name.removesuffix('.report.json'): json.loads(p.read_text())
                                                   for p in root.glob('*.report.json')}})
        finally:
            self.cleanup(root)

    def history_case(self, fault):
        """A committed shutdown survives failed B publication and successful C."""
        from ai_lab.decision_processes import process_fingerprint
        name = 'prior-history-' + fault.removeprefix('post-replace-')
        root = self.root / name
        root.mkdir(parents=True)
        (root / 'serve').write_text(SERVER)
        with socket.socket() as reserve:
            reserve.bind(('127.0.0.1', 0))
            port = reserve.getsockname()[1]
        starter = self.start(root, port, 'starter', 'start', 'before-wait')
        try:
            first = self.ready(starter, root, 'starter')
            second_owner = self.start(root, port, 'second', 'restart', 'durability-starter')
            second = self.ready(second_owner, root, 'second')
            wait_until(lambda: (root / 'starter.waited').exists(), 'A foreground did not reach its real child-wait gate')
            require(first['pid'] != second['pid'] and starter.poll() is None
                    and self.consumable(root, first),
                    'Restart did not commit A shutdown before starting B')
            verifications = {'A_ack_before_B_failure': True, 'A_real_wait_gate_active': True}
            gate = 'fsync' if fault == 'post-replace-fsync-failure' else 'open'
            if gate == 'open':
                (root / 'gate-open').touch()
            stop_second = self.start(root, port, 'second-stop', 'stop', fault)
            wait_until(lambda: (root / ('second-stop.' + gate + '-entered')).exists()
                       and (root / 'second.waited').exists(),
                       'B did not reach its post-replace directory failure gate')
            import fcntl
            with (root / '.state/service-shutdown/contrastive.lock').open('rb') as lock:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    verifications['B_writer_exclusive_lock_observed'] = True
                else:
                    raise RuntimeError('B publication gate did not retain the exclusive writer lock')
            require(starter.poll() is None and self.consumable(root, first)
                    and not self.consumable(root, second),
                    'Concurrent B publication masked committed A or admitted uncommitted B')
            verifications.update(A_ack_during_B_exclusive_write=True, B_uncommitted_ack_consumable=False)
            (root / ('release-' + gate)).touch()
            stopped = self.finish(stop_second, root, 'second-stop', 1)
            require(stopped.get('publication_replaced') and stopped.get(
                    'post_replace_fsync_failed' if fault == 'post-replace-fsync-failure' else 'post_replace_open_failed'),
                    'B failure did not occur after replacing the actual history file')
            require(self.consumable(root, first) and not self.consumable(root, second),
                    'B publication failure masked committed A or admitted failed B')
            verifications.update(A_ack_after_B_failure=True, B_ack_after_failure=False)
            (root / 'release-wait').touch()
            self.finish(starter, root, 'starter', 0)
            self.finish(second_owner, root, 'second', 1)
            third_owner = self.start(root, port, 'third', 'start')
            third = self.ready(third_owner, root, 'third')
            require(third['pid'] not in {first['pid'], second['pid']}
                    and self.consumable(root, first) and not self.consumable(root, second),
                    'Starting C changed previously committed or failed shutdown status')
            stop_third = self.start(root, port, 'third-stop', 'stop')
            self.finish(stop_third, root, 'third-stop', 0)
            self.finish(third_owner, root, 'third', 0)
            require(self.consumable(root, first) and not self.consumable(root, second)
                    and self.consumable(root, third),
                    'Recovery publication lost committed A or promoted failed B')
            verifications.update(A_ack_after_C_recovery=True, B_ack_after_C_recovery=False,
                                 C_ack_after_recovery=True)
            wait_until(lambda: not listening(port), f'{name}: CPU socket leaked')
            require(all(process_fingerprint(state['pid']) is None for state in (first, second, third)),
                    f'{name}: an owned CPU child was not reaped')
            self.results.append({'case': name, 'status': 'PASS', 'port_released': True,
                                 'original_child_reaped': True, 'all_three_children_reaped': True,
                                 'verifications': verifications,
                                 'cli_processes': {p.name.removesuffix('.report.json'): json.loads(p.read_text())
                                                   for p in root.glob('*.report.json')}})
        finally:
            (root / 'release-wait').touch()
            (root / 'release-fsync').touch()
            (root / 'release-open').touch()
            self.cleanup(root)

    def history_prepare_case(self):
        """A foreground completes while B has not yet published its backup."""
        from ai_lab.decision_processes import process_fingerprint
        name = 'prior-history-backup-prepare'
        root = self.root / name
        root.mkdir(parents=True)
        (root / 'serve').write_text(SERVER)
        with socket.socket() as reserve:
            reserve.bind(('127.0.0.1', 0))
            port = reserve.getsockname()[1]
        starter = self.start(root, port, 'starter', 'start', 'before-wait')
        try:
            first = self.ready(starter, root, 'starter')
            second_owner = self.start(root, port, 'second', 'restart', 'durability-starter')
            second = self.ready(second_owner, root, 'second')
            wait_until(lambda: (root / 'starter.waited').exists(), 'A did not reach its real wait gate')
            require(starter.poll() is None and self.consumable(root, first),
                    'A was not committed before starting B backup preparation')
            stop_second = self.start(root, port, 'second-stop', 'stop', 'backup-prepare-gate')
            wait_until(lambda: (root / 'second-stop.prepare-entered').exists()
                       and (root / 'second.waited').exists(),
                       'B did not reach its first staged backup fsync gate')
            require(self.consumable(root, first) and not self.consumable(root, second)
                    and stop_second.poll() is None,
                    'Preparing B backup blocked committed A or admitted uncommitted B')
            (root / 'release-wait').touch()
            self.finish(starter, root, 'starter', 0)
            current = json.loads((root / 'second-stop.report.json').read_text())
            require(stop_second.poll() is None and current['backup_prepare_entered']
                    and not current.get('backup_prepare_released')
                    and not (root / 'second-stop.published').exists(),
                    'A did not complete while B remained gated before backup publication')
            verifications = {'A_ack_during_B_backup_prepare': True,
                             'B_ack_before_backup_publication': False,
                             'A_foreground_succeeded_before_B_prepare_release': True,
                             'fixture': 'B first staged-file fsync delayed; real fsync executes after release'}
            (root / 'release-prepare').touch()
            stopped = self.finish(stop_second, root, 'second-stop', 0)
            self.finish(second_owner, root, 'second', 0)
            require(stopped.get('backup_prepare_released') and self.consumable(root, first)
                    and self.consumable(root, second),
                    'Releasing B backup preparation did not commit the completed shutdown')
            third_owner = self.start(root, port, 'third', 'start')
            third = self.ready(third_owner, root, 'third')
            require(len({first['pid'], second['pid'], third['pid']}) == 3,
                    'A/B/C preparation case did not retain distinct child launches')
            stop_third = self.start(root, port, 'third-stop', 'stop')
            self.finish(stop_third, root, 'third-stop', 0)
            self.finish(third_owner, root, 'third', 0)
            require(all(self.consumable(root, state) for state in (first, second, third)),
                    'Later C publication discarded A or B after backup preparation')
            wait_until(lambda: not listening(port), f'{name}: CPU socket leaked')
            require(all(process_fingerprint(state['pid']) is None for state in (first, second, third)),
                    f'{name}: an owned CPU child was not reaped')
            verifications.update(A_ack_after_C=True, B_ack_after_C=True, C_ack_after_C=True)
            self.results.append({'case': name, 'status': 'PASS', 'port_released': True,
                                 'original_child_reaped': True, 'all_three_children_reaped': True,
                                 'verifications': verifications,
                                 'cli_processes': {p.name.removesuffix('.report.json'): json.loads(p.read_text())
                                                   for p in root.glob('*.report.json')}})
        finally:
            (root / 'release-wait').touch()
            (root / 'release-prepare').touch()
            self.cleanup(root)

    @staticmethod
    def consumable(root, state):
        from ai_lab.service_manager import Identity, NativeServices
        return NativeServices(root)._completed_shutdown(
            'contrastive', Identity(state['pid'], state['fingerprint'], state))

    def run(self):
        for action in ('stop', 'restart', 'interrupt'):
            self.case('independent-' + action, action)
        self.case('unexpected-zero', crash='zero')
        self.case('unexpected-term', crash=signal.SIGTERM)
        self.case('unexpected-int', crash=signal.SIGINT)
        self.case('unexpected-kill', crash=signal.SIGKILL)
        for mode in ('before-wait', 'after-wait', 'after-timeout', 'malformed', 'incomplete', 'empty', 'stale',
                     'wrong-launch', 'wrong-pid', 'wrong-fingerprint', 'wrong-backend', 'wrong-origin',
                     'publish-failed', 'dispatch-lookup', 'dispatch-denied', 'stop-timeout'):
            self.case(mode, mode=mode)
        for mode in ('exec-alive', 'exit-between-probes', 'inspection-failed', 'post-replace-fsync-failure', 'post-replace-open-failure', 'cancel-publication', 'deep-malformed'):
            self.case(mode, mode=mode)
        self.case('foreground-ctrl-c', action='ctrl-c')
        for fault in ('post-replace-fsync-failure', 'post-replace-open-failure'):
            self.history_case(fault)
        self.history_prepare_case()
        return {'status': 'passed', 'scope': 'real public CLI and owned Python CPU loopback processes; fixture discovery/runtime only',
                'package': self.package, 'cases': self.results, 'native_processes': 0,
                'models': 0, 'downloads': 0, 'gpu': False, 'sdk_calls': 0,
                'shutdown_ack_seconds_fixture': .75, 'durability_race_ack_seconds_fixture': 2,
                'shutdown_ack_seconds_production': 2}


def check(evidence=None):
    with tempfile.TemporaryDirectory(prefix='ai-lab-foreground-cpu-') as temporary:
        proof = ForegroundProof(Path(temporary))
        result = None
        try:
            result = proof.run()
        finally:
            if evidence:
                evidence.mkdir(parents=True, exist_ok=True)
                import shutil
                destination = evidence / 'foreground-cpu'
                shutil.copytree(temporary, destination, dirs_exist_ok=True)
                if result is not None:
                    atomic(destination / 'result.json', result)
        return result


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--fixture-cli':
        raise SystemExit(fixture_cli(Path(sys.argv[2]), int(sys.argv[3]), *sys.argv[4:]))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, help='Preserve CPU fixture CLI outputs and process evidence')
    args = parser.parse_args()
    print(json.dumps(check(args.evidence), indent=2))

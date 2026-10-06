#!/usr/bin/env python3
"""CPU-only checker regressions derived from item 6 STAGE1 reviewer reproductions.

Requires already installed literal 0.1.13 and preview/final 0.1.14 entrypoints.
No installs, native generation, hosted calls or Homebrew transaction occur here.
Output/roots are retained for review. Default 40/35-second timeouts are real.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
from types import SimpleNamespace
from unittest.mock import patch


def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


c, u = load('check_cli'), load('check_upgrade')


def rejected(call, text):
    try:
        call()
    except RuntimeError as error:
        assert text in str(error), str(error)
        return str(error)
    raise AssertionError('Expected rejection: ' + text)


class Regression:
    def __init__(self, args):
        self.args = args
        self.base = Path(args.output_directory).resolve()
        self.base.mkdir(mode=0o700)  # Never overwrite an earlier run.
        self.records = []
        self.phases = []
        self.roots = []

    def passed(self, case, **evidence):
        self.records.append({'case': case, 'status': 'PASS', **evidence})
        print(case + ': PASS', flush=True)

    def phase(self, label, phase, root, state, expected=0):
        output = self.base / (label + '.json')
        argv = [sys.executable, str(Path(u.__file__).resolve()), '--phase', phase,
                '--root', str(root), '--state', str(state), '--output', str(output)]
        if phase == 'before':
            argv += ['--executable', self.args.old_executable, '--context', 'isolated-env']
        elif phase == 'after':
            argv += ['--executable', self.args.executable, '--source-sha', self.args.source_sha]
        run = subprocess.run(argv, cwd=self.base, env={'PATH': os.defpath, 'PYTHONDONTWRITEBYTECODE': '1'},
                             capture_output=True, timeout=150)
        u.create_file(self.base / (label + '.log'), run.stdout + run.stderr)
        self.phases.append({'command': argv, 'exit': run.returncode, 'output': str(output)})
        assert run.returncode == expected, label + ': unexpected phase exit; see private log'
        return json.loads(output.read_text())

    def before(self, label):
        root, state = self.base / label, self.base / (label + '-state.json')
        self.roots.append((root, state))
        report = self.phase(label + '-before', 'before', root, state)
        assert report['status'] == 'PASS'
        self.before_checks = len(report['checks'])
        return root, state, json.loads(state.read_text())

    def kill_owner(self, state):
        owner, sock = state['owner'], Path(state['socket_path'])
        assert u.process_identity(owner['pid']) == owner
        u.socket_owner(owner['pid'], sock)
        assert u.socket_record(sock) == state['socket_identity']
        os.kill(owner['pid'], signal.SIGKILL)
        deadline = time.monotonic() + 15
        while u.process_identity(owner['pid']) is not None and time.monotonic() < deadline:
            time.sleep(.1)
        assert u.process_identity(owner['pid']) is None and sock.exists()

    def cli_crash(self):
        scratch = self.base / 'cli'
        scratch.mkdir(mode=0o700)
        check = c.Check(SimpleNamespace(executable=self.args.executable), scratch)
        try:
            check.start_api()
            identity = check.api_identity
            original = check.api
            original.send_signal(signal.SIGKILL)
            original.wait(timeout=15)
            rejected(lambda: check.run(['models', 'list', '--json'], structured=True,
                                       case='FAULT.list-after-owned-exit'), 'Owned API exited')
            rejected(lambda: check.terminal(['models'], 'SAVED MODELS', b'\x11', 80, 24), 'Owned API exited')
            # Bypass only the parent preflight to cover death between preflight
            # and a real child request. The explicit endpoint still cannot start.
            check.process([self.args.executable, '--root', str(check.root), 'models', 'list', '--json'],
                          code=1, structured=True, case='FAULT.transport-after-owned-exit')
            assert u.process_identity(identity['pid']) is None
            assert not (check.root / '.state/ai-lab/server.log').exists()
            rejected(check.stop_api, 'Owned API did not exit cleanly')
            assert not check.socket.exists() and check.api is None
            self.passed('I6-S1-F1.owner-death-no-replacement', owner=identity,
                        checks=check.records, socket_removed=True)
        finally:
            if check.api is not None:
                check.stop_api()

    def stopped_api(self):
        scratch = self.base / 'stopped'
        scratch.mkdir(mode=0o700)
        check = c.Check(SimpleNamespace(executable=self.args.executable), scratch)
        try:
            check.start_api()
            identity = check.api_identity
            process = check.api
            check.signal_api(signal.SIGSTOP)
            real_signal = check.signal_api
            real_identity = c.owned.process_identity

            def substituted_final_identity(sig):
                if sig == signal.SIGKILL:
                    # Only the final ps observation is a fixture. The process
                    # is a real stopped API and must survive this refusal.
                    def observed(pid):
                        value = real_identity(pid)
                        return {**value, 'started': 'simulated reused PID'} if pid == process.pid else value
                    with patch.object(c.owned, 'process_identity', side_effect=observed):
                        return real_signal(sig)
                return real_signal(sig)

            with patch.object(check, 'signal_api', side_effect=substituted_final_identity):
                rejected(check.stop_api, 'changed process identity')
            refusal = check.records[-1]
            assert refusal['signals'] == ['SIGINT', 'SIGTERM']
            assert not refusal['cleanup_complete'] and not refusal['process_exited']
            assert check.api is process and check.api_log is not None
            assert u.process_identity(process.pid) == identity
            u.socket_owner(process.pid, check.socket)
            self.passed('R1.final-signal-identity-refusal', evidence_class='fixture final ps observation on real stopped API',
                        owner=identity, cleanup=refusal)
            rejected(check.stop_api, 'Owned API did not exit cleanly')
            cleanup = check.records[-1]
            assert cleanup['signals'] == ['SIGINT', 'SIGTERM', 'SIGKILL']
            assert [entry['seconds'] for entry in cleanup['timeouts']] == [10, 5]
            assert cleanup['exit'] == -signal.SIGKILL and cleanup['cleanup_complete']
            assert cleanup['process_exited'] and cleanup['socket_removed'] and cleanup['timed_out']
            assert check.api is None and not check.socket.exists() and u.process_identity(process.pid) is None
            self.passed('R1.stopped-owner-bounded-cleanup', owner=identity, cleanup=cleanup)
        finally:
            if check.api is not None:
                if check.api.poll() is None:
                    check.signal_api(signal.SIGKILL)
                    check.api.wait(timeout=5)
                rejected(check.stop_api, 'Owned API did not exit cleanly')
            u.create_file(self.base / 'stopped-api-records.json', (json.dumps(check.records, indent=2) + '\n').encode())

    def hung_ptys(self):
        scratch = self.base / 'pty'
        scratch.mkdir(mode=0o700)
        check = c.Check(SimpleNamespace(executable=self.args.executable), scratch)
        try:
            check.start_api()
            owner = check.api_identity
            fake = scratch / 'hung-child'
            pid_file = scratch / 'child.pid'
            marker = 'OWNED_HUNG_PTY_DIAGNOSTIC'
            u.create_file(fake, (f'#!{sys.executable}\nimport os,signal,time\nfrom pathlib import Path\n'
                                'signal.signal(signal.SIGTERM, signal.SIG_IGN)\n'
                                f'Path({str(pid_file)!r}).write_text(str(os.getpid()))\n'
                                f'print({marker!r} + " " + {check.secrets[0]!r}, flush=True)\n'
                                'time.sleep(120)\n').encode())
            fake.chmod(0o700)
            check.executable = str(fake)
            children = []
            real_popen = c.subprocess.Popen

            def tracked_popen(*args, **kwargs):
                process = real_popen(*args, **kwargs)
                # ps inspection and other subprocesses are not PTY children.
                if kwargs.get('start_new_session') and args[0][0] == str(fake):
                    children.append(process)
                return process

            for fail_cleanup in (False, True):
                try:
                    with patch.object(c.subprocess, 'Popen', side_effect=tracked_popen):
                        if fail_cleanup:
                            # Preserve diagnostics even when final termination
                            # raises. The harness subsequently kills its child.
                            with patch.object(c.os, 'killpg', side_effect=OSError('fixture final signal failure')):
                                rejected(lambda: check.terminal(['models'], marker, b'\x11', 80, 24), 'timed out after SIGTERM')
                        else:
                            rejected(lambda: check.terminal(['models'], marker, b'\x11', 80, 24), 'timed out after SIGTERM')
                    record = check.records[-1]
                    process = children[-1]
                    assert record['case'] == 'PTY.entrypoint-smoke' and record['owned_pid'] == process.pid
                    assert record['timed_out'] and record['marker_seen'] and record['keys_sent']
                    assert [entry['seconds'] for entry in record['timeouts']] == [18, 2, 5]
                    assert marker in record['transcript'] and check.secrets[0] not in json.dumps(record)
                    assert 'timed out after SIGTERM' in record['error']
                    if fail_cleanup:
                        assert record['cleanup_error'] == 'fixture final signal failure'
                        assert not record['process_exited'] and process.poll() is None
                        case = 'R2.pty-transcript-with-cleanup-failure'
                    else:
                        assert record['process_exited'] and record['exit'] == -signal.SIGKILL
                        assert record['signals'] == ['SIGTERM', 'SIGKILL'] and 'cleanup_error' not in record
                        assert u.process_identity(process.pid) is None
                        case = 'R2.hung-pty-timeout-transcript'
                    self.passed(case, evidence_class='real hung PTY; injected final signal failure' if fail_cleanup else 'real hung PTY',
                                owner=owner, pty=record)
                finally:
                    for process in children:
                        if process.poll() is None:
                            identity = u.process_identity(process.pid)
                            assert identity is not None and identity['uid'] == os.getuid() and identity['pgid'] == process.pid
                            assert identity['command'].endswith(' '.join(process.args))
                            process.kill()
                            process.wait(timeout=5)
                    assert all(u.process_identity(process.pid) is None for process in children)
        finally:
            check.executable = self.args.executable
            check.stop_api(via_cli=True)
            u.create_file(self.base / 'hung-pty-records.json', (json.dumps(check.records, indent=2) + '\n').encode())

    def readiness_timeout(self):
        scratch = self.base / 'readiness'
        scratch.mkdir(mode=0o700)
        check = c.Check(SimpleNamespace(executable=self.args.executable), scratch)
        real_run = c.subprocess.run
        pid_file = scratch / 'probe.pid'
        code = ('import os,time; from pathlib import Path; '
                f'Path({str(pid_file)!r}).write_text(str(os.getpid())); '
                f'print("OWNED_READINESS_DIAGNOSTIC " + {check.secrets[0]!r},flush=True); time.sleep(60)')

        def hung_status(command, **kwargs):
            if command[0] == self.args.executable and '--service-action' in command and 'status' in command:
                # Substitute only the probe transport with a real harmless
                # child; the foreground API remains the actual installed app.
                return real_run([sys.executable, '-c', code], **kwargs)
            return real_run(command, **kwargs)

        try:
            with patch.object(c.subprocess, 'run', side_effect=hung_status):
                rejected(check.start_api, 'readiness probe timed out')
            record = check.records[-1]
            assert record['case'] == 'CPL-09.readiness-probe' and record['timeout_seconds'] == 5
            assert record['timed_out'] and 'OWNED_READINESS_DIAGNOSTIC' in record['stdout']
            assert check.secrets[0] not in json.dumps(record)
            pid = int(pid_file.read_text())
            assert u.process_identity(pid) is None
            self.passed('R2.readiness-probe-timeout-diagnostic', evidence_class='real 5s child timeout substituted for status probe',
                        probe_pid=pid, check=record)
        finally:
            try:
                check.stop_api()
            except RuntimeError as error:
                assert 'did not exit cleanly' in str(error)
            assert check.api is None and not check.socket.exists()
            u.create_file(self.base / 'readiness-records.json', (json.dumps(check.records, indent=2) + '\n').encode())

    def positive_and_crash(self):
        root, path, state = self.before('positive')
        after = self.phase('positive-after', 'after', root, path)
        cleanup = self.phase('positive-cleanup', 'cleanup', root, path)
        assert after['after_verified'] and cleanup['cleanup']['socket_removed']
        assert after['owner'] == state['owner']
        self.passed('positive.before-after-cleanup', before_checks=self.before_checks,
                    after_checks=len(after['checks']), owner=state['owner'])

        root, path, state = self.before('crash')
        self.kill_owner(state)
        after = self.phase('crash-after', 'after', root, path, expected=1)
        assert after['error'] == 'Old API process identity changed or exited; never restart it to pass.'
        assert 'cleanup_error' not in after and after['cleanup']['stale_socket_removed']
        assert not Path(state['socket_path']).exists()
        self.phase('crash-cleanup', 'cleanup', root, path)
        self.passed('I6-S1-F2.original-stale-socket-recovered', error=after['error'], cleanup=after['cleanup'])

    def socket_guards(self):
        root, path, state = self.before('guards')
        self.kill_owner(state)
        sock = Path(state['socket_path'])
        # Preserve original inode while a separate owned fixture replaces it.
        parked = sock.with_name('original.sock')
        sock.rename(parked)
        replacement = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            replacement.bind(str(sock))
            replacement.listen()
            replacement_identity = u.socket_record(sock)
            after = self.phase('replaced-after', 'after', root, path, expected=1)
            assert after['error'] == 'Old API process identity changed or exited; never restart it to pass.'
            assert 'replaced socket' in after['cleanup_error']
            self.phase('replaced-cleanup', 'cleanup', root, path, expected=1)
            assert u.socket_record(sock) == replacement_identity
            self.passed('I6-S1-F4.primary-and-cleanup-errors', error=after['error'],
                        cleanup_error=after['cleanup_error'], replacement_untouched=True)
            # A same-inode live holder is also refused (owned socket fixture).
            rejected(lambda: u.remove_stale_socket(sock, replacement_identity, state['owner']), 'socket holder')
            self.passed('I6-S1-F2.live-holder-refused')
        finally:
            replacement.close()
            assert u.socket_record(sock) == replacement_identity
            sock.unlink()  # This regression owns the replacement, not the checker.
            parked.rename(sock)
        args = SimpleNamespace(root=str(root), state=str(path))
        upgrade = u.Upgrade(args, json.loads(path.read_text()))
        # PID reuse cannot reliably be forced; inject only the ps observation.
        changed = {**state['owner'], 'started': 'simulated reused PID'}
        with patch.object(u, 'process_identity', return_value=changed):
            rejected(upgrade.cleanup, 'changed/foreign PID identity')
        assert u.socket_record(sock) == state['socket_identity']
        self.passed('I6-S1-F2.reused-identity-refused', evidence_class='fixture ps observation')
        # Actual foreign-PID substitution must also fail its original receipt.
        child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(120)'], start_new_session=True,
                                 env={'PATH': os.defpath, 'PYTHONDONTWRITEBYTECODE': '1'})
        try:
            changed_state = {**state, 'owner': u.process_identity(child.pid)}
            u.write_json(path, changed_state)
            self.phase('foreign-pid-cleanup', 'cleanup', root, path, expected=1)
            assert child.poll() is None and u.socket_record(sock) == state['socket_identity']
            self.passed('I6-S1-F2.foreign-pid-refused', foreign_pid=child.pid)
        finally:
            child.terminate()
            child.wait(timeout=10)
            u.write_json(path, state)
        self.phase('guards-cleanup', 'cleanup', root, path)

    def timeouts(self):
        # Same harmless actual child/40-second timeout as reviewer reproduction;
        # exercise main as well so scratch/report retention is observable.
        report_path = self.base / 'cli-timeout.json'
        child_pid = self.base / 'cli-timeout.pid'
        sentinel = []

        def timeout_discovery(check):
            sentinel.append(check.secrets[0])
            code = ('import os,time,sys; from pathlib import Path; '
                    f'Path({str(child_pid)!r}).write_text(str(os.getpid())); '
                    f'print("owned-timeout-diagnostic " + {sentinel[0]!r},flush=True); '
                    'print("owned-stderr-diagnostic",file=sys.stderr,flush=True); time.sleep(60)')
            check.process([sys.executable, '-c', code], case='FAULT.cli-timeout')

        argv = ['check_cli.py', '--executable', self.args.executable, '--source-sha', self.args.source_sha,
                '--output', str(report_path)]
        with patch.object(c.Check, 'discovery', timeout_discovery), patch.object(sys, 'argv', argv):
            assert c.main() == 1
        report = json.loads(report_path.read_text())
        record = report['checks'][0]
        assert record['timed_out'] and record['timeout_seconds'] == 40 and record['seconds'] >= 40
        assert 'owned-timeout-diagnostic' in record['stdout'] and 'owned-stderr-diagnostic' in record['stderr']
        assert sentinel[0] not in report_path.read_text() and record['sentinel_leaked']
        assert report['scratch_retained'] and Path(report['scratch_path']).is_dir()
        assert u.process_identity(int(child_pid.read_text())) is None
        assert report_path.stat().st_mode & 0o777 == 0o600
        self.passed('I6-S1-F3.cli-timeout-diagnostics-retained', report=str(report_path), child_exited=True)

        # Upgrade.cli's real default timeout; a harmless executable accepts and
        # ignores the --root prefix. Its diagnostics include the synthetic key.
        root, state_path = self.roots[0]
        upgrade = u.Upgrade(SimpleNamespace(root=str(root), state=str(state_path)), u.read_state(state_path))
        fake = self.base / 'timeout-child'
        upgrade_pid = self.base / 'upgrade-timeout.pid'
        u.create_file(fake, (f'#!{sys.executable}\nimport os,time,sys\nfrom pathlib import Path\n'
                            f'Path({str(upgrade_pid)!r}).write_text(str(os.getpid()))\n'
                            'print("owned-upgrade-diagnostic " + "11" * 32,flush=True)\n'
                            'print("owned-upgrade-stderr",file=sys.stderr,flush=True)\ntime.sleep(60)\n').encode())
        fake.chmod(0o700)
        rejected(lambda: upgrade.cli(fake, [], 'FAULT.upgrade-timeout'), 'CLI timed out')
        record = upgrade.records[-1]
        diagnostic = Path(record['diagnostic_path'])
        assert record['timed_out'] and record['timeout_seconds'] == 35 and record['seconds'] >= 35
        payload = diagnostic.read_text()
        assert 'owned-upgrade-diagnostic' in payload and 'owned-upgrade-stderr' in payload
        assert '11' * 32 not in payload and diagnostic.stat().st_mode & 0o777 == 0o600
        assert u.process_identity(int(upgrade_pid.read_text())) is None
        self.passed('I6-S1-F3.upgrade-timeout-diagnostics-retained', check=record, child_exited=True)

    def run(self):
        report = {'status': 'FAIL', 'context': 'isolated-env', 'full_release_pass': False,
                  'native_inference': False, 'source_sha_supplied': self.args.source_sha,
                  'checker_hashes': {Path(m.__file__).name: u.digest(Path(m.__file__).read_bytes()) for m in (c, u)}}
        try:
            self.cli_crash()
            self.stopped_api()
            self.hung_ptys()
            self.readiness_timeout()
            self.positive_and_crash()
            self.socket_guards()
            self.timeouts()
            report['status'] = 'PASS'
        finally:
            # Failure cleanup uses the original ownership receipts. Never remove
            # directories or foreign paths to make a failed regression pass.
            cleanup_errors = []
            for index, (root, state) in enumerate(self.roots):
                if state.exists():
                    try:
                        self.phase(f'finally-{index}', 'cleanup', root, state)
                    except Exception as error:
                        cleanup_errors.append(type(error).__name__)
            if cleanup_errors:
                report.update(status='FAIL', cleanup_errors=cleanup_errors)
            report.update(checks=self.records, phases=self.phases)
            u.create_file(self.base / 'regressions.json', (json.dumps(report, indent=2) + '\n').encode())
        assert report['status'] == 'PASS'
        print(json.dumps({'status': report['status'], 'checks': len(self.records), 'full_release_pass': False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--old-executable', required=True)
    parser.add_argument('--executable', required=True)
    parser.add_argument('--source-sha', required=True)
    parser.add_argument('--output-directory', required=True)
    args = parser.parse_args()
    os.umask(0o077)
    Regression(args).run()


if __name__ == '__main__':
    main()

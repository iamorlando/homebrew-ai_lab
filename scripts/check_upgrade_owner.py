#!/usr/bin/env python3
"""Owned CPU regressions for early/ready upgrade identity and private diagnostics.

Use an already installed literal13 Framework venv and installed14 executable.
No installation, native generation, model/SDK calls or Homebrew transaction.
"""
import argparse
import contextlib
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('upgrade_owner_subject', Path(__file__).with_name('check_upgrade.py'))
u = importlib.util.module_from_spec(spec)
spec.loader.exec_module(u)


def reject(call, text):
    try:
        call()
    except Exception as error:
        assert text in str(error), type(error).__name__
        return
    raise AssertionError('Expected guard rejection')


class Checks:
    def __init__(self, args):
        self.args = args
        self.base = Path(args.output_directory).resolve()
        self.base.mkdir(mode=0o700)
        self.records, self.pids, self.outcomes = [], [], []

    def passed(self, case, **data):
        self.records.append({'case': case, 'status': 'PASS', **data})
        print(case + ': PASS', flush=True)

    def fresh(self, name):
        root = self.base / name
        root.mkdir(mode=0o700)
        state_path = self.base / (name + '-state.json')
        state = {'format': u.FORMAT, 'phase': 'preparing', 'uid': os.getuid(), 'root': str(root),
                 'state_path': str(state_path), 'root_identity': u.directory(root), 'nonce': name,
                 'context': 'isolated-env', 'socket_path': str(root / '.state/ai-lab/api.sock')}
        u.create_file(root / u.MARKER, json.dumps({k: state[k] for k in ('format', 'uid', 'root', 'state_path', 'nonce')}).encode())
        u.write_json(state_path, state)
        u.create_file(state_path.with_name(state_path.name + '.lock'), b'')
        return u.Upgrade(SimpleNamespace(root=str(root), state=str(state_path), phase='before'), state)

    def synthetic(self):
        for field in ('pid', 'uid', 'pgid', 'started', 'command', 'absent', 'inspection'):
            check = self.fresh('synthetic-' + field)
            saved = {'pid': 123456, 'uid': os.getuid(), 'pgid': 123456,
                     'started': 'Tue Oct 6 19:56:39 2026', 'command': '/owned/python /owned/ai-lab --root /owned completion --service-action run'}
            check.state.update(owner=saved, server_argv=['/owned/ai-lab', '--root', '/owned', 'completion', '--service-action', 'run'],
                               socket_identity={'dev': 1, 'ino': 1, 'uid': os.getuid()})
            u.create_file(check.root / '.upgrade-checker/process-owner.json', json.dumps({
                'nonce': check.state['nonce'], 'owner': saved, 'server_argv': check.state['server_argv'],
                'root': str(check.root), 'state_path': str(check.state_path)}).encode())
            u.create_file(check.root / '.upgrade-checker/socket-owner.json', json.dumps({
                'nonce': check.state['nonce'], 'pid': saved['pid'], 'socket_identity': check.state['socket_identity']}).encode())
            observed = copy.deepcopy(saved)
            if field in ('pid', 'uid', 'pgid'): observed[field] += 1
            elif field == 'started': observed[field] = 'Tue Oct 6 19:57:39 2026'
            elif field == 'command': observed[field] = '/foreign/SECRET-SENTINEL ' + ' '.join(check.state['server_argv'])
            elif field == 'absent': observed = None
            if field == 'inspection':
                observation = patch.object(u, 'process_identity', side_effect=OSError('SECRET-SENTINEL'))
            else:
                observation = patch.object(u, 'process_identity', return_value=observed)
            with observation as probe, patch.object(u.os, 'kill') as kill, patch.object(u, 'api_request') as api:
                reject(check.owner, 'SECRET-SENTINEL' if field == 'inspection' else 'Old API process identity')
                assert probe.call_count == 1, 'diagnostic must reuse original observation, never reread'
                first = copy.deepcopy(check.owner_diagnostics['events'][0])
                assert first['moment'] == 'primary_before_cleanup' and first['observation'] == 'at_failure'
                assert first['expected'] == saved and first['observed'] == (None if field == 'inspection' else observed)
                assert first['process_status'] == ('INSPECTION_ERROR' if field == 'inspection' else 'ABSENT' if field == 'absent' else 'PRESENT')
                if field not in ('absent', 'inspection'):
                    reject(check.cleanup, 'Cleanup refuses changed/foreign')
                    assert check.owner_diagnostics['events'][1]['moment'] == 'internal_cleanup'
                    check.phase = 'cleanup'
                    reject(check.cleanup, 'Cleanup refuses changed/foreign')
                    assert check.owner_diagnostics['events'][2]['moment'] == 'explicit_cleanup'
                kill.assert_not_called();api.assert_not_called()
                assert check.owner_diagnostics['events'][0] == first
            self.passed('diagnostic-' + field, events=check.owner_diagnostics)

        check = self.fresh('write-error')
        check.state.update(owner=saved, server_argv=['/owned/ai-lab'])
        with patch.object(check, 'save', side_effect=PermissionError('SECRET-SENTINEL')):
            check.owner_evidence('primary_before_cleanup', None, inspection='ABSENT')
        assert check.owner_diagnostics['capture_error'] == 'PERSISTENCE_ERROR'
        assert len(check.owner_diagnostics['events']) == 1
        assert 'SECRET-SENTINEL' not in json.dumps(check.owner_diagnostics)
        self.passed('diagnostic-write-error-secondary')
        first = copy.deepcopy(check.owner_diagnostics['events'][0])
        check.owner_evidence('primary_before_cleanup', saved)
        assert check.owner_diagnostics['events'][0] == first
        self.passed('diagnostic-first-event-preserved')
        too_big = {**saved, 'command': 'SECRET-SENTINEL' * 10000}
        check.owner_evidence('internal_cleanup', too_big)
        assert check.owner_diagnostics['capture_error'] == 'CAPTURE_ERROR' and len(check.owner_diagnostics['events']) == 1
        self.passed('diagnostic-envelope-bound')

        for primary_failure in (False, True):
            name = 'output-failure-' + str(primary_failure)
            root, state, output = self.base / name, self.base / (name + '.state.json'), self.base / (name + '.json')
            argv = ['check_upgrade', '--phase', 'before', '--executable', self.args.old_executable,
                    '--root', str(root), '--state', str(state), '--output', str(output), '--context', 'isolated-env']
            real_create = u.create_file
            def write(path, data):
                if path == output:raise PermissionError('SECRET-SENTINEL')
                return real_create(path, data)
            captured = io.StringIO()
            with patch.object(sys, 'argv', argv), patch.object(u, 'create_file', side_effect=write), \
                    patch.object(u.Upgrade, 'before', side_effect=RuntimeError('PRIMARY_TEST_FAILURE') if primary_failure else None), \
                    contextlib.redirect_stdout(captured):
                assert u.main() == 1
            report = json.loads(captured.getvalue())
            assert report['output_error'] == 'WRITE_ERROR' and report['status'] == 'FAIL'
            assert ('PRIMARY_TEST_FAILURE' in report['error']) is primary_failure
            assert 'SECRET-SENTINEL' not in captured.getvalue()
            self.passed(name, console=report)

    def phase(self, name, phase, root, state):
        report = self.base / (name + '.json')
        argv = [sys.executable, u.__file__, '--phase', phase, '--root', str(root), '--state', str(state), '--output', str(report)]
        if phase == 'before':argv += ['--executable', self.args.old_executable, '--context', 'isolated-env']
        if phase == 'after':argv += ['--executable', self.args.executable, '--source-sha', self.args.source_sha]
        run = subprocess.run(argv, cwd=self.base, capture_output=True, timeout=180)
        u.create_file(self.base / (name + '.log'), run.stdout + run.stderr)
        assert run.returncode == 0, 'see retained phase log'
        return json.loads(report.read_text()), argv

    def positive(self, name='positive'):
        root, state_path = self.base / name, self.base / (name + '-state.json')
        primary_error = cleanup_error = output_error = None
        stage = 'before'
        try:
            before, before_command = self.phase(name + '-before', 'before', root, state_path)
            stage = 'state_read'
            state = u.read_state(state_path)
            self.pids.append(state['owner']['pid'])
            stage = 'ready_guards'
            assert state['ready_owner_bound'] is True
            assert any('Python.framework/' in path and '/Python.app/' in path
                       for path in state['interpreter_binding']['command_interpreters']), 'Requires retained Framework Python'
            early = json.loads((root / '.upgrade-checker/process-owner.json').read_text())
            assert early['owner'] == state['startup_owner']
            assert u.startup_identity_matches(state['startup_owner'], state['owner'], state['server_argv'], state['interpreter_binding'])
            for field, value, message in (
                    ('ready_owner_bound', False, 'Ready binding phase'),
                    ('ready_owner_bound', 'true', 'Ready binding phase'),
                    ('owner', {**state['owner'], 'started': 'substituted'}, 'Ready receipt')):
                modified = copy.deepcopy(state)
                modified[field] = value
                guard = u.Upgrade(SimpleNamespace(root=str(root), state=str(state_path), phase='after'), modified)
                with patch.object(u, 'process_identity') as probe, patch.object(u.os, 'kill') as kill:
                    reject(guard.cleanup, message)
                    probe.assert_not_called()
                    kill.assert_not_called()
                self.passed('ready-receipt-' + field + '-' + str(value if field != 'owner' else 'substituted'))
            # Even another *bound* prefix is no longer interchangeable after readiness.
            check = u.Upgrade(SimpleNamespace(root=str(root), state=str(state_path), phase='after'), state)
            changed = {**state['owner'], 'command': next(path + ' ' + ' '.join(state['server_argv'])
                       for path in state['interpreter_binding']['command_interpreters']
                       if path + ' ' + ' '.join(state['server_argv']) != state['owner']['command'])}
            with patch.object(u, 'process_identity', return_value=changed), patch.object(u.os, 'kill') as kill, patch.object(u, 'api_request') as api:
                reject(check.owner, 'Old API process identity')
                reject(check.cleanup, 'Cleanup refuses changed/foreign')
                kill.assert_not_called();api.assert_not_called()
            self.passed('strict-ready-command-even-bound-prefix', events=check.owner_diagnostics)
            # Keep this injected negative separate from actual successful phase input.
            state.pop('owner_diagnostics', None)
            u.write_json(state_path, state)
            stage = 'after'
            after, after_command = self.phase(name + '-after', 'after', root, state_path)
            assert before['status'] == after['status'] == 'PASS' and after['after_verified']
            self.passed('actual-framework-before-after', before_checks=len(before['checks']), after_checks=len(after['checks']),
                        startup_owner=state['startup_owner'], ready_owner=state['owner'],
                        transition_observed=state['startup_owner']['command'] != state['owner']['command'],
                        commands=[before_command, after_command])
        except (Exception, KeyboardInterrupt) as error:
            primary_error = error
            raise
        finally:
            # BEFORE can leave a live owner even when its final report cannot
            # be written/read. Always invoke receipt-guarded cleanup using the
            # original paths, including BEFORE/state-read failure paths.
            try:
                cleanup, command = self.phase(name + '-cleanup', 'cleanup', root, state_path)
                assert cleanup['cleanup']['process_exited'] and cleanup['cleanup']['socket_removed']
                self.pids.append(cleanup['cleanup']['pid'])
                if primary_error is None:
                    self.passed('actual-framework-explicit-cleanup', command=command)
            except (Exception, KeyboardInterrupt) as error:
                cleanup_error = error
            outcome = {'case': name, 'status': 'FAIL' if primary_error or cleanup_error else 'PASS',
                       'primary_error': {'type': type(primary_error).__name__, 'stage': stage} if primary_error else None,
                       'cleanup_error': {'type': type(cleanup_error).__name__} if cleanup_error else None}
            self.outcomes.append(outcome)
            try:
                u.create_file(self.base / (name + '-outcome.json'), (json.dumps(outcome, indent=2) + '\n').encode())
            except Exception as error:
                output_error = error
                outcome.update(status='FAIL', output_error='WRITE_ERROR')
            # Cleanup/report errors never replace the original failed proof.
            if primary_error is None:
                if cleanup_error is not None:
                    raise cleanup_error
                if output_error is not None:
                    raise output_error

    def positive_failure_cleanup(self):
        for fail_cleanup_report in (False, True):
            name = 'read-cleanerr' if fail_cleanup_report else 'read-fault'
            original_phase = self.phase
            original_read = u.read_state
            def failed_state_read(path):
                state = original_read(path)
                assert u.process_identity(state['owner']['pid']) == state['owner']
                u.socket_owner(state['owner']['pid'], Path(state['socket_path']))
                self.pids.append(state['owner']['pid'])
                raise OSError('PRIVATE_STATE_READ_SENTINEL')
            def phase(label, phase_name, root, state):
                result = original_phase(label, phase_name, root, state)
                if phase_name == 'cleanup' and fail_cleanup_report:
                    raise RuntimeError('Injected error after actual receipt-safe cleanup')
                return result
            # Only the parent harness state read is injected. BEFORE and
            # CLEANUP run the actual checker/public old API in subprocesses.
            with patch.object(u, 'read_state', side_effect=failed_state_read), \
                    patch.object(self, 'phase', side_effect=phase):
                reject(lambda: self.positive(name), 'PRIVATE_STATE_READ_SENTINEL')
            outcome = self.outcomes[-1]
            assert outcome['primary_error'] == {'type': 'OSError', 'stage': 'state_read'}
            assert outcome['cleanup_error'] == ({'type': 'RuntimeError'} if fail_cleanup_report else None)
            state = u.read_state(self.base / (name + '-state.json'))
            self.pids.append(state['owner']['pid'])
            assert state['cleanup']['process_exited'] and state['cleanup']['socket_removed']
            assert u.process_identity(state['owner']['pid']) is None
            assert not Path(state['socket_path']).exists()
            assert 'PRIVATE_STATE_READ_SENTINEL' not in json.dumps(outcome)
            self.passed('actual-before-state-read-failure-' + ('secondary-error' if fail_cleanup_report else 'cleanup'),
                        evidence_class='real BEFORE/CLEANUP; injected parent state-read failure' +
                        (' and injected error after real cleanup' if fail_cleanup_report else ''), outcome=outcome)

    def early(self, fault):
        check = self.fresh('early-' + fault)
        real_identity, real_api = u.process_identity, u.api_request
        observations = []
        def record_identity(pid):
            value = real_identity(pid)
            observations.append({'elapsed_seconds': round(time.monotonic() - check.diagnostic_started, 6),
                                 'identity': value})
            return value
        def observe(pid):
            value = record_identity(pid)
            if value is not None and check.state.get('owner'):
                if fault == 'crash':
                    assert check.child.pid == pid and check.child.poll() is None
                    check.child.kill();check.child.wait(timeout=5)
                    return None
                if fault in ('uid', 'started', 'argv'):
                    value = copy.deepcopy(value)
                    if fault == 'uid':value['uid'] += 1
                    elif fault == 'started':value['started'] = 'Tue Oct 6 00:00:00 1999'
                    else:value['command'] += ' --foreign-argument'
            return value
        def api(path, method, route, body=None):
            if fault == 'timeout' and method == 'GET':return 503, b'{}'
            return real_api(path, method, route, body)
        try:
            with patch.object(u, 'process_identity', side_effect=observe), patch.object(u, 'api_request', side_effect=api):
                reject(lambda: check.start_old(Path(self.args.old_executable)), 'failed to start' if fault == 'timeout' else 'startup identity')
                assert check.state['startup_owner'] == check.state['owner'] and not check.state['ready_owner_bound']
                first = check.owner_diagnostics['events'][0]
                assert first['moment'] == 'primary_before_cleanup' and first['observation'] == 'at_failure'
                assert first['reason'] == ('READINESS_TIMEOUT' if fault == 'timeout' else
                                           'PROCESS_ABSENT' if fault == 'crash' else 'IDENTITY_MISMATCH')
                self.pids.append(check.child.pid)
                if fault in ('uid', 'started', 'argv'):
                    with patch.object(u.os, 'kill') as kill:
                        reject(check.cleanup, 'Cleanup refuses changed/foreign')
                        kill.assert_not_called()
        finally:
            try:
                with patch.object(u, 'process_identity', side_effect=record_identity):
                    check.cleanup()
                if check.child is not None:
                    check.child.wait(timeout=5)
                assert not check.socket.exists()
                assert u.process_identity(check.state['owner']['pid']) is None
            finally:
                u.create_file(self.base / ('early-' + fault + '-result.json'), json.dumps({
                    'cleanup': check.state.get('cleanup'), 'owner_diagnostics': check.owner_diagnostics,
                    'private_observations': observations}, indent=2).encode())
        self.passed('actual-framework-early-' + fault, owner=check.state['startup_owner'],
                    diagnostics=copy.deepcopy(check.owner_diagnostics))

    def publication_failures(self):
        for index, fault in enumerate(('ready-write', 'socket-write', 'journal-write', 'link-write',
                                       'state-before', 'state-after', 'deferred', 'foreign')):
            check = self.fresh('pub-' + str(index))  # Preserve the <=62-byte output-root contract.
            assert check.cli(Path(self.args.old_executable), ['--version'], 'old.version',
                             structured=False) == 'AI Lab 0.1.13'
            check.save()
            real_create, real_write, real_link = u.create_file, u.write_json, u.os.link
            injected, foreign = [], []
            folder = check.root / '.upgrade-checker'

            def fail():
                injected.append(fault)
                raise OSError('PRIVATE_PUBLICATION_SENTINEL')

            def create(path, data):
                real_create(path, data)
                if path.name == ('ready-owner.json' if fault == 'ready-write' else
                                 'socket-owner.json' if fault == 'socket-write' else ''):
                    fail()

            def write(path, value):
                commit = path == check.state_path and value.get('ready_owner_bound') is True
                if fault == 'state-before' and commit:
                    fail()
                real_write(path, value)
                if (fault == 'state-after' and commit
                        or fault == 'journal-write' and path.name == 'ready-publication.json'):
                    fail()

            def link(source, destination):
                real_link(source, destination)
                if destination.name == 'ready-owner.json' and fault in ('link-write', 'deferred', 'foreign'):
                    if fault == 'foreign':
                        # The harness replaces only its freshly created alias;
                        # the checker must refuse this different owned fixture.
                        assert source.stat().st_ino == destination.stat().st_ino
                        destination.unlink()
                        real_create(destination, b'FOREIGN_RECEIPT_FIXTURE\n')
                        foreign.append((source, destination, u.file_record(destination)))
                    fail()

            try:
                with patch.object(u, 'create_file', side_effect=create), \
                        patch.object(u, 'write_json', side_effect=write), \
                        patch.object(u.os, 'link', side_effect=link), contextlib.ExitStack() as stack:
                    if fault == 'deferred':
                        stack.enter_context(patch.object(check, 'recover_ready_publication',
                                            side_effect=RuntimeError('Injected deferred recovery')))
                    reject(lambda: check.start_old(Path(self.args.old_executable)), 'PRIVATE_PUBLICATION_SENTINEL')
                assert injected == [fault], 'publication errors must not be swallowed/retried as health failures'
                self.pids.append(check.child.pid)
                observed = u.process_identity(check.child.pid)
                assert u.startup_identity_matches(check.state['startup_owner'], observed,
                                                  check.state['server_argv'], check.state['interpreter_binding'])
                u.socket_owner(check.child.pid, check.socket)
                failure = check.records[-1]
                assert failure['case'] == 'before.ready-publication' and failure['error'] == 'OSError'
                assert ('cleanup_error' in failure) is (fault in ('deferred', 'foreign'))
                if foreign:
                    source, destination, record = foreign[0]
                    guarded = u.Upgrade(SimpleNamespace(root=str(check.root), state=str(check.state_path), phase='cleanup'),
                                        u.read_state(check.state_path))
                    with patch.object(u.os, 'kill') as kill, patch.object(u, 'api_request') as api:
                        reject(guarded.cleanup, 'unverified or replaced receipt')
                        kill.assert_not_called()
                        api.assert_not_called()
                    assert u.file_record(destination) == record
                if fault not in ('deferred', 'foreign'):
                    check.cleanup()  # Real internal cleanup with the original child handle.
            finally:
                # Restore only the harness-created foreign fixture, never an
                # unverified path, before the unmodified explicit cleanup path.
                for source, destination, record in foreign:
                    assert u.file_record(destination) == record
                    destination.unlink()
                    real_link(source, destination)
                if check.state_path.exists():
                    cleanup, command = self.phase('pub-' + fault + '-cleanup', 'cleanup', check.root, check.state_path)
                    assert cleanup['cleanup']['process_exited'] and cleanup['cleanup']['socket_removed']
                if check.child is not None:
                    check.child.wait(timeout=5)
                    assert check.child.returncode == 0
                    self.pids.append(check.child.pid)
                    assert u.process_identity(check.child.pid) is None
                assert not check.socket.exists()
            assert not (folder / 'ready-publication.json').exists()
            self.passed('actual-publication-' + fault, failure=failure, command=command,
                        evidence_class='real published13 CPU API; private filesystem fault only',
                        foreign_receipt_untouched=(fault == 'foreign'))

    def run(self):
        status = 'FAIL'
        try:
            self.synthetic()
            self.positive()
            self.positive_failure_cleanup()
            self.publication_failures()
            for fault in ('timeout', 'crash', 'uid', 'started', 'argv'):self.early(fault)
            assert all(u.process_identity(pid) is None for pid in self.pids)
            status = 'PASS'
        finally:
            u.create_file(self.base / 'results.json', json.dumps({'status': status, 'checks': self.records,
                'positive_outcomes': self.outcomes,
                'checker_sha256': u.digest(Path(u.__file__).read_bytes()),
                'regression_sha256': u.digest(Path(__file__).read_bytes()),
                'runtime_source_sha_supplied': self.args.source_sha, 'context': 'isolated-env',
                'recorded_pids': sorted(set(self.pids)),
                'all_pids_absent': all(u.process_identity(pid) is None for pid in self.pids),
                'native_inference': False, 'homebrew_transaction': False, 'full_release_pass': False}, indent=2).encode())
        print(json.dumps({'status': status, 'checks': len(self.records), 'full_release_pass': False}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--old-executable', required=True)
    parser.add_argument('--executable', required=True)
    parser.add_argument('--source-sha', required=True)
    parser.add_argument('--output-directory', required=True)
    os.umask(0o077)
    Checks(parser.parse_args()).run()

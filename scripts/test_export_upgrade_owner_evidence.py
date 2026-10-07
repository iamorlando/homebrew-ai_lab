#!/usr/bin/env python3
"""Fake-data stdlib tests. No application, process inspection or network calls."""
import copy
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('owner_export', Path(__file__).with_name('export_upgrade_owner_evidence.py'))
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='owner-evidence-fake-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root, self.proof = self.base / 'root', self.base / 'proof'
        self.root.mkdir(mode=0o700)
        self.proof.mkdir(mode=0o700)
        (self.root / '.upgrade-checker').mkdir(mode=0o700)
        self.checker = self.base / 'fake-checker.py'
        self.checker.write_text('# inert file, never executed\n')
        self.checker_hash = hashlib.sha256(self.checker.read_bytes()).hexdigest()
        self.state_path = self.proof / 'state.json'
        self.argv = [str(self.base / 'old/venv/bin/ai-lab'), '--root', str(self.root),
                     'completion', '--service-action', 'run']
        self.owner = {'pid': 4242, 'uid': os.getuid(), 'pgid': 4242,
                      'started': 'Tue Oct  6 23:47:14 2026',
                      'command': '/opt/homebrew/bin/python3.13 ' + ' '.join(self.argv)}
        info = self.root.stat()
        self.state = {'format': 'ai-lab-owned-upgrade-v1', 'uid': os.getuid(),
                      'root': str(self.root), 'state_path': str(self.state_path),
                      'nonce': 'a' * 32, 'root_identity': {'dev': info.st_dev, 'ino': info.st_ino, 'uid': info.st_uid},
                      'phase': 'preparing', 'socket_path': str(self.root / '.state/ai-lab/api.sock'),
                      'owner': self.owner, 'server_argv': self.argv,
                      'old_executable': {'path': self.argv[0], 'version': '0.1.13'}}
        self.event = {'moment': 'primary_before_cleanup', 'phase': 'before', 'observation': 'at_failure',
                      'captured_at': '2026-10-06T23:47:16Z', 'elapsed_seconds': 1.25,
                      'process_status': 'PRESENT', 'reason': 'IDENTITY_MISMATCH',
                      'expected': copy.deepcopy(self.owner), 'observed': copy.deepcopy(self.owner),
                      'differing_keys': ['command'], 'process_receipt_validated': True,
                      'socket_receipt_validated': False, 'socket_present': None,
                      'socket_identity_matches': None, 'after_verified': False,
                      'state_phase': 'preparing', 'process_exited': None,
                      'socket_removed': None, 'child_exit': None}
        self.event['observed']['command'] = ('/opt/homebrew/Cellar/python@3.13/3.13.16/Frameworks/'
            'Python.framework/Versions/3.13/Resources/Python.app/Contents/MacOS/Python ' + ' '.join(self.argv))
        self.args = SimpleNamespace(root=str(self.root), state=str(self.state_path),
            output=str(self.base / 'visible'), checker=str(self.checker), tap_sha='b' * 40,
            source_sha='c' * 40, run_id=123, run_attempt=1,
            before_report=str(self.proof / 'before.json'), after_report=str(self.base / 'upgrade.json'),
            cleanup_report=str(self.proof / 'cleanup.json'), before_outcome='failure',
            after_outcome='skipped', cleanup_outcome='failure')
        self.save_state()

    def write(self, path, value):
        path = Path(path)
        path.write_bytes(exporter.encoded(value))
        path.chmod(0o600)

    def save_state(self):
        self.write(self.state_path, self.state)
        private = self.root / '.upgrade-checker'
        self.write(private / 'owner.json', {k: self.state[k] for k in ('format', 'uid', 'root', 'state_path', 'nonce')})
        self.write(private / 'process-owner.json', {'nonce': self.state['nonce'], 'owner': self.owner,
                    'server_argv': self.argv, 'root': str(self.root), 'state_path': str(self.state_path)})

    def report(self, phase, events=(), **extra):
        value = {'phase': phase, 'status': 'FAIL', 'checker_sha256': self.checker_hash,
                 'root': str(self.root), 'state': str(self.state_path), 'error': 'private error sentinel',
                 'owner_diagnostics': {'schema': 1, 'events': list(events)}, **extra}
        self.write(getattr(self.args, phase + '_report'), value)
        return value

    def run_export(self):
        summary, manifest = exporter.export(self.args)
        data = (Path(self.args.output) / 'summary.json').read_bytes()
        self.assertEqual(manifest['files'], [{'name': 'summary.json', 'bytes': len(data),
                            'sha256': hashlib.sha256(data).hexdigest()}])
        self.assertEqual(set(p.name for p in Path(self.args.output).iterdir()), {'summary.json', 'manifest.json'})
        self.assertEqual(stat.S_IMODE(Path(self.args.output).stat().st_mode), 0o700)
        self.assertFalse(summary['full_release_pass'])
        return summary

    def test_primary_then_cleanup_and_immutable_duplicate(self):
        internal, explicit = copy.deepcopy(self.event), copy.deepcopy(self.event)
        internal.update(moment='internal_cleanup', elapsed_seconds=2.0)
        explicit.update(moment='explicit_cleanup', phase='cleanup', elapsed_seconds=0.2)
        self.state['owner_diagnostics'] = {'schema': 1, 'events': [self.event, internal, explicit]}
        self.save_state()
        self.report('before', [self.event, internal], cleanup_error='private cleanup error')
        self.report('cleanup', [self.event, internal, explicit])
        summary = self.run_export()
        self.assertEqual(summary['diagnostic_status'], 'EXPORTED')
        self.assertEqual(summary['coverage'], 'failure_time')
        self.assertEqual(len(summary['events']), 3)
        self.assertEqual([e['elapsed_seconds'] for e in summary['events']], [1.25, 2.0, 0.2])
        self.assertEqual(summary['phases']['before']['report_status'], 'FAIL')
        self.assertTrue(summary['phases']['before']['internal_cleanup_error_present'])
        self.assertEqual(summary['phases']['cleanup']['report_status'], 'FAIL')

    def test_command_transition_and_privacy(self):
        sentinel = 'SECRET_do_not_export_unique_19394'
        self.state['keys'] = {'password': sentinel}
        self.save_state()
        self.event['observed']['command'] += ' ' + sentinel
        self.event['unknown'] = {'argv': sentinel}
        self.report('before', [self.event], settings=sentinel, checks=[{'command': sentinel}])
        self.report('cleanup')
        (self.root / '.upgrade-checker/old-api.log').write_text(sentinel)
        summary = self.run_export()
        event = summary['events'][0]
        self.assertEqual(event['changed_fields'], ['command'])
        self.assertNotEqual(event['expected']['command_sha256'], event['observed']['command_sha256'])
        self.assertTrue(event['expected']['launch_suffix_matches'])
        self.assertFalse(event['observed']['launch_suffix_matches'])
        visible = ''.join(p.read_text() for p in Path(self.args.output).iterdir())
        for private in (sentinel, self.owner['command'], self.argv[0], 'private error sentinel', self.state['nonce']):
            self.assertNotIn(private, visible)

    def test_fixed_roles_exact_suffix_and_identity_change(self):
        self.report('before', [self.event])
        self.report('cleanup')
        event = self.run_export()['events'][0]
        self.assertEqual(event['expected']['interpreter_role'], 'homebrew-bin-python')
        self.assertEqual(event['observed']['interpreter_role'], 'Python.framework')
        self.assertTrue(event['observed']['launch_suffix_matches'])
        self.assertEqual(event['expected']['pid'], event['observed']['pid'])

    def test_pid_reuse(self):
        self.event['observed']['uid'] += 1
        self.event['observed']['started'] = 'Tue Oct  6 23:47:15 2026'
        self.event['differing_keys'] = ['command', 'uid', 'started']
        self.report('before', [self.event])
        self.assertEqual(self.run_export()['events'][0]['changed_fields'], ['command', 'started', 'uid'])

    def test_changed_process_group_one_is_observed_not_rejected(self):
        self.event['observed']['pgid'] = 1
        self.event['differing_keys'] = ['command', 'pgid']
        self.report('before', [self.event])
        self.assertEqual(self.run_export()['events'][0]['observed']['pgid'], 1)

    def test_absence_and_inspection_error_are_distinct(self):
        for status, reason in [('ABSENT', 'PROCESS_ABSENT'), ('INSPECTION_ERROR', 'INSPECTION_ERROR')]:
            with self.subTest(status=status):
                self.args.output = str(self.base / status)
                event = {**self.event, 'observed': None, 'process_status': status,
                         'reason': reason, 'differing_keys': []}
                self.report('before', [event])
                actual = self.run_export()['events'][0]
                self.assertEqual(actual['process_status'], status)
                self.assertEqual(actual['process_exited'], 'UNKNOWN')
                self.assertIsNone(actual['observed'])

    def test_missing_before_output_state_fallback(self):
        self.state['owner_diagnostics'] = {'schema': 1, 'events': [self.event]}
        self.save_state()
        summary = self.run_export()
        self.assertEqual(summary['diagnostic_status'], 'INCOMPLETE')
        self.assertEqual(summary['coverage'], 'failure_time')
        self.assertEqual(summary['phases']['before']['report_output_status'], 'MISSING')
        self.assertEqual(summary['phases']['before']['step_outcome'], 'failure')
        self.assertEqual(summary['phases']['before']['exit_status'], 'UNKNOWN')

    def test_missing_state_report_fallback_has_unknown_suffix(self):
        self.state_path.unlink()
        self.report('before', [self.event])
        summary = self.run_export()
        self.assertEqual(summary['coverage'], 'failure_time')
        self.assertEqual(summary['events'][0]['expected']['launch_suffix_matches'], 'UNKNOWN')

    def test_missing_all_inputs_is_not_run(self):
        self.state_path.unlink()
        summary = self.run_export()
        self.assertEqual(summary['diagnostic_status'], 'NOT_RUN')
        self.assertEqual(summary['events'], [])
        self.assertEqual(summary['phases']['before']['step_outcome'], 'failure')

    def test_late_success_and_late_only_after_failure(self):
        late = {**self.event, 'moment': 'late_observation', 'phase': 'cleanup', 'observation': 'late',
                'reason': 'CLEANUP_COMPLETE', 'process_status': 'ABSENT', 'observed': None,
                'differing_keys': [], 'process_exited': True, 'socket_removed': True, 'state_phase': 'cleaned'}
        self.report('before')
        self.report('cleanup', [late], status='PASS')
        summary = self.run_export()
        self.assertEqual(summary['diagnostic_status'], 'INCOMPLETE')
        self.assertEqual(summary['coverage'], 'late_only')
        self.assertEqual(summary['phases']['before']['report_status'], 'FAIL')
        self.assertEqual(summary['phases']['cleanup']['report_status'], 'PASS')
        self.args.output = str(self.base / 'successful')
        self.args.before_outcome = self.args.cleanup_outcome = 'success'
        self.report('before', status='PASS')
        self.assertEqual(self.run_export()['diagnostic_status'], 'EXPORTED')

    def test_conflicting_duplicate_rejected_including_unknown_fields(self):
        self.state['owner_diagnostics'] = {'schema': 1, 'events': [self.event]}
        self.save_state()
        other = copy.deepcopy(self.event)
        other['unknown_private'] = 'not the same record'
        self.report('before', [other])
        summary = self.run_export()
        self.assertEqual(summary['diagnostic_status'], 'INPUT_REJECTED')
        self.assertEqual(summary['events'], [])

    def test_event_contract_and_size_rejections(self):
        variants = [
            {'moment': 'late_observation'}, {'captured_at': 'SECRET_timestamp'},
            {'differing_keys': ['SECRET_field']}, {'phase': 'SECRET_phase'},
            {'elapsed_seconds': float('inf')}, {'process_status': 'ABSENT'},
            {'expected': {**self.owner, 'pid': True}},
        ]
        for index, delta in enumerate(variants):
            with self.subTest(delta=delta):
                self.args.output = str(self.base / ('invalid' + str(index)))
                self.report('before', [{**self.event, **delta}])
                self.assertEqual(self.run_export()['diagnostic_status'], 'INPUT_REJECTED')
        for index, events in enumerate(([self.event] * 5, [{**self.event, 'unknown': 'a' * 65_536}])):
            self.args.output = str(self.base / ('bound' + str(index)))
            self.report('before', events)
            self.assertEqual(self.run_export()['diagnostic_status'], 'INPUT_REJECTED')

    def test_capture_failure_is_secondary(self):
        self.report('before', [self.event], owner_diagnostics={
            'schema': 1, 'events': [self.event], 'capture_error': 'PERSISTENCE_ERROR'})
        self.report('cleanup')
        summary = self.run_export()
        self.assertEqual(summary['diagnostic_status'], 'INCOMPLETE')
        self.assertEqual(summary['capture_errors'], ['PERSISTENCE_ERROR'])
        self.assertEqual(summary['phases']['before']['report_status'], 'FAIL')

    def test_readiness_timeout_is_not_identity_mismatch(self):
        timeout = {**self.event, 'observed': self.event['expected'],
                   'differing_keys': [], 'reason': 'READINESS_TIMEOUT'}
        self.report('before', [timeout])
        event = self.run_export()['events'][0]
        self.assertEqual(event['reason'], 'READINESS_TIMEOUT')
        self.assertEqual(event['changed_fields'], [])

    def test_private_output_failure_retains_primary_and_cleanup_outcomes(self):
        self.report('before', [self.event], output_error='WRITE_ERROR', cleanup_error='private cleanup')
        self.report('cleanup', status='PASS')
        summary = self.run_export()
        before = summary['phases']['before']
        self.assertEqual(before['output_error'], 'WRITE_ERROR')
        self.assertEqual(before['report_status'], 'FAIL')
        self.assertTrue(before['primary_error_present'])
        self.assertTrue(before['internal_cleanup_error_present'])
        self.assertEqual(summary['phases']['cleanup']['report_status'], 'PASS')

    def test_startup_and_ready_receipts_remain_distinct(self):
        self.state['startup_owner'] = copy.deepcopy(self.owner)
        self.state['owner'] = copy.deepcopy(self.event['observed'])
        self.state['ready_owner_bound'] = True
        self.state['interpreter_binding'] = {'files': {'private interpreter path': {'sha256': 'd' * 64}}}
        self.state['owner_diagnostics'] = {'schema': 1, 'events': [self.event]}
        self.save_state()
        private = self.root / '.upgrade-checker'
        self.write(private / 'interpreter-owner.json', {'nonce': self.state['nonce'],
                    'binding': self.state['interpreter_binding'], 'server_argv': self.argv})
        self.write(private / 'ready-owner.json', {'nonce': self.state['nonce'], 'owner': self.state['owner'],
                    'startup_owner': self.state['startup_owner'], 'server_argv': self.argv})
        summary = self.run_export()
        self.assertTrue(summary['state']['process_receipt_validated'])
        self.assertTrue(summary['state']['ready_receipt_validated'])
        self.assertTrue(summary['state']['interpreter_receipt_validated'])
        self.assertEqual(summary['events'][0]['expected']['command_sha256'],
                         hashlib.sha256(self.owner['command'].encode()).hexdigest())
        self.assertNotIn('private interpreter path', json.dumps(summary))
        self.args.output = str(self.base / 'bad-ready')
        self.write(private / 'ready-owner.json', {'wrong': True})
        self.assertEqual(self.run_export()['diagnostic_status'], 'INPUT_REJECTED')

    def test_unready_receipt_cannot_be_silently_promoted(self):
        self.state['startup_owner'] = self.owner
        self.state['interpreter_binding'] = {}
        self.save_state()
        private = self.root / '.upgrade-checker'
        self.write(private / 'interpreter-owner.json', {'nonce': self.state['nonce'],
                    'binding': {}, 'server_argv': self.argv})
        summary = self.run_export()
        self.assertFalse(summary['state']['ready_receipt_validated'])
        self.args.output = str(self.base / 'unexpected-ready')
        self.write(private / 'ready-owner.json', {'owner': self.owner})
        self.assertEqual(self.run_export()['diagnostic_status'], 'INPUT_REJECTED')

    def test_after_outcome_is_allowlisted(self):
        self.args.after_outcome = 'failure'
        self.report('after', [self.event], error='PRIVATE_AFTER_SECRET', after_verified=True)
        summary = self.run_export()
        self.assertTrue(summary['phases']['after']['after_verified'])
        self.assertEqual(summary['phases']['after']['report_status'], 'FAIL')
        self.assertNotIn('PRIVATE_AFTER_SECRET', json.dumps(summary))

    def test_symlink_hardlink_unsafe_mode_fifo_oversize_and_duplicate_json(self):
        original = self.state_path.read_bytes()
        backup = self.proof / 'original.json'
        self.write(backup, self.state)
        for kind in ('symlink', 'hardlink', 'unsafe_mode', 'fifo', 'oversize', 'duplicate_json', 'malformed'):
            with self.subTest(kind=kind):
                self.args.output = str(self.base / kind)
                self.state_path.unlink()
                if kind == 'symlink': self.state_path.symlink_to(backup)
                elif kind == 'hardlink': os.link(backup, self.state_path)
                elif kind == 'fifo': os.mkfifo(self.state_path, 0o600)
                else:
                    self.state_path.write_bytes(b'x' * (exporter.STATE_LIMIT + 1) if kind == 'oversize'
                        else b'{"phase": "preparing", "phase": "cleaned"}' if kind == 'duplicate_json'
                        else b'PRIVATE_invalid_json' if kind == 'malformed' else original)
                    self.state_path.chmod(0o644 if kind == 'unsafe_mode' else 0o600)
                self.assertEqual(self.run_export()['diagnostic_status'], 'INPUT_REJECTED')

    def test_foreign_file_uid(self):
        real_fstat = os.fstat
        def foreign(fd):
            info = real_fstat(fd)
            if stat.S_ISREG(info.st_mode) and info.st_ino == self.state_path.stat().st_ino:
                return SimpleNamespace(**{name: (info.st_uid + 1 if name == 'st_uid' else getattr(info, name))
                                          for name in dir(info) if name.startswith('st_')})
            return info
        with patch.object(exporter.os, 'fstat', side_effect=foreign):
            self.assertEqual(self.run_export()['diagnostic_status'], 'INPUT_REJECTED')

    def test_symlink_parent_and_unsafe_parent(self):
        link = self.base / 'linked-proof'
        link.symlink_to(self.proof, target_is_directory=True)
        self.args.state = str(link / 'state.json')
        self.assertEqual(self.run_export()['diagnostic_status'], 'INPUT_REJECTED')
        self.args.state = str(self.state_path)
        self.proof.chmod(0o777)
        self.args.output = str(self.base / 'unsafe-parent')
        self.assertEqual(self.run_export()['diagnostic_status'], 'INPUT_REJECTED')
        self.proof.chmod(0o700)

    def test_output_exclusive_and_outside_private_paths(self):
        self.run_export()
        before = (Path(self.args.output) / 'summary.json').read_bytes()
        with self.assertRaises(FileExistsError): exporter.export(self.args)
        self.assertEqual((Path(self.args.output) / 'summary.json').read_bytes(), before)
        for target in (self.root / 'export', self.proof / 'export', self.base):
            self.args.output = str(target)
            with self.assertRaises(exporter.Rejected): exporter.export(self.args)
        link = self.base / 'linked-output'
        link.symlink_to(self.base, target_is_directory=True)
        self.args.output = str(link / 'new')
        with self.assertRaises(OSError): exporter.export(self.args)

    def test_replaced_output_directory_and_oversized_summary_fail_closed(self):
        real_write = exporter.write_file
        def replace_directory(fd, name, data):
            real_write(fd, name, data)
            if name == 'summary.json':
                Path(self.args.output).rename(self.base / 'moved')
                Path(self.args.output).mkdir(mode=0o700)
        with patch.object(exporter, 'write_file', side_effect=replace_directory):
            with self.assertRaises(exporter.Rejected): exporter.export(self.args)
        with self.assertRaises(exporter.Rejected):
            exporter.write_export(self.base / 'too-large', {'diagnostic_status': 'INCOMPLETE', 'x': 'a' * 65_536})

    def test_deterministic_manifest_and_no_probe_imports(self):
        self.report('before', [self.event])
        self.run_export()
        initial = (Path(self.args.output) / 'summary.json').read_bytes()
        self.args.output = str(self.base / 'second')
        self.run_export()
        self.assertEqual(initial, (Path(self.args.output) / 'summary.json').read_bytes())
        import ast
        tree = ast.parse(Path(exporter.__file__).read_text())
        modules = [n.names[0].name for n in ast.walk(tree) if isinstance(n, ast.Import)]
        self.assertFalse(set(modules) & {'subprocess', 'socket', 'http', 'urllib', 'signal'})

    def test_cli_does_not_print_private_inputs_or_exception_text(self):
        sentinel = 'SECRET_stdout_stderr_test_23887'
        self.report('before', [self.event], error=sentinel)
        self.report('cleanup')
        argv = ['export_upgrade_owner_evidence.py']
        for key, value in vars(self.args).items():
            argv.extend(['--' + key.replace('_', '-'), str(value)])
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch('sys.argv', argv), redirect_stdout(stdout), redirect_stderr(stderr):
            self.assertEqual(exporter.main(), 0)
        self.assertNotIn(sentinel, stdout.getvalue() + stderr.getvalue())
        self.assertEqual(set(json.loads(stdout.getvalue())), {'diagnostic_status', 'coverage', 'full_release_pass'})
        with patch('sys.argv', argv), redirect_stdout(stdout), redirect_stderr(stderr):
            self.assertEqual(exporter.main(), 1)  # Existing output remains untouched.
        self.assertNotIn(str(self.base), stdout.getvalue() + stderr.getvalue())


if __name__ == '__main__':
    unittest.main()

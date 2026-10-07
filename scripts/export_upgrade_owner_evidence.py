#!/usr/bin/env python3
"""Export bounded owner evidence; never inspect processes or copy private inputs."""
import argparse
from contextlib import contextmanager
from datetime import datetime
import errno
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import stat

SMALL_LIMIT = 65_536
STATE_LIMIT = 4_000_000
MOMENTS = ('primary_before_cleanup', 'internal_cleanup', 'explicit_cleanup', 'late_observation')
IDENTITY_FIELDS = ('pid', 'uid', 'pgid', 'started', 'command')
PHASES = ('before', 'after', 'cleanup')
STEPS = ('success', 'failure', 'cancelled', 'skipped', 'UNKNOWN')


class Rejected(ValueError):
    """Untrusted input was outside the fixed diagnostic contract."""


def require(condition):
    if not condition:
        raise Rejected('INPUT_REJECTED')


def absolute(value):
    path = Path(value)
    require(path.is_absolute() and '..' not in path.parts
            and not any(ord(c) < 32 for c in str(path)))
    return path


@contextmanager
def directory_fd(path, *, owned=False, private=False):
    """Walk from / with no-follow directory descriptors, not resolve()+open()."""
    path = absolute(path)
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in path.parts[1:]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                              dir_fd=fd)
            os.close(fd)
            fd = next_fd
            info = os.fstat(fd)
            # System sticky temporary ancestors are allowed, not writable input
            # directories. Every component still has to be a real directory.
            require(info.st_uid in (0, os.getuid()))
            require(not (info.st_mode & 0o022)
                    or (info.st_uid == 0 and info.st_mode & stat.S_ISVTX))
        info = os.fstat(fd)
        if owned:
            require(info.st_uid == os.getuid() and not info.st_mode & 0o022)
        if private:
            require(stat.S_IMODE(info.st_mode) == 0o700)
        yield fd
    finally:
        os.close(fd)


def bounded_read(path, limit, *, private=True):
    """Read one explicit regular file. Reject links, unsafe modes and races."""
    path = absolute(path)
    with directory_fd(path.parent, owned=True) as parent:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                     dir_fd=parent)
        try:
            before = os.fstat(fd)
            require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
                    and before.st_uid == os.getuid() and before.st_size <= limit)
            require(stat.S_IMODE(before.st_mode) == 0o600 if private
                    else not before.st_mode & 0o022)
            chunks, size = [], 0
            while size <= limit:
                chunk = os.read(fd, min(65_536, limit + 1 - size))
                if not chunk:
                    break
                chunks.append(chunk)
                size += len(chunk)
            after = os.fstat(fd)
            identity = lambda s: (s.st_dev, s.st_ino, s.st_uid, s.st_nlink,
                                  s.st_mode, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
            require(size <= limit and identity(before) == identity(after)
                    and size == before.st_size)
            # A swapped directory entry is not the file we attested above.
            current = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
            require(identity(current) == identity(after))
            return b''.join(chunks)
        finally:
            os.close(fd)


def read_json(path, limit):
    """Never include exception text, paths or private values in diagnostics."""
    try:
        data = bounded_read(path, limit)
        value = json.loads(data, object_pairs_hook=unique_object,
                           parse_constant=lambda value: require(False))
        require(type(value) is dict)
        return value, {'status': 'PRESENT', 'bytes': len(data),
                       'sha256': hashlib.sha256(data).hexdigest()}
    except FileNotFoundError:
        return None, {'status': 'MISSING'}
    except (Rejected, ValueError, UnicodeError, RecursionError):
        return None, {'status': 'INPUT_REJECTED'}
    except OSError as error:
        return None, {'status': 'INPUT_REJECTED' if error.errno in
                      (errno.ELOOP, errno.ENOTDIR) else 'INSPECTION_ERROR'}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result)
        result[key] = value
    return result


def integer(value, minimum=0, maximum=2**63 - 1):
    require(type(value) is int and minimum <= value <= maximum)
    return value


def boolean(value):
    require(type(value) is bool)
    return value


def choice(value, choices):
    require(type(value) is str and value in choices)
    return value


def hexadecimal(value, length):
    require(type(value) is str and re.fullmatch('[0-9a-f]{%d}' % length, value))
    return value


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def fingerprint(value, argv):
    if value is None:
        return None
    require(type(value) is dict and set(value) == set(IDENTITY_FIELDS))
    result = {k: integer(value[k], 2 if k == 'pid' else 1 if k == 'pgid' else 0, 2**32 - 1)
              for k in ('pid', 'uid', 'pgid')}
    started = value['started']
    require(type(started) is str and re.fullmatch(
        r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
        r' {1,2}[0-9]{1,2} [0-9]{2}:[0-9]{2}:[0-9]{2} [0-9]{4}', started))
    datetime.strptime(started, '%a %b %d %H:%M:%S %Y')
    result['started'] = started
    command = value['command']
    require(type(command) is str and 0 < len(command.encode()) <= SMALL_LIMIT)
    result.update(command_sha256=hashlib.sha256(command.encode()).hexdigest(),
                  command_bytes=len(command.encode()), launch_suffix_matches='UNKNOWN',
                  interpreter_role='unparsed')
    if argv is not None:
        suffix = ' '.join(argv)
        # This is diagnostic comparison only, never authorization to act on a PID.
        matches = command == suffix or command.endswith(' ' + suffix)
        result['launch_suffix_matches'] = matches
        if matches:
            prefix = command[:-len(suffix)].strip()
            try:
                tokens = shlex.split(prefix)
            except ValueError:
                tokens = []
            role = 'other'
            if len(tokens) != 1:
                role = 'unparsed'
            elif re.fullmatch(r'/[^\r\n]*Python\.framework/[^\r\n]*/Python', tokens[0]):
                role = 'Python.framework'
            elif re.fullmatch(r'/[^\r\n]*/(?:\.?venv)/bin/python(?:3(?:\.[0-9]+)?)?', tokens[0]):
                role = 'venv-python'
            elif re.fullmatch(r'/opt/homebrew/(?:bin|opt/python@3\.[0-9]+/bin)/python3(?:\.[0-9]+)?', tokens[0]):
                role = 'homebrew-bin-python'
            result['interpreter_role'] = role
    return result


def event_summary(event, argv):
    require(type(event) is dict)
    moment = choice(event.get('moment'), MOMENTS)
    phase = choice(event.get('phase'), PHASES)
    observation = choice(event.get('observation'), ('at_failure', 'late'))
    reason = choice(event.get('reason'), ('IDENTITY_MISMATCH', 'PROCESS_ABSENT',
                    'INSPECTION_ERROR', 'UNVERIFIED_OWNER', 'CLEANUP_COMPLETE', 'READINESS_TIMEOUT'))
    require((moment == 'late_observation') == (observation == 'late'))
    require((reason == 'CLEANUP_COMPLETE') == (observation == 'late'))
    require(phase == 'cleanup' if moment == 'explicit_cleanup'
            else phase in ('before', 'after') if moment in MOMENTS[:2] else True)
    captured = event.get('captured_at')
    require(type(captured) is str and re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z', captured))
    datetime.strptime(captured, '%Y-%m-%dT%H:%M:%SZ')
    elapsed = event.get('elapsed_seconds')
    require(type(elapsed) in (float, int) and math.isfinite(elapsed) and 0 <= elapsed <= 10_000_000)
    process_status = choice(event.get('process_status'), ('PRESENT', 'ABSENT', 'INSPECTION_ERROR'))
    expected, observed = event.get('expected'), event.get('observed')
    require((observed is not None) == (process_status == 'PRESENT'))
    if reason == 'PROCESS_ABSENT':
        require(process_status == 'ABSENT')
    if reason == 'INSPECTION_ERROR':
        require(process_status == 'INSPECTION_ERROR')
    expected_safe, observed_safe = fingerprint(expected, argv), fingerprint(observed, argv)
    differing = event.get('differing_keys')
    require(type(differing) is list and len(differing) <= 6
            and all(type(k) is str and k in (*IDENTITY_FIELDS, 'unexpected_fields') for k in differing)
            and len(set(differing)) == len(differing))
    if expected is not None and observed is not None:
        actual = [key for key in IDENTITY_FIELDS if expected[key] != observed[key]]
        require(set(actual) == set(differing) - {'unexpected_fields'})
    if reason == 'IDENTITY_MISMATCH':
        require(expected is not None and observed is not None and differing)
    result = {'moment': moment, 'phase': phase, 'observation': observation,
              'captured_at': captured, 'elapsed_seconds': elapsed,
              'elapsed_scope': 'this_phase_invocation_only', 'process_status': process_status,
              'reason': reason, 'expected': expected_safe, 'observed': observed_safe,
              'changed_fields': sorted(differing)}
    for key in ('process_receipt_validated', 'socket_receipt_validated', 'after_verified'):
        result[key] = boolean(event.get(key))
    for key in ('socket_present', 'socket_identity_matches', 'process_exited', 'socket_removed'):
        value = event.get(key)
        result[key] = 'UNKNOWN' if value is None else boolean(value)
    require(not (process_status == 'INSPECTION_ERROR' and result['process_exited'] is True))
    result['state_phase'] = choice(event.get('state_phase'), ('preparing', 'before_ready', 'cleaned', 'UNKNOWN'))
    result['child_exit'] = (None if event.get('child_exit') is None
                            else integer(event['child_exit'], -255, 255))
    return result


def collect_events(inputs, argv):
    events, raw_events, capture_errors = {}, {}, set()
    for value in inputs:
        if value is None or 'owner_diagnostics' not in value:
            continue
        envelope = value['owner_diagnostics']
        require(type(envelope) is dict and type(envelope.get('schema')) is int
                and envelope['schema'] == 1 and len(encoded(envelope)) <= SMALL_LIMIT)
        incoming = envelope.get('events')
        require(type(incoming) is list and len(incoming) <= 4)
        if 'capture_error' in envelope:
            capture_errors.add(choice(envelope['capture_error'], ('PERSISTENCE_ERROR', 'CAPTURE_ERROR')))
        for event in incoming:
            safe = event_summary(event, argv)
            moment = safe['moment']
            # Compare the original event, not only sanitized fields: even an
            # unknown-field difference is a conflict, never last-writer-wins.
            original = encoded(event)
            require(moment not in raw_events or raw_events[moment] == original)
            raw_events[moment], events[moment] = original, safe
        require(len(events) <= 4)
    return [events[m] for m in MOMENTS if m in events], sorted(capture_errors)


def state_summary(state, root, state_path, inputs):
    if state is None:
        return None, {'validation': 'UNAVAILABLE'}
    require(state.get('format') == 'ai-lab-owned-upgrade-v1'
            and type(state.get('uid')) is int and state['uid'] == os.getuid()
            and state.get('root') == str(root) and state.get('state_path') == str(state_path))
    hexadecimal(state.get('nonce'), 32)
    with directory_fd(root, owned=True, private=True) as fd:
        info = os.fstat(fd)
        require(state.get('root_identity') == {'dev': info.st_dev, 'ino': info.st_ino, 'uid': info.st_uid})
    with directory_fd(root / '.upgrade-checker', owned=True, private=True):
        pass
    require(state.get('socket_path') == str(root / '.state/ai-lab/api.sock'))
    marker, inputs['marker'] = read_json(root / '.upgrade-checker/owner.json', SMALL_LIMIT)
    require(marker == {k: state[k] for k in ('format', 'uid', 'root', 'state_path', 'nonce')})
    result = {'validation': 'VALIDATED', 'phase': choice(state.get('phase'),
              ('preparing', 'before_ready', 'cleaned')), 'after_verified': boolean(state.get('after_verified', False)),
              'marker_validated': True, 'process_receipt_validated': False, 'socket_receipt_validated': False,
              'ready_receipt_validated': False, 'interpreter_receipt_validated': False,
              'receipt_validation_scope': 'private_inputs_only_no_live_or_interpreter_file_probes'}
    argv = state.get('server_argv')
    if argv is not None:
        require(type(argv) is list and len(argv) == 6
                and type(argv[0]) is str and len(argv[0].encode()) <= 4096
                and absolute(argv[0]).name == 'ai-lab'
                and argv[1:] == ['--root', str(root), 'completion', '--service-action', 'run'])
        old = state.get('old_executable')
        require(type(old) is dict and old.get('path') == argv[0] and old.get('version') == '0.1.13')
    owner = state.get('owner')
    if owner is not None:
        fingerprint(owner, argv)
        require(argv is not None and owner['uid'] == os.getuid() and owner['pgid'] == owner['pid'])
        startup_owner = state.get('startup_owner', owner)
        fingerprint(startup_owner, argv)
        receipt, inputs['process_receipt'] = read_json(root / '.upgrade-checker/process-owner.json', SMALL_LIMIT)
        require(receipt == {'nonce': state['nonce'], 'owner': startup_owner, 'server_argv': argv,
                            'root': str(root), 'state_path': str(state_path)})
        result['process_receipt_validated'] = True
        if 'startup_owner' in state:
            binding = state.get('interpreter_binding')
            require(type(binding) is dict and len(encoded(binding)) <= SMALL_LIMIT)
            receipt, inputs['interpreter_receipt'] = read_json(root / '.upgrade-checker/interpreter-owner.json', SMALL_LIMIT)
            require(receipt == {'nonce': state['nonce'], 'binding': binding, 'server_argv': argv})
            result['interpreter_receipt_validated'] = True
            receipt, inputs['ready_receipt'] = read_json(root / '.upgrade-checker/ready-owner.json', SMALL_LIMIT)
            bound = boolean(state.get('ready_owner_bound', False))
            require(bound == (inputs['ready_receipt']['status'] == 'PRESENT'))
            if bound:
                require(receipt == {'nonce': state['nonce'], 'owner': owner,
                                    'startup_owner': startup_owner, 'server_argv': argv})
                result['ready_receipt_validated'] = True
            else:
                require(owner == startup_owner and inputs['ready_receipt']['status'] == 'MISSING')
    if 'socket_identity' in state:
        identity = state['socket_identity']
        require(type(identity) is dict and set(identity) == {'dev', 'ino', 'uid'} and owner is not None)
        for value in identity.values():
            integer(value)
        require(identity['uid'] == os.getuid())
        receipt, inputs['socket_receipt'] = read_json(root / '.upgrade-checker/socket-owner.json', SMALL_LIMIT)
        require(receipt == {'nonce': state['nonce'], 'pid': owner['pid'], 'socket_identity': identity})
        result['socket_receipt_validated'] = True
    cleanup = state.get('cleanup')
    result['cleanup'] = {k: 'UNKNOWN' for k in ('process_exited', 'socket_removed')}
    if cleanup is not None:
        require(type(cleanup) is dict)
        for key in result['cleanup']:
            if key in cleanup:
                result['cleanup'][key] = boolean(cleanup[key])
    return argv, result


def phase_summary(report, phase, outcome, checker_hash, root, state):
    result = {'step_outcome': choice(outcome, STEPS), 'report_status': 'UNAVAILABLE',
              'exit_status': 'UNKNOWN'}
    if report is None:
        return result
    require(report.get('phase') == phase and report.get('checker_sha256') == checker_hash)
    for key, expected in (('root', str(root)), ('state', str(state))):
        require(key not in report or report[key] == expected)
    result.update(report_status=choice(report.get('status'), ('PASS', 'FAIL')),
                  primary_error_present=report.get('error') is not None,
                  internal_cleanup_error_present=report.get('cleanup_error') is not None,
                  after_verified=boolean(report['after_verified']) if 'after_verified' in report else 'UNKNOWN',
                  output_error=choice(report['output_error'], ('WRITE_ERROR',)) if 'output_error' in report else 'NONE_RECORDED')
    # Presence/absence of a report is distinct from a step outcome. In particular
    # a missing output is never called a successful or failed historical phase.
    if 'exit_status' in report:
        result['exit_status'] = integer(report['exit_status'], -255, 255)
    if 'checks' in report:
        require(type(report['checks']) is list and len(report['checks']) <= 1024)
        result['checks_count'] = len(report['checks'])
    return result


def export(args):
    root, state, output = map(absolute, (args.root, args.state, args.output))
    reports = {phase: absolute(getattr(args, phase + '_report')) for phase in PHASES}
    require(state.parent != root and not state.is_relative_to(root))
    private_paths = [state, *reports.values()]
    require(len(set(private_paths)) == 4 and all(not path.is_relative_to(root) for path in private_paths))
    require(not output.is_relative_to(root) and not root.is_relative_to(output)
            and not output.is_relative_to(state.parent) and not state.parent.is_relative_to(output)
            and all(not path.is_relative_to(output) and not output.is_relative_to(path) for path in private_paths))
    summary = {'schema_version': 1, 'installation': 'upgrade', 'full_release_pass': False,
               'diagnostic_status': 'NOT_RUN', 'coverage': 'no_events', 'events': [],
               'provenance': {'tap_sha': hexadecimal(args.tap_sha, 40),
                              'source_sha': hexadecimal(args.source_sha, 40),
                              'run_id': integer(args.run_id, 1), 'run_attempt': integer(args.run_attempt, 1)},
               'inputs': {}, 'phases': {}}
    inputs = summary['inputs']
    state_value, inputs['state'] = read_json(state, STATE_LIMIT)
    phase_values = {}
    for phase, path in reports.items():
        phase_values[phase], inputs[phase] = read_json(path, STATE_LIMIT)
        summary['phases'][phase] = {'step_outcome': choice(getattr(args, phase + '_outcome'), STEPS),
                                    'report_status': 'UNAVAILABLE', 'exit_status': 'UNKNOWN'}
    try:
        checker_bytes = bounded_read(absolute(args.checker), STATE_LIMIT, private=False)
        checker_hash = hashlib.sha256(checker_bytes).hexdigest()
        summary['provenance']['checker_sha256'] = checker_hash
        argv, summary['state'] = state_summary(state_value, root, state, inputs)
        for phase in PHASES:
            summary['phases'][phase] = phase_summary(phase_values[phase], phase,
                getattr(args, phase + '_outcome'), checker_hash, root, state)
        events, capture_errors = collect_events([state_value, *phase_values.values()], argv)
        summary.update(events=events, capture_errors=capture_errors)
        primary = any(e['moment'] == 'primary_before_cleanup' and e['observation'] == 'at_failure' for e in events)
        summary['coverage'] = ('failure_time' if primary else 'late_only' if events
                               and all(e['observation'] == 'late' for e in events) else 'no_primary_failure_event' if events else 'no_events')
        present = any(inputs[key]['status'] == 'PRESENT' for key in ('state', *PHASES))
        summary['diagnostic_status'] = 'EXPORTED' if present else 'NOT_RUN'
        if present and (capture_errors or not events or any(
                summary['phases'][phase].get('output_error') == 'WRITE_ERROR' for phase in PHASES) or any(
                inputs[phase]['status'] == 'MISSING' and getattr(args, phase + '_outcome') in ('success', 'failure')
                for phase in PHASES)):
            summary['diagnostic_status'] = 'INCOMPLETE'
        if summary['coverage'] == 'late_only' and any(getattr(args, p + '_outcome') == 'failure' for p in PHASES):
            summary['diagnostic_status'] = 'INCOMPLETE'
    except (Rejected, ValueError, KeyError, TypeError, UnicodeError, RecursionError):
        summary.update(diagnostic_status='INPUT_REJECTED', events=[], coverage='no_events',
                       diagnostic_error='INPUT_CONTRACT_REJECTED')
    except OSError:
        summary.update(diagnostic_status='INCOMPLETE', diagnostic_error='INPUT_INSPECTION_ERROR')
    for phase in PHASES:
        summary['phases'][phase]['report_output_status'] = inputs[phase]['status']
    if any(item['status'] == 'INPUT_REJECTED' for item in inputs.values()):
        summary.update(diagnostic_status='INPUT_REJECTED', events=[], coverage='no_events')
    elif any(item['status'] == 'INSPECTION_ERROR' for item in inputs.values()):
        summary['diagnostic_status'] = 'INCOMPLETE'
    manifest = write_export(output, summary)
    return summary, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'state', 'before-report', 'after-report', 'cleanup-report',
                 'checker', 'output', 'tap-sha', 'source-sha'):
        parser.add_argument('--' + name, required=True)
    for phase in PHASES:
        parser.add_argument('--' + phase + '-outcome', choices=STEPS, default='UNKNOWN')
    parser.add_argument('--run-id', type=int, required=True)
    parser.add_argument('--run-attempt', type=int, required=True)
    args = parser.parse_args()
    try:
        summary, _ = export(args)
    except (Exception, KeyboardInterrupt):
        # The original checker step owns its failure. This separate exporter may
        # fail too, but neither arbitrary exceptions nor input paths are echoed.
        print(json.dumps({'diagnostic_status': 'INPUT_REJECTED',
                          'diagnostic_error': 'EXPORT_UNAVAILABLE', 'full_release_pass': False}))
        return 1
    print(json.dumps({key: summary[key] for key in ('diagnostic_status', 'coverage', 'full_release_pass')}))
    return 1 if summary['diagnostic_status'] in ('INPUT_REJECTED', 'INCOMPLETE') else 0


def write_file(parent, name, data):
    fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                 0o600, dir_fd=parent)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def write_export(output, summary):
    """Fresh fixed-name visible output only; never overwrite earlier evidence."""
    output = absolute(output)
    data = encoded(summary)
    require(len(data) <= SMALL_LIMIT)
    with directory_fd(output.parent, owned=True) as parent:
        os.mkdir(output.name, mode=0o700, dir_fd=parent)
        fd = os.open(output.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                     dir_fd=parent)
        try:
            identity = os.fstat(fd)
            write_file(fd, 'summary.json', data)
            manifest = {'schema_version': 1, 'status': summary['diagnostic_status'],
                        'files': [{'name': 'summary.json', 'bytes': len(data),
                                   'sha256': hashlib.sha256(data).hexdigest()}]}
            write_file(fd, 'manifest.json', encoded(manifest))
            current = os.stat(output.name, dir_fd=parent, follow_symlinks=False)
            require((current.st_dev, current.st_ino, current.st_mode, current.st_uid) ==
                    (identity.st_dev, identity.st_ino, identity.st_mode, identity.st_uid))
        finally:
            os.close(fd)
    return manifest


if __name__ == '__main__':
    raise SystemExit(main())

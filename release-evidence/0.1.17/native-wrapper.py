import datetime
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

directory = Path('/private/tmp/qwen017-native')
root = Path('/Users/orlando/dev/deepseek/.worktrees/qwen38-integration')
environment = {key: os.environ[key] for key in ('HOME', 'TMPDIR') if key in os.environ}
environment.update(PATH='/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin', LANG='en_US.UTF-8', PYTHONUNBUFFERED='1')
command = [sys.executable, '-I', str(directory / 'check_qwen_native.py'),
           '--root', str(root), '--output', str(directory / 'native-results.json'), '--start-through-app', '--mcp-wire']
with socket.socket() as sock:
    sock.bind(('127.0.0.1', 11440))
record = {'command': command, 'cwd': '/private/tmp', 'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'environment_keys': sorted(environment), 'fixture': False,
          'driver_sha256': hashlib.sha256((directory / 'check_qwen_native.py').read_bytes()).hexdigest()}
started = time.monotonic()
started_ns = time.time_ns()
with (directory / 'native.stdout').open('w') as out, (directory / 'native.stderr').open('w') as err:
    process = subprocess.Popen(command, env=environment, cwd='/private/tmp', stdout=out, stderr=err, start_new_session=True)
    record['driver_pid'] = process.pid
    try:
        record['exit_code'] = process.wait(timeout=1200)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
        record['exit_code'] = 124
        record['error'] = 'Native run exceeded authorized 20-minute bound.'
from ai_lab.paths import load_backend
load_backend(root)
import inference
state = inference.owned_state('qwen38')
record['remaining_owned_state'] = state
if state and state.get('started_at_ns', 0) >= started_ns:
    record['fallback_cleanup'] = inference.stop('qwen38')
with socket.socket() as sock:
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        assert sock.connect_ex(('127.0.0.1', 11440)) != 0
        sock.bind(('127.0.0.1', 11440))
        record['endpoint_released'] = True
    except OSError:
        record['endpoint_released'] = False
record['receipt_removed'] = not (root / '.state/qwen38-server.json').exists()
record['elapsed_seconds'] = round(time.monotonic() - started, 3)
log = root / '.state/qwen38-server.log'
if log.exists():
    (directory / 'qwen38-server.log').write_bytes(log.read_bytes())
(directory / 'native-command.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2), flush=True)
sys.exit(record['exit_code'] or (0 if record['endpoint_released'] and record['receipt_removed'] else 1))

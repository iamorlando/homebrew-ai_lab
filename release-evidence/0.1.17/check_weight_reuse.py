"""Verify real installed Qwen weight reuse without permitting any download."""
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

from ai_lab.downloads import catalog, install, verified_present
from ai_lab.paths import root_path

root = root_path('/Users/orlando/dev/deepseek/.worktrees/qwen38-integration')
output = Path('/private/tmp/qwen017-native/weight-reuse.json')
files = catalog()['qwen38']['files']

def identities():
    result = {}
    for row in files:
        path = root / row['path']
        stat = path.stat()
        with path.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        assert digest == row['sha256'] and stat.st_size == row['bytes'], row['path']
        result[row['path']] = {'sha256': digest, 'bytes': stat.st_size, 'device': stat.st_dev,
            'inode': stat.st_ino, 'mtime_ns': stat.st_mtime_ns, 'ctime_ns': stat.st_ctime_ns}
    return result

before = identities()
assert all(verified_present(root, row) for row in files)
with patch('ai_lab.downloads.download_file', side_effect=AssertionError('Verified weights must not download')) as weight_download, \
     patch('urllib.request.urlopen', side_effect=AssertionError('Ready setup must not make a network request')) as network:
    result = install(root, ['qwen38'], yes=True)
assert weight_download.call_count == 0 and network.call_count == 0
after = identities()
assert before == after
report = {'status': 'PASS', 'python': sys.executable, 'root': str(root),
    'kind': 'real-weight adoption by installed0.1.17 after earlier0.1.16setup; separate from literal package environment upgrade',
    'result': result, 'weight_download_calls': weight_download.call_count,
    'network_calls': network.call_count, 'identity_and_hash_unchanged': before == after,
    'files': after}
output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({key: value for key, value in report.items() if key != 'files'}, indent=2))

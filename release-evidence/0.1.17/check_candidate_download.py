"""Validate candidate downloader integrity without network or Homebrew execution."""
import hashlib
import io
import json
from pathlib import Path
import runpy
import sys
import tempfile
from unittest.mock import patch

tap = Path(__file__).resolve().parents[2]
script = tap / 'scripts/candidate_homebrew.py'
payload = (tap / 'packages/0.1.17/ai_lab-0.1.17.tar.gz').read_bytes()
cases = [
    ('exact', payload, 'https://example.invalid/pkg', True),
    ('bad-hash', b'x' * len(payload), 'https://example.invalid/pkg', False),
    ('truncated', payload[:-1], 'https://example.invalid/pkg', False),
    ('insecure', payload, 'http://example.invalid/pkg', False),
]
for label, data, url, expected_success in cases:
    with tempfile.TemporaryDirectory(prefix='qwen017-download-check-') as directory:
        root = Path(directory)
        evidence = root / 'evidence'
        (root / 'release-binding.json').write_text(json.dumps({
            'version': '0.1.17',
            'sdist_sha256': hashlib.sha256(payload).hexdigest(),
            'sdist_bytes': len(payload),
        }))
        (root / 'release-delivery.json').write_text(json.dumps({
            'assets': {'ai_lab-0.1.17.tar.gz': url},
            'delivery': 'owned test transport',
        }))
        succeeded = False
        with patch.object(sys, 'argv', [str(script), 'download', '--directory', str(root), '--evidence', str(evidence)]), patch('urllib.request.urlopen', return_value=io.BytesIO(data)) as transport:
            try:
                runpy.run_path(str(script), run_name='__main__')
            except SystemExit as error:
                succeeded = error.code == 0
            except AssertionError:
                pass
        assert succeeded == expected_success, label
        assert (evidence / 'asset.json').exists() == expected_success, label
        if expected_success:
            assert (evidence / 'ai_lab-0.1.17.tar.gz').read_bytes() == payload
        if label == 'insecure':
            transport.assert_not_called()
        print(label, 'PASS')
print('Four integrity/transport cases passed. No network, Homebrew, or native execution.')

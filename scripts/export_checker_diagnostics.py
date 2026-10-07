#!/usr/bin/env python3
"""Export only sanitized timeout bodies from an owned checker run for CI."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat


def require(value, message):
    if not value:
        raise ValueError(message)


def regular(path, base):
    require(path.is_relative_to(base), 'Diagnostic escapes the owned checker root')
    for item in (path, *path.parents):
        require(not item.is_symlink(), 'Refuse a symlink diagnostic path')
        if item == base:
            break
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_uid == os.getuid(),
            'Diagnostic is not a private owned regular file')
    require(info.st_mode & 0o077 == 0 and info.st_size <= 2_000_000,
            'Diagnostic permissions or size exceed the export contract')
    return path.read_bytes()


def references(value):
    result = {}

    def merge(nested):
        for path, digest in references(nested).items():
            require(path not in result or result[path] == digest,
                    'Conflicting recorded diagnostic hashes')
            result[path] = digest

    if isinstance(value, dict):
        if 'diagnostic_path' in value:
            require(isinstance(value['diagnostic_path'], str)
                    and isinstance(value.get('diagnostic_sha256'), str)
                    and re.fullmatch('[0-9a-f]{64}', value['diagnostic_sha256']),
                    'Recorded diagnostic hash is invalid')
            result[value['diagnostic_path']] = value['diagnostic_sha256']
        for nested in value.values():
            merge(nested)
    elif isinstance(value, list):
        for nested in value:
            merge(nested)
    return result


def export(root, output):
    root, output = root.absolute(), output.absolute()
    require(not output.exists() and not output.is_symlink(), 'Use a fresh export directory')
    for parent in output.parents:
        require(not parent.is_symlink(), 'Refuse a symlink export parent')
    output.mkdir(mode=0o700, parents=True)
    manifest = {'status': 'NOT_RUN', 'scope': 'Sanitized timeout bodies only', 'diagnostics': []}
    if root.exists():
        require(root.is_dir() and not root.is_symlink() and root.stat().st_uid == os.getuid(),
                'Refuse a foreign checker root')
        recorded = {}
        report = root / 'regressions.json'
        if report.exists():
            recorded = references(json.loads(regular(report, root)))
        paths = sorted(root.rglob('timeout-*.json'))
        require(len(paths) <= 32, 'Too many timeout diagnostics')
        exported = {}
        for path in paths:
            require(path.parent.name == '.upgrade-checker', 'Unexpected timeout body location')
            data = regular(path, root)
            payload = json.loads(data)
            require(isinstance(payload, dict) and set(payload) == {'stdout', 'stderr'}
                    and all(isinstance(v, str) for v in payload.values()),
                    'Unexpected sanitized timeout body shape')
            digest = hashlib.sha256(data).hexdigest()
            if str(path) in recorded:
                require(recorded[str(path)] == digest, 'Recorded diagnostic hash differs')
            target = output / (digest + '.json')
            if not target.exists():
                with os.fdopen(os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as f:
                    f.write(data)
            exported[str(path)] = digest
            manifest['diagnostics'].append({'source_relative': path.relative_to(root).as_posix(),
                                            'exported_file': target.name, 'sha256': digest,
                                            'bytes': len(data), 'recorded_hash_checked': str(path) in recorded})
        require(all(exported.get(p) == digest for p, digest in recorded.items()),
                'A referenced timeout body was not exported')
        manifest.update(status='PASS', referenced_hashes_verified=len(recorded))
    data = (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode()
    with os.fdopen(os.open(output / 'manifest.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'wb') as f:
        f.write(data)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = export(args.root, args.output)
    print(json.dumps({'status': result['status'], 'diagnostics': len(result['diagnostics'])}))


if __name__ == '__main__':
    main()

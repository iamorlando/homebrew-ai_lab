#!/usr/bin/env python3
"""Bind a clean Homebrew installation to the frozen wheel, sdist and manifest."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import tarfile
import zipfile


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--wheel', type=Path, required=True)
    parser.add_argument('--sdist', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    import ai_lab
    from ai_lab import __version__
    manifest = json.loads(args.manifest.read_text())
    binding = manifest['package_binding']
    require(__version__ == manifest['version'], 'Installed version mismatch')
    require(digest(args.wheel.read_bytes()) == binding['wheel_sha256'], 'Wheel hash mismatch')
    require(digest(args.sdist.read_bytes()) == binding['sdist_sha256'], 'Sdist hash mismatch')
    expected = binding['runtime_sha256']
    site = Path(ai_lab.__file__).resolve().parent.parent
    require(site.is_relative_to(Path(sys.prefix).resolve()), 'Installed import outside candidate environment')
    wheel_files = {}
    with zipfile.ZipFile(args.wheel) as archive:
        for entry in archive.infolist():
            name = entry.filename
            if not name.startswith('ai_lab/') or entry.is_dir():
                continue
            require(not PurePosixPath(name).is_absolute() and '..' not in PurePosixPath(name).parts,
                    'Unsafe wheel member')
            require(name not in wheel_files, 'Duplicate wheel member')
            wheel_files[name] = digest(archive.read(entry))
    require(wheel_files == expected, 'Wheel runtime set or bytes mismatch')
    installed = {}
    for path in (site / 'ai_lab').rglob('*'):
        if not path.is_file() or '__pycache__' in path.parts or path.suffix == '.pyc':
            continue
        require(not path.is_symlink(), 'Unexpected installed package symlink')
        installed[path.relative_to(site).as_posix()] = digest(path.read_bytes())
    require(installed == expected, 'Installed runtime set or bytes mismatch')
    source_files = {}
    with tarfile.open(args.sdist, 'r:gz') as archive:
        for entry in archive:
            if not entry.isfile():
                continue
            name = PurePosixPath(entry.name)
            require(not name.is_absolute() and '..' not in name.parts, 'Unsafe sdist member')
            relative = PurePosixPath(*name.parts[1:]).as_posix()
            require(relative not in source_files, 'Duplicate sdist source member')
            source_files[relative] = digest(archive.extractfile(entry).read())
    require(source_files == binding['sdist_sha256_by_file'], 'Sdist source set or bytes mismatch')
    sources = binding['runtime_sources']
    require(set(sources) == set(expected), 'Incomplete source-to-runtime mapping')
    require(all(source_files[source] == expected[target] for target, source in sources.items()),
            'Sdist application/resources differ from installed wheel')
    report = {'status': 'PASS', 'source_sha': manifest['source_sha'], 'version': __version__,
              'wheel_sha256': binding['wheel_sha256'], 'sdist_sha256': binding['sdist_sha256'],
              'runtime_files': len(installed), 'sdist_source_files': len(source_files),
              'executable': sys.executable, 'environment': sys.prefix,
              'import': str(Path(ai_lab.__file__).resolve())}
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()

"""Collect license notices from Cargo's resolved package sources."""
from pathlib import Path


def collect(metadata):
    chunks = ['Third-party notices for AI Lab\n\nResolved Cargo packages; includes build-time packages.\n']
    for package in sorted(metadata['packages'], key=lambda p: (p['name'], p['version'])):
        chunks.append(f"\n{'=' * 72}\n{package['name']} {package['version']}\n"
                      f"License: {package.get('license')}\nRepository: {package.get('repository')}\n")
        root = Path(package['manifest_path']).parent
        files = []
        if package.get('license_file'):
            files.append(root / package['license_file'])
        for directory in (root, root.parent, root.parent.parent):
            matches = [p for pattern in ('LICENSE*', 'LICENCE*', 'COPYING*', 'NOTICE*')
                       for p in directory.glob(pattern) if p.is_file()]
            if matches:
                files += matches
                break
        for path in sorted(set(files)):
            if path.is_file():
                chunks.append(f'\n--- {path.name} ---\n' + path.read_text(errors='replace'))
    return '\n'.join(chunks)

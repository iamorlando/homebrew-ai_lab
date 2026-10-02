#!/usr/bin/env python3
"""Build and package AI Lab's exact public forks for Apple Silicon consumers."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile


def output(*args, **kwargs):
    return subprocess.check_output(args, text=True, **kwargs).strip()


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', type=Path, required=True)
    parser.add_argument('--checkout', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    sources = json.loads(args.sources.read_text())
    runtime = sources['runtime']
    library = sources['watermark_library']
    checkout = args.checkout.resolve()
    checkout.mkdir(parents=True, exist_ok=True)
    for name, config in (('mistral', runtime), ('llm_watermarking', library)):
        directory = checkout / name
        if not directory.exists():
            subprocess.run(['git', 'clone', config['repository'], str(directory)], check=True)
        if output('git', 'status', '--porcelain', cwd=directory):
            raise RuntimeError(f'Refusing modified sources: {directory}')
        subprocess.run(['git', 'fetch', 'origin', config['commit']], cwd=directory, check=True)
        subprocess.run(['git', 'checkout', '--detach', config['commit']], cwd=directory, check=True)
        assert output('git', 'rev-parse', 'HEAD', cwd=directory) == config['commit']
        assert not output('git', 'status', '--porcelain', cwd=directory)
    env = os.environ.copy()
    env.update(MACOSX_DEPLOYMENT_TARGET='15.0', MISTRALRS_METAL_PRECOMPILE='0',
               CARGO_NET_GIT_FETCH_WITH_CLI='true', RUSTFLAGS='')
    subprocess.run(['rustup', 'toolchain', 'install', runtime['rust_version'], '--profile', 'minimal'], check=True)
    cargo = ['cargo', '+' + runtime['rust_version']]
    subprocess.run([*cargo, 'build', '--locked', '--release', '--package', runtime['package'],
                    '--no-default-features', '--features', ','.join(runtime['features'])],
                   cwd=checkout / 'mistral', env=env, check=True)
    metadata = json.loads(output(*cargo, 'metadata', '--no-deps', '--format-version', '1', cwd=checkout / 'mistral', env=env))
    destination = args.output.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    package = destination / 'package'
    package.mkdir(exist_ok=True)
    binary = package / 'mistralrs'
    shutil.copy2(Path(metadata['target_directory']) / 'release/mistralrs', binary)
    subprocess.run(['strip', '-x', str(binary)], check=True)
    subprocess.run(['codesign', '--force', '--sign', '-', str(binary)], check=True)
    linkage = output('otool', '-L', str(binary))
    for line in linkage.splitlines()[1:]:
        if not line.strip().startswith(('/usr/lib/', '/System/Library/')):
            raise RuntimeError(f'Non-system dynamic dependency: {line}')
    build = {'repository': runtime['repository'], 'commit': runtime['commit'],
             'watermark_library': {'repository': library['repository'], 'commit': library['commit'], 'dirty': False},
             'features': runtime['features'], 'watermark_support': True,
             'binary_sha256': digest(binary), 'version': output(str(binary), '--version'),
             'rustc': output('rustup', 'run', runtime['rust_version'], 'rustc', '--version'),
             'cargo_lock_sha256': digest(checkout / 'mistral/Cargo.lock'),
             'source': {'commit': runtime['commit'], 'dirty': False},
             'platform': 'macos-arm64', 'minimum_macos': '15.0',
             'metal_compilation': 'macOS Metal framework; no developer tools at runtime'}
    (package / 'build.json').write_text(json.dumps(build, indent=2) + '\n')
    for name in ('mistral', 'llm_watermarking'):
        shutil.copy2(checkout / name / 'LICENSE', package / f'LICENSE-{name}')
    archive = destination / 'ai_lab-runtime-macos-arm64.tar.gz'
    with tarfile.open(archive, 'w:gz') as tar:
        for path in sorted(package.iterdir()):
            tar.add(path, arcname=path.name, recursive=False)
    manifest = {**build, 'sha256': digest(archive), 'bytes': archive.stat().st_size, 'filename': archive.name}
    (destination / 'runtime.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Installed-package storage proof using tiny files and an in-memory archive.

Run: /installed/venv/bin/python -I check_storage.py
Or:  python check_storage.py --python /installed/venv/bin/python

Self-contained; no source tests/assets, model starts, real downloads or SDK calls.
Two isolated interpreters prove that unchanged weights reuse private receipts.
"""
import argparse
import asyncio
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
from unittest.mock import patch

DATA = b'tiny installed-package weight fixture'


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def catalog_fixture():
    return {name: {'label': name, 'dependencies': 'fixture runtime', 'files': [
        {'path': f'.models/{name}/fixture.bin', 'bytes': len(DATA),
         'sha256': hashlib.sha256(DATA).hexdigest(), 'url': 'https://example.invalid/weights'}]}
        for name in ('deepseek', 'qwen', 'clm', 'laya')}


def put(root, file, data=DATA):
    target = root / file['path']
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return target


def runtime_fixture(sources):
    binary = b'tiny fake runtime, never executed'
    release = {**sources['runtime'], 'watermark_library': sources['watermark_library'],
               'binary_sha256': hashlib.sha256(binary).hexdigest(), 'minimum_macos': '15.0',
               'version': 'storage-fixture-runtime', 'url': 'https://example.invalid/runtime.tar.gz'}
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode='w:gz') as archive:
        for name, data in [('mistralrs', binary), ('build.json', json.dumps(release).encode()),
                           ('LICENSE-mistral', b'MIT'), ('LICENSE-llm_watermarking', b'MIT'),
                           ('THIRD_PARTY_NOTICES.txt', b'fixture notices')]:
            entry = tarfile.TarInfo(name); entry.size = len(data)
            archive.addfile(entry, io.BytesIO(data))
    data = stream.getvalue()
    return {**release, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}, data


def reuse_proof(base, paths, downloads):
    model = catalog_fixture()['deepseek']
    file = model['files'][0]
    outcomes = []
    for scenario in ('verified', 'wrong-hash', 'ambiguous'):
        home = base / scenario; home.mkdir()
        old = home / 'dev/deepseek'; old.mkdir(parents=True)
        source = put(old, file, DATA if scenario != 'wrong-hash' else b'x' * len(DATA))
        private = old / 'harness/models.json'; private.parent.mkdir(); private.write_bytes(b'private, never copied')
        other = home / 'dev/ai_experiments'
        if scenario == 'ambiguous': put(other, file)
        unrelated = home / 'arbitrary/deep/models'; unrelated.mkdir(parents=True)
        before = source.read_bytes(), private.read_bytes()
        with patch.dict(os.environ, {}, clear=True), patch.object(paths.Path, 'home', return_value=home):
            selected = paths.root_path(); selected.mkdir(parents=True)
            require(paths.root_details(selected)['automatic_reuse'], 'Default installed selection does not allow bounded reuse')
            known = paths.known_model_roots(selected)
            require(old in known and unrelated not in known, 'Root discovery escaped bounded known locations')
            if scenario == 'verified':
                require(downloads.reuse_weights(selected, model) == [file['path']], 'Verified source was not reused')
                require((selected / file['path']).is_symlink(), 'Reuse copied or moved the source instead of attaching')
                require(downloads.reuse_weights(selected, model) == [], 'Reuse is not idempotent')
                require(not (old / '.state').exists(), 'Attachment wrote a receipt into the source root')
                require(not (selected / 'harness/models.json').exists(), 'Attachment merged private profiles')
            else:
                try:
                    downloads.reuse_weights(selected, model)
                except ValueError as error:
                    expected = 'checksum mismatch' if scenario == 'wrong-hash' else 'multiple known roots'
                    require(expected in str(error), 'Reuse rejected the fixture for the wrong reason')
                else:
                    raise RuntimeError('Unsafe reuse scenario did not fail')
                require(not (selected / '.models').exists(), 'Failed reuse created model attachments')
            explicit = home / 'explicit'; paths.root_path(explicit)
            require(downloads.reuse_weights(explicit, model) == [], 'Explicit root silently fell back')
        require((source.read_bytes(), private.read_bytes()) == before, 'Reuse changed source weights or private data')
        outcomes.append(scenario)
    return outcomes


def initialization_boundary_proof(base, paths, downloads, setup):
    from ai_lab import model_servers

    def snapshot(folder):
        return sorted((str(p.relative_to(folder)), p.lstat().st_mode & 0o777,
                       os.readlink(p) if p.is_symlink() else p.read_bytes() if p.is_file() else None)
                      for p in [folder, *folder.rglob('*')])

    outcomes = []
    for relative in ('.state', '.state/ai-lab', 'harness', 'harness/models.json'):
        scenario = base / relative.replace('/', '-').lstrip('.'); scenario.mkdir()
        selected = scenario / 'selected'; selected.mkdir()
        foreign = scenario / 'foreign'; foreign.mkdir(mode=0o755)
        (foreign / 'ai-lab').mkdir(mode=0o755)
        (foreign / 'sentinel').write_bytes(b'foreign bytes must be unchanged')
        file = catalog_fixture()['deepseek']['files'][0]; put(selected, file)
        link = selected / relative; link.parent.mkdir(parents=True, exist_ok=True)
        target = foreign if not relative.endswith('.json') else foreign / 'absent-models.json'
        link.symlink_to(target)
        before = snapshot(foreign), snapshot(selected)
        entries = [lambda: setup.prepare(selected), lambda: setup.repair_generation_runtime(selected, 'deepseek'),
                   lambda: model_servers.ModelServers(selected),
                   lambda: asyncio.run(model_servers.available_models(selected)),
                   lambda: asyncio.run(model_servers.serve(selected, ['deepseek']))]
        if relative.startswith('.state'):
            entries.append(lambda: paths.state_path(selected))
        for entry in entries:
            try:
                entry()
            except ValueError as error:
                require('Custom runtime/source override is preserved' in str(error), 'Initialization failed for the wrong reason')
            else:
                raise RuntimeError('Initialization accepted a foreign managed-path link')
            require((snapshot(foreign), snapshot(selected)) == before,
                    'Rejected initialization changed foreign/selected files, bytes, modes or links')
        outcomes.append(relative)
    return outcomes


def probe(root, phase):
    from ai_lab import downloads, paths, runtime, setup
    import ai_lab
    require(paths.BUNDLE.is_dir(), 'Proof requires an installed wheel with bundled resources, not source/editable imports')
    root = root.resolve()
    package = str(Path(ai_lab.__file__).resolve())
    pins = {name: (Path(ai_lab.__file__).parent / name).read_bytes()
            for name in ('runtime.json', 'decisions-runtime.json', 'model-downloads.json')}
    sources_bytes = (paths.RESOURCES / 'sources.json').read_bytes()
    catalog = catalog_fixture()
    weight_calls = []

    def no_weights(*args, **kwargs):
        weight_calls.append(True)
        raise RuntimeError('A weight-download call occurred')

    with patch.object(downloads, 'catalog', return_value=catalog), \
            patch.object(downloads, 'download_file', side_effect=no_weights), \
            patch('urllib.request.urlopen', side_effect=RuntimeError('Real network is forbidden')), \
            patch('subprocess.run', side_effect=RuntimeError('Compiler/model processes are forbidden')), \
            patch('os.killpg', side_effect=RuntimeError('Process stops are forbidden')):
        if phase == 'initial':
            setup.prepare(root)
            for model in catalog.values(): put(root, model['files'][0])
            sources = json.loads((root / 'sources.json').read_text())
            release, archive = runtime_fixture(sources)
            binary = root / '.runtime/mistral/mistralrs'; binary.parent.mkdir(parents=True)
            binary.write_bytes(b'old fake runtime'); binary.chmod(0o755)
            build_file = root / '.state/mistral-build.json'
            build_file.write_text(json.dumps({**release, 'commit': 'stale-fixture-pin',
                                             'binary': str(binary), 'distribution': 'prebuilt'}))
            generation_ready = downloads.dependencies_ready

            def readiness(root, name):
                return generation_ready(root, name) if name in {'deepseek', 'qwen'} else False

            artifact_calls = []

            def fake_artifact(request, **kwargs):
                require(request.full_url == release['url'], 'Runtime-only repair requested weights or another URL')
                artifact_calls.append(request.full_url)
                return io.BytesIO(archive)

            with patch.object(downloads, 'dependencies_ready', side_effect=readiness), \
                    patch.object(runtime, 'descriptor', return_value=release), \
                    patch.object(runtime, 'supported', return_value=True), \
                    patch.object(downloads, 'install', return_value={'installed': [], 'reason': 'declined'}) as install:
                rows = downloads.status(root)
                require(all(r['weights_present'] and r['missing_bytes'] == 0 and not r['installed'] for r in rows),
                        'Verified weights and stale runtime are conflated')
                require(all('weights verified; runtime setup required' in r['status'] for r in rows), 'Status label is misleading')
                with patch('sys.stdin.isatty', return_value=True):
                    offer = downloads.offer(root)
                install.assert_called_once_with(root, list(catalog), yes=False)
                require(offer['reason'] == 'declined' and offer['installed'] == []
                        and set(offer['runtime_setup_required']) == set(catalog),
                        'Explicit offer must include runtime repairs and preserve unselected repairs')
                with patch('urllib.request.urlopen', side_effect=fake_artifact), \
                        patch('subprocess.check_output', return_value=release['version']):
                    require(setup.repair_generation_runtime(root, 'deepseek')['repaired'], 'Stale runtime did not repair')
                    require(not setup.repair_generation_runtime(root, 'qwen')['repaired'], 'Shared runtime repaired twice')
                require(all(generation_ready(root, family) for family in ('deepseek', 'qwen')), 'Repaired runtime is not ready')
            require(len(artifact_calls) == 1, 'Runtime repair must use exactly one in-memory artifact')
            require(all((root / m['files'][0]['path']).read_bytes() == DATA for m in catalog.values()), 'Runtime repair changed weights')
            reuse_root = root / 'reuse'; reuse_root.mkdir()
            reuse = reuse_proof(reuse_root, paths, downloads)
            boundary_root = root / 'initialization-boundaries'; boundary_root.mkdir()
            boundaries = initialization_boundary_proof(boundary_root, paths, downloads, setup)
            details = {'runtime_fake_artifacts': len(artifact_calls), 'bounded_reuse': reuse,
                       'initialization_boundaries': boundaries, 'foreign_bytes_modes_unchanged': True}
        else:
            with patch.object(downloads, 'dependencies_ready', return_value=False), \
                    patch.object(downloads, 'sha256', side_effect=RuntimeError('Unchanged weights were rehashed in a fresh process')):
                rows = downloads.status(root)
                require(all(r['weights_present'] for r in rows), 'Fresh process failed to reuse private verification receipts')
            file = catalog['deepseek']['files'][0]
            target = root / file['path']; before = target.stat()
            target.write_bytes(b'x' * len(DATA)); os.utime(target, ns=(before.st_atime_ns, before.st_mtime_ns))
            with patch.object(downloads, 'sha256', wraps=runtime.sha256) as digest:
                require(not downloads.verified_present(root, file), 'Same-size edit with restored mtime bypassed hash validation')
                require(digest.call_count == 1, 'Changed scratch weight did not receive a fresh hash check')
            receipt = root / '.state/ai-lab/weight-verification.json'
            require(receipt.stat().st_mode & 0o777 == 0o600, 'Verification receipts are not private')
            details = {'fresh_process_unchanged_weight_hashes': 0, 'modified_weight_hashes': 1, 'wrong_hash_rejected': True}
    require(not weight_calls, 'Weight downloads occurred')
    require(all((Path(ai_lab.__file__).parent / name).read_bytes() == data for name, data in pins.items()), 'Published pins changed')
    require((paths.RESOURCES / 'sources.json').read_bytes() == sources_bytes, 'Bundled source manifest changed')
    return {'phase': phase, 'package': package, 'weight_download_calls': len(weight_calls), **details}


def check(python):
    script = Path(__file__).resolve()
    with tempfile.TemporaryDirectory(prefix='ai-lab-storage-proof-') as directory:
        root = Path(directory).resolve()
        env = {key: os.environ[key] for key in ('PATH', 'LANG', 'LC_ALL', 'TMPDIR') if key in os.environ}
        env.update(HOME=str(root), AI_LAB_ROOT=str(root), DEEPSEEK_ROOT=str(root))
        phases = []
        for phase in ('initial', 'reload'):
            result = subprocess.run([str(python), '-I', str(script), '--probe', str(root), '--phase', phase],
                                    cwd=root, env=env, text=True, capture_output=True, timeout=60)
            require(result.returncode == 0, f'Installed {phase} phase failed: {result.stderr.strip()}')
            phases.append(json.loads(result.stdout))
        return {'status': 'passed', 'scope': 'installed-package scratch storage and in-memory runtime artifact',
                'phases': phases, 'weight_download_calls': 0, 'real_network_requests': 0,
                'model_processes': 0, 'GPU': False, 'SDK_calls': 0, 'published_pins_unchanged': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python', type=Path, default=Path(sys.executable))
    parser.add_argument('--probe', type=Path, help=argparse.SUPPRESS)
    parser.add_argument('--phase', choices=('initial', 'reload'), help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        print(json.dumps(probe(args.probe, args.phase) if args.probe else check(args.python), indent=2))
    except Exception as error:
        print(json.dumps({'status': 'failed', 'error': str(error)}), file=sys.stderr)
        sys.exit(1)

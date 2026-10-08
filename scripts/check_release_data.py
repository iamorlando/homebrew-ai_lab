"""Preserve owned release fixtures across a literal installed-package upgrade.

Run using an installed interpreter with -I outside the source checkout. No native
runtime, model request, download, credential lookup or user data is accessed.
"""
import argparse
import hashlib
import json
from pathlib import Path

from ai_lab.paths import load_backend
from ai_lab.setup import prepare

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('action', choices=('seed', 'verify'))
p.add_argument('--root', type=Path, required=True)
p.add_argument('--record', type=Path, required=True)
p.add_argument('--binding', type=Path)
a = p.parse_args()
root = a.root.resolve()

def digest(path):
    with path.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()

if a.action == 'seed':
    assert not root.exists(), 'Seed needs a new owned root'
    prepare(root); load_backend(root)
    from model_profiles import ModelProfiles, profile_values
    from watermarks import validate_watermark
    registry = ModelProfiles(root)
    registry.save({'retained-release': profile_values('Retained release profile', 42, 'deepseek',
                  validate_watermark({'scheme': 'synthid', 'key': '57' * 32, 'depth': 4}))})
    files = {
        '.state/ai-lab/settings.json': b'{"theme":"dark","release_fixture":true}\n',
        '.state/ai-lab/sessions/retained.json': b'{"messages":[{"role":"user","content":"preserve exactly"}]}\n',
        '.models/owned-release-fixture.bin': b'Owned persistence fixture; not native model weights.\n',
    }
    for name, data in files.items():
        path = root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
    files['harness/models.json'] = (root/'harness/models.json').read_bytes()
    record = {name: dict(sha256=digest(root/name), inode=(root/name).stat().st_ino,
                        size=(root/name).stat().st_size) for name in files}
    a.record.write_text(json.dumps(record, indent=2) + '\n')
else:
    record = json.loads(a.record.read_text())
    for name, expected in record.items():
        path = root / name
        assert digest(path) == expected['sha256'], 'Retained bytes changed: ' + name
        if name.startswith('.models/'):
            assert path.stat().st_ino == expected['inode'], 'Weight fixture identity changed'
    if a.binding:
        import ai_lab
        binding = json.loads(a.binding.read_text())
        package = Path(ai_lab.__file__).resolve().parent
        expected = binding['runtime_sha256']
        actual = {'ai_lab/' + p.relative_to(package).as_posix(): digest(p)
                  for p in package.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
        assert actual == expected, 'Installed payload does not match accepted source/wheel'
print(json.dumps(dict(status='PASS', action=a.action, root=str(root), files=len(record),
                     scope='owned persistence fixture; not native weight reuse', downloads=0, native_starts=0)))

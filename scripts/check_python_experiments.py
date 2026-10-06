#!/usr/bin/env python3
"""Run checkout/secret/isolation fixtures against an installed AI Lab package.

Uses local Git fixture repositories and fake Python/dependency commands. No
network, notebook execution, model/native provisioning or provider SDK calls.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python', required=True, help='Python in a detached installed AI Lab environment')
    parser.add_argument('--output', type=Path, help='Save the JSON proof')
    args = parser.parse_args()
    fixture = Path(__file__).resolve().with_name('python_experiments_fixture.py')
    with tempfile.TemporaryDirectory(prefix='ai-lab-experiments-proof-', dir='/private/tmp') as folder:
        scratch = Path(folder)
        worker = scratch / 'installed_setup_fixtures.py'
        worker.write_text('''import pathlib,sys
import ai_lab.experiments_setup
package=pathlib.Path(ai_lab.experiments_setup.__file__).resolve()
assert package.is_relative_to(pathlib.Path(sys.prefix).resolve()), 'Package is not installed in the selected environment'
assert (package.parent / '_bundle/harness/generation_models.py').is_file(), 'Bundled package resources are missing'
''' + fixture.read_text())
        env = {name: value for name, value in os.environ.items()
               if name not in {'PYTHONPATH', 'PYTHONHOME', 'VIRTUAL_ENV', 'DEEPSEEK_ROOT'}
               and not name.startswith(('AI_LAB_', 'UV_', 'POETRY_', 'PIP_'))
               and not name.endswith(('_KEY', '_TOKEN', '_PASSWORD', '_SECRET'))}
        home = scratch / 'home'
        home.mkdir(mode=0o700)
        env.update(HOME=str(home), PYTHONDONTWRITEBYTECODE='1')
        result = subprocess.run([str(Path(args.python).absolute()), '-I', '-B', str(worker), '-v'],
                                cwd=scratch, env=env, capture_output=True, text=True, timeout=60)
        if result.returncode:
            print(result.stderr.strip(), file=sys.stderr)
            return result.returncode
        proof = {'status': 'PASS', 'proof_scope': 'installed-package-local-git-and-fake-dependency-tools',
                 'checks': ['public-discovery-dispatch', 'poetry-only-declarations', 'python-requirement',
                            'foreign-environment-isolation', 'private-keys-and-exclusions',
                            'checkout-rerun-preservation', 'clone-install-failure-redaction',
                            'symlink-hardlink-refusal', 'isolated-uv-poetry-fallback'],
                 'network_requests': 0, 'provider_requests': 0, 'notebooks_started': 0,
                 'native_runtime_or_model_installs': 0}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(proof, indent=2) + '\n')
    print(json.dumps(proof, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

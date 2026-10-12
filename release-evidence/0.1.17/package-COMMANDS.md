# Exact commands and exit statuses

Final source `83f5ce69046810e664d9686683d50f6db4fca5ca`. Final application artifacts are byte-identical to candidate 217b310. Prior attempts retain their original evidence under `attempt-89f4d680` and `attempt-217b310`; old artifact paths shown in command logs resolve to those retained copies.

## Initial exactsource build, all initial installations

### git-archive

Working directory: `/Users/orlando/dev/deepseek/.worktrees/qwen38-release-0.1.17`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/git-archive.log`.

```sh
git archive --format=tar --output=/private/tmp/ai-lab-qwen38-release-017/source.tar 89f4d6800f7478bd9d3065f85a364a5ff5dd92a4
```

### build-wheel

Working directory: `/private/tmp/ai-lab-qwen38-release-017`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/build-wheel.log`.

```sh
/Users/orlando/.local/bin/uv build --offline --no-python-downloads --python /Users/orlando/dev/deepseek/.venv/bin/python --build-constraints /private/tmp/ai-lab-qwen38-release-017/build-constraints.txt --wheel --out-dir /private/tmp/ai-lab-qwen38-release-017/dist /private/tmp/ai-lab-qwen38-release-017/source
```

### build-sdist

Working directory: `/private/tmp/ai-lab-qwen38-release-017`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/build-sdist.log`.

```sh
/Users/orlando/.local/bin/uv build --offline --no-python-downloads --python /Users/orlando/dev/deepseek/.venv/bin/python --build-constraints /private/tmp/ai-lab-qwen38-release-017/build-constraints.txt --sdist --out-dir /private/tmp/ai-lab-qwen38-release-017/dist /private/tmp/ai-lab-qwen38-release-017/source
```

### build-sdist-wheel

Working directory: `/private/tmp/ai-lab-qwen38-release-017`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/build-sdist-wheel.log`.

```sh
/Users/orlando/.local/bin/uv build --offline --no-python-downloads --python /Users/orlando/dev/deepseek/.venv/bin/python --build-constraints /private/tmp/ai-lab-qwen38-release-017/build-constraints.txt --wheel --out-dir /private/tmp/ai-lab-qwen38-release-017/sdist-wheel /private/tmp/ai-lab-qwen38-release-017/dist/ai_lab-0.1.17.tar.gz
```

### build-prior-published-sdist

Working directory: `/private/tmp/ai-lab-qwen38-release-017`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/build-prior-published-sdist.log`.

```sh
/Users/orlando/.local/bin/uv build --offline --no-python-downloads --python /Users/orlando/dev/deepseek/.venv/bin/python --build-constraints /private/tmp/ai-lab-qwen38-release-017/build-constraints.txt --wheel --out-dir /private/tmp/ai-lab-qwen38-release-017/prior-wheel /private/tmp/textgrain-artifacts-bd2be50/dist/ai_lab-0.1.16.tar.gz
```

### artifact-binding

Working directory: `/private/tmp/ai-lab-qwen38-release-017`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/artifact-binding.log`.

```sh
/Users/orlando/dev/deepseek/.venv/bin/python /private/tmp/ai-lab-qwen38-release-017/verify_artifacts.py
```

### clean-locked-dependencies

Working directory: `/private/tmp/ai-lab-qwen38-release-017`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-locked-dependencies.log`.

```sh
/Users/orlando/.local/bin/uv sync --project /private/tmp/ai-lab-qwen38-release-017/source --locked --offline --no-install-project --no-python-downloads --python /Users/orlando/dev/deepseek/.venv/bin/python
```

### clean-install

Working directory: `/private/tmp/ai-lab-qwen38-release-017`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-install.log`.

```sh
/Users/orlando/.local/bin/uv pip install --offline --no-deps --python /private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python /private/tmp/ai-lab-qwen38-release-017/dist/ai_lab-0.1.17-py3-none-any.whl
```

### clean-version

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-version.log`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/ai-lab --version
```

### clean-installed-probe

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-installed-probe.log`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/installed_probe.py clean
```

### sdist-locked-dependencies

Working directory: `/private/tmp/ai-lab-qwen38-release-017`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/sdist-locked-dependencies.log`.

```sh
/Users/orlando/.local/bin/uv sync --project /private/tmp/ai-lab-qwen38-release-017/source --locked --offline --no-install-project --no-python-downloads --python /Users/orlando/dev/deepseek/.venv/bin/python
```

### sdist-install

Working directory: `/private/tmp/ai-lab-qwen38-release-017`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/sdist-install.log`.

```sh
/Users/orlando/.local/bin/uv pip install --offline --no-deps --python /private/tmp/ai-lab-qwen38-release-017/sdist-env/bin/python /private/tmp/ai-lab-qwen38-release-017/sdist-wheel/ai_lab-0.1.17-py3-none-any.whl
```

### sdist-version

Working directory: `/private/tmp/ai-lab-qwen38-release-017/sdist-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/sdist-version.log`.

```sh
/private/tmp/ai-lab-qwen38-release-017/sdist-env/bin/ai-lab --version
```

### sdist-installed-probe

Working directory: `/private/tmp/ai-lab-qwen38-release-017/sdist-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/sdist-installed-probe.log`.

```sh
/private/tmp/ai-lab-qwen38-release-017/sdist-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/installed_probe.py sdist
```

### upgrade-locked-dependencies

Working directory: `/private/tmp/ai-lab-qwen38-release-017`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-locked-dependencies.log`.

```sh
/Users/orlando/.local/bin/uv sync --project /private/tmp/ai-lab-qwen38-release-017/source --locked --offline --no-install-project --no-python-downloads --python /Users/orlando/dev/deepseek/.venv/bin/python
```

### upgrade-install

Working directory: `/private/tmp/ai-lab-qwen38-release-017`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-install.log`.

```sh
/Users/orlando/.local/bin/uv pip install --offline --no-deps --python /private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python /private/tmp/ai-lab-qwen38-release-017/prior-wheel/ai_lab-0.1.16-py3-none-any.whl
```

### upgrade-version

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-version.log`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/ai-lab --version
```

## Corrected owner-checker exactsource rebuild

### git-archive

Working directory: `/Users/orlando/dev/deepseek/.worktrees/qwen38-release-0.1.17`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/git-archive.log`.

```sh
git archive --format=tar --output=/private/tmp/ai-lab-qwen38-release-017/source.tar 217b310fbb96fd4b89fb6ad5679c477a5c71293b
```

### build-wheel

Working directory: `/private/tmp/ai-lab-qwen38-release-017`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/build-wheel.log`.

```sh
/Users/orlando/.local/bin/uv build --offline --no-python-downloads --python /Users/orlando/dev/deepseek/.venv/bin/python --build-constraints /private/tmp/ai-lab-qwen38-release-017/build-constraints.txt --wheel --out-dir /private/tmp/ai-lab-qwen38-release-017/dist /private/tmp/ai-lab-qwen38-release-017/source
```

### build-sdist

Working directory: `/private/tmp/ai-lab-qwen38-release-017`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/build-sdist.log`.

```sh
/Users/orlando/.local/bin/uv build --offline --no-python-downloads --python /Users/orlando/dev/deepseek/.venv/bin/python --build-constraints /private/tmp/ai-lab-qwen38-release-017/build-constraints.txt --sdist --out-dir /private/tmp/ai-lab-qwen38-release-017/dist /private/tmp/ai-lab-qwen38-release-017/source
```

### build-sdist-wheel

Working directory: `/private/tmp/ai-lab-qwen38-release-017`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/build-sdist-wheel.log`.

```sh
/Users/orlando/.local/bin/uv build --offline --no-python-downloads --python /Users/orlando/dev/deepseek/.venv/bin/python --build-constraints /private/tmp/ai-lab-qwen38-release-017/build-constraints.txt --wheel --out-dir /private/tmp/ai-lab-qwen38-release-017/sdist-wheel /private/tmp/ai-lab-qwen38-release-017/dist/ai_lab-0.1.17.tar.gz
```

### build-prior-published-sdist

Working directory: `/private/tmp/ai-lab-qwen38-release-017`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/build-prior-published-sdist.log`.

```sh
/Users/orlando/.local/bin/uv build --offline --no-python-downloads --python /Users/orlando/dev/deepseek/.venv/bin/python --build-constraints /private/tmp/ai-lab-qwen38-release-017/build-constraints.txt --wheel --out-dir /private/tmp/ai-lab-qwen38-release-017/prior-wheel /private/tmp/textgrain-artifacts-bd2be50/dist/ai_lab-0.1.16.tar.gz
```

### artifact-binding

Working directory: `/private/tmp/ai-lab-qwen38-release-017`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/artifact-binding.log`.

```sh
/Users/orlando/dev/deepseek/.venv/bin/python /private/tmp/ai-lab-qwen38-release-017/verify_artifacts.py
```

## Final tests-only exactsource rebuild

### git-archive

Working directory: `/Users/orlando/dev/deepseek/.worktrees/qwen38-release-0.1.17`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/git-archive.log`.

```sh
git archive --format=tar --output=/private/tmp/ai-lab-qwen38-release-017/source.tar 83f5ce69046810e664d9686683d50f6db4fca5ca
```

### build-wheel

Working directory: `/private/tmp/ai-lab-qwen38-release-017`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/build-wheel.log`.

```sh
/Users/orlando/.local/bin/uv build --offline --no-python-downloads --python /Users/orlando/dev/deepseek/.venv/bin/python --build-constraints /private/tmp/ai-lab-qwen38-release-017/build-constraints.txt --wheel --out-dir /private/tmp/ai-lab-qwen38-release-017/dist /private/tmp/ai-lab-qwen38-release-017/source
```

### build-sdist

Working directory: `/private/tmp/ai-lab-qwen38-release-017`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/build-sdist.log`.

```sh
/Users/orlando/.local/bin/uv build --offline --no-python-downloads --python /Users/orlando/dev/deepseek/.venv/bin/python --build-constraints /private/tmp/ai-lab-qwen38-release-017/build-constraints.txt --sdist --out-dir /private/tmp/ai-lab-qwen38-release-017/dist /private/tmp/ai-lab-qwen38-release-017/source
```

### build-sdist-wheel

Working directory: `/private/tmp/ai-lab-qwen38-release-017`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/build-sdist-wheel.log`.

```sh
/Users/orlando/.local/bin/uv build --offline --no-python-downloads --python /Users/orlando/dev/deepseek/.venv/bin/python --build-constraints /private/tmp/ai-lab-qwen38-release-017/build-constraints.txt --wheel --out-dir /private/tmp/ai-lab-qwen38-release-017/sdist-wheel /private/tmp/ai-lab-qwen38-release-017/dist/ai_lab-0.1.17.tar.gz
```

### build-prior-published-sdist

Working directory: `/private/tmp/ai-lab-qwen38-release-017`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/build-prior-published-sdist.log`.

```sh
/Users/orlando/.local/bin/uv build --offline --no-python-downloads --python /Users/orlando/dev/deepseek/.venv/bin/python --build-constraints /private/tmp/ai-lab-qwen38-release-017/build-constraints.txt --wheel --out-dir /private/tmp/ai-lab-qwen38-release-017/prior-wheel /private/tmp/textgrain-artifacts-bd2be50/dist/ai_lab-0.1.16.tar.gz
```

### artifact-binding

Working directory: `/private/tmp/ai-lab-qwen38-release-017`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/artifact-binding.log`.

```sh
/Users/orlando/dev/deepseek/.venv/bin/python /private/tmp/ai-lab-qwen38-release-017/verify_artifacts.py
```

## Initial retained-owner checker attempt (failure preserved)

### clean-seed-prior-data

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-seed-prior-data.log`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/Users/orlando/.local/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_CACHE_DIR": "/Users/orlando/.cache/uv", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/checkers/check_release_data.py seed --root /private/tmp/ai-lab-qwen38-release-017/clean-retained-data --record /private/tmp/ai-lab-qwen38-release-017/clean-data-before.json
```

### sdist-seed-prior-data

Working directory: `/private/tmp/ai-lab-qwen38-release-017/sdist-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/sdist-seed-prior-data.log`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/sdist-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/sdist-env/bin:/Users/orlando/.local/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_CACHE_DIR": "/Users/orlando/.cache/uv", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/checkers/check_release_data.py seed --root /private/tmp/ai-lab-qwen38-release-017/sdist-retained-data --record /private/tmp/ai-lab-qwen38-release-017/sdist-data-before.json
```

### upgrade-seed-prior-data

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-seed-prior-data.log`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/Users/orlando/.local/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_CACHE_DIR": "/Users/orlando/.cache/uv", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/checkers/check_release_data.py seed --root /private/tmp/ai-lab-qwen38-release-017/upgrade-retained-data --record /private/tmp/ai-lab-qwen38-release-017/upgrade-data-before.json
```

### literal-upgrade-retained-owner

Working directory: `/private/tmp/ai-lab-qwen38-release-017`. Exit status: `1`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/literal-upgrade-retained-owner.log`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/Users/orlando/.local/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_CACHE_DIR": "/Users/orlando/.cache/uv", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/checkers/check_upgrade_web_owner.py --executable /private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/ai-lab --root /private/tmp/ai-lab-qwen38-release-017/upgrade-retained-data --output /private/tmp/ai-lab-qwen38-release-017/upgrade-owner --web-checker /private/tmp/ai-lab-qwen38-release-017/checkers/check_web.py -- /Users/orlando/.local/bin/uv pip install --offline --no-deps --python /private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python /private/tmp/ai-lab-qwen38-release-017/dist/ai_lab-0.1.17-py3-none-any.whl
```

## Corrected literal upgrade and persistence

### owner-locked-dependencies

Working directory: `/private/tmp/ai-lab-qwen38-release-017`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/owner-locked-dependencies.log`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/owner-upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/owner-upgrade-env/bin:/Users/orlando/.local/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_CACHE_DIR": "/Users/orlando/.cache/uv", "UV_OFFLINE": "1", "UV_PROJECT_ENVIRONMENT": "/private/tmp/ai-lab-qwen38-release-017/owner-upgrade-env", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/Users/orlando/.local/bin/uv sync --project /private/tmp/ai-lab-qwen38-release-017/source --locked --offline --no-install-project --no-python-downloads --python /Users/orlando/dev/deepseek/.venv/bin/python
```

### owner-install-published-prior

Working directory: `/private/tmp/ai-lab-qwen38-release-017`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/owner-install-published-prior.log`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/owner-upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/owner-upgrade-env/bin:/Users/orlando/.local/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_CACHE_DIR": "/Users/orlando/.cache/uv", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/Users/orlando/.local/bin/uv pip install --offline --no-deps --python /private/tmp/ai-lab-qwen38-release-017/owner-upgrade-env/bin/python /private/tmp/ai-lab-qwen38-release-017/prior-wheel/ai_lab-0.1.16-py3-none-any.whl
```

### owner-prior-version

Working directory: `/private/tmp/ai-lab-qwen38-release-017`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/owner-prior-version.log`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/owner-upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/owner-upgrade-env/bin:/Users/orlando/.local/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_CACHE_DIR": "/Users/orlando/.cache/uv", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/owner-upgrade-env/bin/ai-lab --version
```

### owner-seed-prior-data

Working directory: `/private/tmp/ai-lab-qwen38-release-017`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/owner-seed-prior-data.log`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/owner-upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/owner-upgrade-env/bin:/Users/orlando/.local/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_CACHE_DIR": "/Users/orlando/.cache/uv", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/owner-upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/checkers/check_release_data.py seed --root /private/tmp/ai-lab-qwen38-release-017/owner-upgrade-retained-data --record /private/tmp/ai-lab-qwen38-release-017/owner-upgrade-data-before.json
```

### owner-literal-upgrade-rerun

Working directory: `/private/tmp/ai-lab-qwen38-release-017`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/owner-literal-upgrade-rerun.log`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/owner-upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/owner-upgrade-env/bin:/Users/orlando/.local/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_CACHE_DIR": "/Users/orlando/.cache/uv", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/owner-upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/checkers/check_upgrade_web_owner.py --executable /private/tmp/ai-lab-qwen38-release-017/owner-upgrade-env/bin/ai-lab --root /private/tmp/ai-lab-qwen38-release-017/owner-upgrade-retained-data --output /private/tmp/ai-lab-qwen38-release-017/upgrade-owner-final --web-checker /private/tmp/ai-lab-qwen38-release-017/checkers/check_web.py -- /Users/orlando/.local/bin/uv pip install --offline --no-deps --python /private/tmp/ai-lab-qwen38-release-017/owner-upgrade-env/bin/python /private/tmp/ai-lab-qwen38-release-017/dist/ai_lab-0.1.17-py3-none-any.whl
```

### owner-verify-retained-data

Working directory: `/private/tmp/ai-lab-qwen38-release-017`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/owner-verify-retained-data.log`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/owner-upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/owner-upgrade-env/bin:/Users/orlando/.local/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_CACHE_DIR": "/Users/orlando/.cache/uv", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/owner-upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/checkers/check_release_data.py verify --root /private/tmp/ai-lab-qwen38-release-017/owner-upgrade-retained-data --record /private/tmp/ai-lab-qwen38-release-017/owner-upgrade-data-before.json --binding /private/tmp/ai-lab-qwen38-release-017/package-binding.json
```

### owner-installed-probe

Working directory: `/private/tmp/ai-lab-qwen38-release-017/owner-upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/owner-installed-probe.log`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/owner-upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/owner-upgrade-env/bin:/Users/orlando/.local/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_CACHE_DIR": "/Users/orlando/.cache/uv", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/owner-upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/installed_probe.py owner-upgrade
```

## Installed release checkers

### upgrade-installed-probe

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-installed-probe.log`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/Users/orlando/.local/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_CACHE_DIR": "/Users/orlando/.cache/uv", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/installed_probe.py upgrade
```

### clean-verify-retained-data

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-verify-retained-data.log`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/Users/orlando/.local/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_CACHE_DIR": "/Users/orlando/.cache/uv", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/checkers/check_release_data.py verify --root /private/tmp/ai-lab-qwen38-release-017/clean-retained-data --record /private/tmp/ai-lab-qwen38-release-017/clean-data-before.json --binding /private/tmp/ai-lab-qwen38-release-017/package-binding.json
```

### clean-cli

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-cli.log`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/Users/orlando/.local/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_CACHE_DIR": "/Users/orlando/.cache/uv", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/checkers/check_cli.py /private/tmp/ai-lab-qwen38-release-017/clean-env/bin/ai-lab --output /private/tmp/ai-lab-qwen38-release-017/clean-cli.json
```

### clean-web

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-web.log`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/Users/orlando/.local/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_CACHE_DIR": "/Users/orlando/.cache/uv", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/checkers/check_web.py /private/tmp/ai-lab-qwen38-release-017/clean-env/bin/ai-lab
```

### clean-web-jev

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-web-jev.log`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/Users/orlando/.local/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_CACHE_DIR": "/Users/orlando/.cache/uv", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/checkers/check_web.py /private/tmp/ai-lab-qwen38-release-017/clean-env/bin/ai-lab --jev-configured
```

### clean-mcp

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-mcp.log`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/Users/orlando/.local/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_CACHE_DIR": "/Users/orlando/.cache/uv", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/checkers/check_mcp.py --executable /private/tmp/ai-lab-qwen38-release-017/clean-env/bin/ai-lab
```

### clean-cross-model

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-cross-model.log`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/Users/orlando/.local/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_CACHE_DIR": "/Users/orlando/.cache/uv", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/checkers/check_cross_model_profiles.py --python /private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python
```

### sdist-verify-retained-data

Working directory: `/private/tmp/ai-lab-qwen38-release-017/sdist-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/sdist-verify-retained-data.log`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/sdist-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/sdist-env/bin:/Users/orlando/.local/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_CACHE_DIR": "/Users/orlando/.cache/uv", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/sdist-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/checkers/check_release_data.py verify --root /private/tmp/ai-lab-qwen38-release-017/sdist-retained-data --record /private/tmp/ai-lab-qwen38-release-017/sdist-data-before.json --binding /private/tmp/ai-lab-qwen38-release-017/package-binding.json
```

### sdist-cli

Working directory: `/private/tmp/ai-lab-qwen38-release-017/sdist-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/sdist-cli.log`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/sdist-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/sdist-env/bin:/Users/orlando/.local/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_CACHE_DIR": "/Users/orlando/.cache/uv", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/sdist-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/checkers/check_cli.py /private/tmp/ai-lab-qwen38-release-017/sdist-env/bin/ai-lab --output /private/tmp/ai-lab-qwen38-release-017/sdist-cli.json
```

### sdist-web

Working directory: `/private/tmp/ai-lab-qwen38-release-017/sdist-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/sdist-web.log`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/sdist-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/sdist-env/bin:/Users/orlando/.local/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_CACHE_DIR": "/Users/orlando/.cache/uv", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/sdist-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/checkers/check_web.py /private/tmp/ai-lab-qwen38-release-017/sdist-env/bin/ai-lab
```

### sdist-web-jev

Working directory: `/private/tmp/ai-lab-qwen38-release-017/sdist-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/sdist-web-jev.log`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/sdist-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/sdist-env/bin:/Users/orlando/.local/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_CACHE_DIR": "/Users/orlando/.cache/uv", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/sdist-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/checkers/check_web.py /private/tmp/ai-lab-qwen38-release-017/sdist-env/bin/ai-lab --jev-configured
```

### sdist-mcp

Working directory: `/private/tmp/ai-lab-qwen38-release-017/sdist-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/sdist-mcp.log`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/sdist-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/sdist-env/bin:/Users/orlando/.local/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_CACHE_DIR": "/Users/orlando/.cache/uv", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/sdist-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/checkers/check_mcp.py --executable /private/tmp/ai-lab-qwen38-release-017/sdist-env/bin/ai-lab
```

### sdist-cross-model

Working directory: `/private/tmp/ai-lab-qwen38-release-017/sdist-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/sdist-cross-model.log`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/sdist-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/sdist-env/bin:/Users/orlando/.local/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_CACHE_DIR": "/Users/orlando/.cache/uv", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/sdist-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/checkers/check_cross_model_profiles.py --python /private/tmp/ai-lab-qwen38-release-017/sdist-env/bin/python
```

### upgrade-verify-retained-data

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-verify-retained-data.log`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/Users/orlando/.local/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_CACHE_DIR": "/Users/orlando/.cache/uv", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/checkers/check_release_data.py verify --root /private/tmp/ai-lab-qwen38-release-017/upgrade-retained-data --record /private/tmp/ai-lab-qwen38-release-017/upgrade-data-before.json --binding /private/tmp/ai-lab-qwen38-release-017/package-binding.json
```

### upgrade-cli

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-cli.log`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/Users/orlando/.local/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_CACHE_DIR": "/Users/orlando/.cache/uv", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/checkers/check_cli.py /private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/ai-lab --output /private/tmp/ai-lab-qwen38-release-017/upgrade-cli.json
```

### upgrade-web

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-web.log`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/Users/orlando/.local/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_CACHE_DIR": "/Users/orlando/.cache/uv", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/checkers/check_web.py /private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/ai-lab
```

### upgrade-web-jev

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-web-jev.log`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/Users/orlando/.local/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_CACHE_DIR": "/Users/orlando/.cache/uv", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/checkers/check_web.py /private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/ai-lab --jev-configured
```

### upgrade-mcp

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-mcp.log`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/Users/orlando/.local/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_CACHE_DIR": "/Users/orlando/.cache/uv", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/checkers/check_mcp.py --executable /private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/ai-lab
```

### upgrade-cross-model

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-cross-model.log`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/Users/orlando/.local/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_CACHE_DIR": "/Users/orlando/.cache/uv", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/checkers/check_cross_model_profiles.py --python /private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python
```

## Installed matrix modules

### clean-tests-ai_lab-test_clm_ownership.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-tests-ai_lab-test_clm_ownership.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_clm_ownership.py
```

### clean-tests-ai_lab-test_coordination.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `1`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-tests-ai_lab-test_coordination.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_coordination.py
```

### clean-tests-ai_lab-test_credentials.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-tests-ai_lab-test_credentials.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_credentials.py
```

### clean-tests-ai_lab-test_decoder_service.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-tests-ai_lab-test_decoder_service.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_decoder_service.py
```

### clean-tests-ai_lab-test_downloads.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-tests-ai_lab-test_downloads.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_downloads.py
```

### clean-tests-ai_lab-test_generation_identity.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-tests-ai_lab-test_generation_identity.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_generation_identity.py
```

### clean-tests-ai_lab-test_generation_launch.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-tests-ai_lab-test_generation_launch.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_generation_launch.py
```

### clean-tests-ai_lab-test_generation_startup_errors.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-tests-ai_lab-test_generation_startup_errors.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_generation_startup_errors.py
```

### clean-tests-ai_lab-test_mcp_client.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-tests-ai_lab-test_mcp_client.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_mcp_client.py
```

### clean-tests-ai_lab-test_mcp_detection.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-tests-ai_lab-test_mcp_detection.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_mcp_detection.py
```

### clean-tests-ai_lab-test_mcp_generation.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-tests-ai_lab-test_mcp_generation.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_mcp_generation.py
```

### clean-tests-ai_lab-test_mcp_install.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-tests-ai_lab-test_mcp_install.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_mcp_install.py
```

### clean-tests-ai_lab-test_mcp_result_semantics.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `1`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-tests-ai_lab-test_mcp_result_semantics.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_mcp_result_semantics.py
```

### clean-tests-ai_lab-test_mcp_startup.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-tests-ai_lab-test_mcp_startup.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_mcp_startup.py
```

### clean-tests-ai_lab-test_mcp_tools.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-tests-ai_lab-test_mcp_tools.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_mcp_tools.py
```

### clean-tests-ai_lab-test_mcp_transport_schema.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-tests-ai_lab-test_mcp_transport_schema.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_mcp_transport_schema.py
```

### clean-tests-ai_lab-test_native_clm.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-tests-ai_lab-test_native_clm.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_native_clm.py
```

### clean-tests-ai_lab-test_runtime.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-tests-ai_lab-test_runtime.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_runtime.py
```

### clean-tests-ai_lab-test_screen_removal.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-tests-ai_lab-test_screen_removal.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_screen_removal.py
```

### clean-tests-ai_lab-test_service.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-tests-ai_lab-test_service.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_service.py
```

### clean-tests-ai_lab-test_service_manager.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-tests-ai_lab-test_service_manager.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_service_manager.py
```

### clean-tests-ai_lab-test_setup.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-tests-ai_lab-test_setup.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_setup.py
```

### clean-tests-ai_lab-test_startup_errors.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-tests-ai_lab-test_startup_errors.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_startup_errors.py
```

### clean-tests-ai_lab-test_storage.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-tests-ai_lab-test_storage.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_storage.py
```

### clean-tests-ai_lab-test_web_only_cli.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-tests-ai_lab-test_web_only_cli.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_web_only_cli.py
```

### clean-tests-ai_lab-test_web_process.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-tests-ai_lab-test_web_process.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_web_process.py
```

### clean-tests-ai_lab-test_web_runtime.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-tests-ai_lab-test_web_runtime.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_web_runtime.py
```

### clean-tests-ai_lab-test_weight_repair.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-tests-ai_lab-test_weight_repair.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_weight_repair.py
```

### clean-harness-tests-test_completion.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-harness-tests-test_completion.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests harness/tests test_completion.py
```

### clean-harness-tests-test_decoder.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-harness-tests-test_decoder.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests harness/tests test_decoder.py
```

### clean-harness-tests-test_detection_lab.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-harness-tests-test_detection_lab.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests harness/tests test_detection_lab.py
```

### clean-harness-tests-test_generation_models.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-harness-tests-test_generation_models.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests harness/tests test_generation_models.py
```

### clean-harness-tests-test_generation_tournament.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-harness-tests-test_generation_tournament.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests harness/tests test_generation_tournament.py
```

### clean-harness-tests-test_models.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-harness-tests-test_models.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests harness/tests test_models.py
```

### clean-harness-tests-test_qwen38_template.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-harness-tests-test_qwen38_template.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests harness/tests test_qwen38_template.py
```

### clean-harness-tests-test_teaching_tournament.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-harness-tests-test_teaching_tournament.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests harness/tests test_teaching_tournament.py
```

### clean-harness-tests-test_textgrain.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-harness-tests-test_textgrain.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests harness/tests test_textgrain.py
```

### clean-harness-tests-test_watermark_scoring.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-harness-tests-test_watermark_scoring.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests harness/tests test_watermark_scoring.py
```

### upgrade-tests-ai_lab-test_clm_ownership.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-tests-ai_lab-test_clm_ownership.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_clm_ownership.py
```

### upgrade-tests-ai_lab-test_coordination.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-tests-ai_lab-test_coordination.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_coordination.py
```

### upgrade-tests-ai_lab-test_credentials.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-tests-ai_lab-test_credentials.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_credentials.py
```

### upgrade-tests-ai_lab-test_decoder_service.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-tests-ai_lab-test_decoder_service.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_decoder_service.py
```

### upgrade-tests-ai_lab-test_downloads.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-tests-ai_lab-test_downloads.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_downloads.py
```

### upgrade-tests-ai_lab-test_generation_identity.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-tests-ai_lab-test_generation_identity.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_generation_identity.py
```

### upgrade-tests-ai_lab-test_generation_launch.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-tests-ai_lab-test_generation_launch.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_generation_launch.py
```

### upgrade-tests-ai_lab-test_generation_startup_errors.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-tests-ai_lab-test_generation_startup_errors.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_generation_startup_errors.py
```

### upgrade-tests-ai_lab-test_mcp_client.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-tests-ai_lab-test_mcp_client.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_mcp_client.py
```

### upgrade-tests-ai_lab-test_mcp_detection.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-tests-ai_lab-test_mcp_detection.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_mcp_detection.py
```

### upgrade-tests-ai_lab-test_mcp_generation.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-tests-ai_lab-test_mcp_generation.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_mcp_generation.py
```

### upgrade-tests-ai_lab-test_mcp_install.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-tests-ai_lab-test_mcp_install.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_mcp_install.py
```

### upgrade-tests-ai_lab-test_mcp_result_semantics.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-tests-ai_lab-test_mcp_result_semantics.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_mcp_result_semantics.py
```

### upgrade-tests-ai_lab-test_mcp_startup.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-tests-ai_lab-test_mcp_startup.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_mcp_startup.py
```

### upgrade-tests-ai_lab-test_mcp_tools.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-tests-ai_lab-test_mcp_tools.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_mcp_tools.py
```

### upgrade-tests-ai_lab-test_mcp_transport_schema.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-tests-ai_lab-test_mcp_transport_schema.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_mcp_transport_schema.py
```

### upgrade-tests-ai_lab-test_native_clm.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-tests-ai_lab-test_native_clm.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_native_clm.py
```

### upgrade-tests-ai_lab-test_runtime.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-tests-ai_lab-test_runtime.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_runtime.py
```

### upgrade-tests-ai_lab-test_screen_removal.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-tests-ai_lab-test_screen_removal.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_screen_removal.py
```

### upgrade-tests-ai_lab-test_service.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-tests-ai_lab-test_service.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_service.py
```

### upgrade-tests-ai_lab-test_service_manager.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-tests-ai_lab-test_service_manager.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_service_manager.py
```

### upgrade-tests-ai_lab-test_setup.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-tests-ai_lab-test_setup.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_setup.py
```

### upgrade-tests-ai_lab-test_startup_errors.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-tests-ai_lab-test_startup_errors.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_startup_errors.py
```

### upgrade-tests-ai_lab-test_storage.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-tests-ai_lab-test_storage.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_storage.py
```

### upgrade-tests-ai_lab-test_web_only_cli.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-tests-ai_lab-test_web_only_cli.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_web_only_cli.py
```

### upgrade-tests-ai_lab-test_web_process.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-tests-ai_lab-test_web_process.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_web_process.py
```

### upgrade-tests-ai_lab-test_web_runtime.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-tests-ai_lab-test_web_runtime.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_web_runtime.py
```

### upgrade-tests-ai_lab-test_weight_repair.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-tests-ai_lab-test_weight_repair.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_weight_repair.py
```

### upgrade-harness-tests-test_completion.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-harness-tests-test_completion.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests harness/tests test_completion.py
```

### upgrade-harness-tests-test_decoder.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-harness-tests-test_decoder.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests harness/tests test_decoder.py
```

### upgrade-harness-tests-test_detection_lab.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-harness-tests-test_detection_lab.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests harness/tests test_detection_lab.py
```

### upgrade-harness-tests-test_generation_models.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-harness-tests-test_generation_models.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests harness/tests test_generation_models.py
```

### upgrade-harness-tests-test_generation_tournament.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-harness-tests-test_generation_tournament.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests harness/tests test_generation_tournament.py
```

### upgrade-harness-tests-test_models.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-harness-tests-test_models.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests harness/tests test_models.py
```

### upgrade-harness-tests-test_qwen38_template.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-harness-tests-test_qwen38_template.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests harness/tests test_qwen38_template.py
```

### upgrade-harness-tests-test_teaching_tournament.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-harness-tests-test_teaching_tournament.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests harness/tests test_teaching_tournament.py
```

### upgrade-harness-tests-test_textgrain.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-harness-tests-test_textgrain.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests harness/tests test_textgrain.py
```

### upgrade-harness-tests-test_watermark_scoring.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/upgrade-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/upgrade-harness-tests-test_watermark_scoring.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/upgrade-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/upgrade-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests harness/tests test_watermark_scoring.py
```

## Corrected/isolated reruns

### clean-rerun-tests-ai_lab-test_coordination.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-rerun-tests-ai_lab-test_coordination.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_coordination.py
```

### clean-rerun-tests-ai_lab-test_mcp_result_semantics.py

Working directory: `/private/tmp/ai-lab-qwen38-release-017/clean-run`. Exit status: `0`. Output: `/private/tmp/ai-lab-qwen38-release-017/logs/clean-rerun-tests-ai_lab-test_mcp_result_semantics.py`.

Sanitized environment: `{"HOME": "/private/tmp/ai-lab-qwen38-release-017/clean-run/home", "LANG": "en_US.UTF-8", "PATH": "/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin", "PYTHONNOUSERSITE": "1", "UV_OFFLINE": "1", "UV_PYTHON_DOWNLOADS": "never"}`.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I /private/tmp/ai-lab-qwen38-release-017/test_entry.py /private/tmp/ai-lab-qwen38-release-017/installed-tests tests/ai_lab test_mcp_result_semantics.py
```

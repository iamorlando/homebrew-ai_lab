# Installed browser validation — AI Lab 0.1.17

Tested source metadata: `217b310fbb96fd4b89fb6ad5679c477a5c71293b`.
Final accepted source: `83f5ce69046810e664d9686683d50f6db4fca5ca`.
Tests began on `89f4d6800f7478bd9d3065f85a364a5ff5dd92a4`; the final change only
corrected a packaging checker/documentation. The package lane rebuilt the final
source and independently rebuilt the sdist wheel. All three wheel bytes match
SHA-256 `962de95352a893e0c0afef603a5e670dffbad98d3ae56ec46057a9bdd579fb60`.
`finalize.py` rechecks every installed module/resource against the final binding.

After browser completion, only `tests/ai_lab/test_mcp_result_semantics.py`
changed from 217b310 to 83f5ce6. The package lane rebuilt that exact final source;
wheel and sdist bytes remained identical. `refresh_binding.py` performed a
metadata-only update using the package lane's `release-binding.json`, checked
the one-file git diff, rehashed both artifacts and all 129 installed files in
each tested environment, and preserved original tested metadata in
`SUMMARY-tested-217b310.json`. No browser check was rerun or relabeled as fresh.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I \
 /private/tmp/qwen017-browser/refresh_binding.py
```

No source edits, CI, model downloads, native runtime, GPU, or hosted requests were
performed in this browser lane. All API responses are owned CPU fixtures.

## Fixture commands

Run from `/private/tmp/qwen017-browser/clean` or `upgrade`, substituting that
installation name below. Every successful command exited 0. The initial clean
fixture sandbox attempt failed with `PermissionError` at bind; its unchanged
approved loopback retry is the accepted run.

```sh
env -i PATH=/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin \
 PYTHONNOUSERSITE=1 AI_LAB_TEXTGRAIN_FIXTURE=1 \
 AI_LAB_DECODER_CODE=/private/tmp/ai-lab-qwen38-release-017/clean-env/lib/python3.13/site-packages \
 /private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I \
 /private/tmp/qwen017-browser/fixtures/decoder_http_fixture.py

env -i PATH=/private/tmp/ai-lab-qwen38-release-017/clean-env/bin:/usr/bin:/bin \
 PYTHONNOUSERSITE=1 /private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I \
 /private/tmp/qwen017-browser/serve_installed.py \
 --executable /private/tmp/ai-lab-qwen38-release-017/clean-env/bin/ai-lab \
 --proof /private/tmp/qwen017-browser/clean/qwen
```

Accepted fixtures/scripts were copied byte-for-byte from the candidate export;
`SUMMARY.json` records each exact-source hash. The additional Qwen and Decoder
error scripts are owned test drivers in this proof directory. They do not edit
or intercept application behavior. The Qwen runner launches the actual installed
`ai-lab web` command with copied `check_web.py` CPU endpoints.

## Browser commands

The Playwright skill was read and `npx` prerequisite checked. The skill wrapper
was used, with named sessions `qwen017-clean` and `qwen017-upgrade`.
`npm_config_offline=true` used cached CLI packages after initial resolution.

```sh
npm_config_offline=true /Users/orlando/.codex/skills/playwright/scripts/playwright_cli.sh \
 --session=qwen017-clean open http://127.0.0.1:62747/completion
npm_config_offline=true /Users/orlando/.codex/skills/playwright/scripts/playwright_cli.sh \
 --session=qwen017-clean snapshot
npm_config_offline=true /Users/orlando/.codex/skills/playwright/scripts/playwright_cli.sh \
 --session=qwen017-clean run-code --filename /private/tmp/qwen017-browser/fixtures/textgrain-browser-completion.js
```

The identical command ran sequentially for `textgrain-browser-states.js`,
`textgrain-browser-profile.js`, and `textgrain-browser-retained.js`. Logs have
their JSON result and the exact executed script. All passed on both installed
environments. The upgraded run is additionally recorded command-by-command in
`upgrade/cli-suite.json` by `run_cli_suite.py`.

Clean Qwen origin: `http://127.0.0.1:63159`.
Upgraded TextGrain origin: `http://127.0.0.1:63290`.
Upgraded Qwen origin: `http://127.0.0.1:63988`.
Second clean Decoder error fixture: `http://127.0.0.1:64738`.
Navigate via `goto ORIGIN/completion` (or `/decoder`), then run the corresponding
`/private/tmp/qwen017-browser/qwen-browser.js` or `decoder-errors.js` with the
same `run-code --filename` command. Both passed in both environments.

`curl --fail --silent ORIGIN/__fixture/status` captured installed import paths,
owned ports, public request observations, and unchanged fixture profiles before
and after the checks. `fixture-errors-status.json` records the second clean
fixture. No keys occur in those status records.

## Cleanup and limitations

Pressing Enter on each fixture runner's owned stdin stopped its fixture servers.
The Qwen runner stopped its own web child with SIGINT and reaped fixture children.
Both named browsers were closed with `playwright-cli --session=NAME close`.
The finalizer verifies all reported ports reject connections and records them in
`SUMMARY.json`; `qwen/cleanup.json` records each CLI fixture's child exits.

```sh
/private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python -I \
 /private/tmp/qwen017-browser/finalize.py
```

Browser fixtures use fresh owned data roots. The upgraded package environment
was literally upgraded from published 0.1.16 to 0.1.17 by the package agent.
Retained user-data upgrade checks and native inference are separate evidence,
not claimed by these browser checks. Desktop Qwen Models and Decoder, and narrow
Decoder screenshots were visually inspected; automated layout checks also pass.

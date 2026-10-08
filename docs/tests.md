# AI Lab 0.1.16 release checks

This matrix describes the web-only release. It replaces the terminal-screen
matrix from 0.1.14. A listed check is a requirement, not an execution result.
Execution reports bind the final source, wheel, sdist and installed files.

This release adds TextGrain configuration, completion traces and Gamma-tail
watermark evidence, and updates the DeepSeek native runtime to the reviewed
TextGrain-capable build. The CLM runtime and dependency versions stay pinned.
GitHub CI is unavailable and explicitly excluded from this release by the
release owner's instruction. Do not dispatch GitHub Actions. Record local
validation and any unavailable Homebrew host prerequisites truthfully.

## Package and upgrade

- Build a wheel and sdist from the clean committed final source. Verify their
  payloads and installed modules against that exact source. Bind the new DeepSeek
  runtime archive/binary to its exact native source and lock; preserve the CLM
  runtime and Python dependency versions.
- Install the wheel and the sdist independently into fresh locked environments.
- Install the actual published 0.1.15 artifact, retain its data root, and upgrade
  that same environment to 0.1.16. Verify literal versions before and after.
- Preserve profiles, watermark keys, sessions and existing weight paths/content.
  No model download is permitted in these checks. Test setup's compatible weight
  reuse and missing/corrupt/runtime-repair paths separately.
- Run installed checks outside the checkout. Verify imports come from the tested
  environment. Render the formula from the accepted archive and check its Ruby
  syntax, three-command assertions and dependency recipe locally. Run actual
  Homebrew clean installation and literal 0.1.15-to-0.1.16 upgrade, retaining the
  same owned data root. Run `brew test iamorlando/ai_lab/ai_lab` on a supported
  local installation. Draft assets may seed an owned
  Homebrew source cache; the unchanged final formula must validate their hashes.

## Supported CLI

- `ai-lab --help`, `--version`, `--json` and `--skill` work; discovery contains
  exactly `web`, `mcp` and `setup`.
- Help and invalid arguments work for every supported action. Removed terminal
  commands are rejected, including chat, completion, decisions, decoder, models,
  services, weights, apis, skills and completions.
- Setup lists downloadable/installed families, installs selected families,
  resumes/reuses compatible files, handles cancellation and supports runtime
  repair without redownloading weights.
- MCP configuration previews do not write user client files. An owned temporary
  install can create/update its entry and real stdio discovery returns the
  supported tool catalog. CLM and Jev are the decision provider choices.
  Fixture tool requests validate routing and key privacy, not model reasoning.

## Website and APIs

Run the copied `packaging/homebrew/check_web.py INSTALLED_AI_LAB` with the
installed interpreter (also `--jev-configured` for synthetic-key discovery).
It launches the actual installed `web` command in an owned root with explicit CPU fixture endpoints and checks:

- root opens Completion; old Comparison/Watermarking routes redirect there;
  navigation offers Completion, Decisions, Decoder and Models;
- package HTML/assets, manifest/icons/service worker load;
- model create/update/delete persists without OpenCode, saved DeepSeek profiles route correctly; standalone Qwen is rejected, with
  legacy profiles and CLM base weights preserved, and decoder discovery does not expose saved keys;
- missing weights produce setup guidance without a download or orphan service;
- second launch reuses the same owned site; Ctrl+C cleans up its web listener.

Use a real browser against the installed app as well as API checks:

- **Completion:** select a model, inspect token probabilities and tournament,
  choose a token/layer and append. Preserve the published page's behavior.
- **Decisions:** CLM/Jev discovery, Ask/Rank controls, examples, result/raw views,
  missing Jev key and request errors. Laya/upstream CLM are not offered or accepted.
- **Decoder:** left/right desktop split and usable narrow layout; left named-model
  selection, prompt, Generate/output; Copy to decoder; right paste/edit/model
  inheritance, scheme/settings/key override, reset, decode and error recovery.
  Switching config must not mutate profiles or leave a stale result authoritative.
  Check sufficient match, below-threshold high confidence, missing key and
  insufficient-token messages independently. Preserve exact copied text.
- **Models:** create/select/update/delete with DeepSeek and
  watermark/no-watermark profiles. Errors remain visible.

## Automatic local APIs

CPU process/HTTP fixtures must exercise eager web startup of both DeepSeek and
native CLM, simultaneous process lifetimes, readiness only after both are ready,
PID reuse across page/model switches and idle periods, and a direct Python CLM
HTTP request while DeepSeek is in use. No switch may stop either API. Verify
owned shutdown only when the web process exits, startup failures with nonzero
exit, stale-owner recovery, and preservation of unrelated/borrowed services.
Explicit fixture endpoints and injected test runtimes must never start native
models. Web startup with missing prerequisites must give setup guidance without
claiming readiness. All terminal screen modules and retired Comparison and
Watermarking assets must be absent, including direct static URLs.

One serialized bounded live lane uses existing verified weights and pinned
prebuilt runtimes. Confirm the website starts both APIs and keeps them up without service
commands, sends genuine requests and cleans up what it owns. Generation/decoder
and CLM request transport are application proof. Model prompt fidelity, reasoning
quality and reliable MCP tool choice are explicitly out of scope; do not repeat
prompts or tune models to improve those results.

## Evidence and publication

Record exact commands, statuses, package/source hashes and cleanup. Keep fixture
and native evidence distinct and retain genuine failures. Review accepted source
independently; reviewers push feature commits, root merges the combined source
and tap release. Commit before every version, use normal non-force pushes, and
publish only the locally checked bytes. Verify public asset URLs and checksums
after publication. Never report an unrun or blocked check as passed.

## TextGrain runtime and web acceptance

The TextGrain contract and runtime target Mistral commit
`edc4950d31f1247ed641176e1cf0c9d8ce4d0274` and watermark library
`af89e9ecdb8f9a9640fd48a331c4cdc2b35e76e1`. Record the supplied archive,
binary, lock, toolchain, features and notices. Verify the actual installed
binary; fixture traces alone are not native acceptance. Preserve SynthID's
tournament implementation, all model weights, profiles, keys and sessions.

Only exact previously shipped source manifests and unchanged official templates
may advance to the new runtime pair. Custom manifests/templates remain intact.
Test migration without process starts/downloads, runtime replacement with zero
weight-download calls, and unchanged weight hashes/inodes. Runtime installation
before publication may serve exact draft archive bytes at the descriptor's
requested URL through a narrowly scoped test transport; all production archive
size/hash/provenance/version checks must run unchanged. Label this evidence
STAGED and verify the final public URL returns identical bytes after publication.

Required CPU feature checks (use a locked project Python environment):

```sh
python -m unittest discover -s harness/tests -p test_textgrain.py -v
python -m unittest discover -s harness/tests -p test_completion.py -q
python -m unittest discover -s harness/tests -p test_generation_tournament.py -q
python -m unittest discover -s harness/tests -p test_teaching_tournament.py -q
python -m unittest discover -s tests/ai_lab -p test_mcp_detection.py -q
node --test harness/tests/*.test.mjs
```

Run Python file groups in separate processes: legacy broad discovery includes
retired-route expectations and cross-workspace module state. Compare any such
failure with the candidate's base; never silently label the broad suite PASS.

Owned browser fixture (no native/GPU/model starts):

```sh
AI_LAB_TEXTGRAIN_FIXTURE=1 python -I harness/tests/decoder_http_fixture.py
mkdir -p output/playwright
# Open the reported loopback origin in an owned Playwright CLI session.
playwright-cli -s=textgrain open http://127.0.0.1:REPORTED_PORT/completion
playwright-cli -s=textgrain snapshot
playwright-cli -s=textgrain run-code --filename harness/tests/textgrain-browser-completion.js
playwright-cli -s=textgrain run-code --filename harness/tests/textgrain-browser-states.js
playwright-cli -s=textgrain run-code --filename harness/tests/textgrain-browser-profile.js
playwright-cli -s=textgrain run-code --filename harness/tests/textgrain-browser-retained.js
playwright-cli -s=textgrain close
```

The retained-view script additionally checks Decisions typed answers, ranking,
keyboard submission, raw/code views and error recovery. Each browser script returns a CPU-fixture result and writes screenshots under
`output/playwright/`. Use a fresh fixture root for the profile-creation check.
Press Enter on the fixture runner's stdin to stop its owned website/API servers;
verify all reported sockets are released. Check the following:

- Models, Completion, Decoder and MCP expose all seven TextGrain settings plus
  its key, with upstream defaults/ranges; no tournament depth/policy leaks.
- Both generation policies route unchanged; capture limits bound diagnostics
  only. Large tables can omit transport without changing solver settings.
- Native token/block alignment, selected column, full-support input/output
  probabilities, row-major costs/coupling, requested/capped/achieved entropy,
  solver status/residuals/iterations, candidate cost/detection scores, and actual
  production block/token CDF draws are retained without private fields.
- Warmup, repeated context, greedy, missing/malformed trace, omitted capture,
  iteration limit and unsatisfied budget never invent transport or a bracket.
- Token inspection/append, keyboard focus, matrix toggle, narrow layout,
  settings staleness/error recovery, saved-profile persistence, generate/copy/
  decode/inheritance/reset, Gamma-tail evidence and short/weak/match outcomes.
- Switching back to SynthID preserves its depth-4 tournament default, actual
  production bracket, winner, token inspection and all existing behavior.

For native acceptance, use a separately granted serialized lane with an owned
TextGrain-capable runtime and existing approved weights. Record actual native
trace and detection evidence for both policies, include a SynthID regression,
and clean up owned processes. CPU fixtures do not satisfy this lane.

## Installed command reference

Copy checkers from the exact candidate to an owned directory outside the checkout.
For each clean wheel, independently built sdist, and literal upgraded installation:

```sh
"$INSTALLED_PYTHON" check_cli.py "$INSTALLED_AI_LAB"
"$INSTALLED_PYTHON" check_web.py "$INSTALLED_AI_LAB"
"$INSTALLED_PYTHON" check_web.py "$INSTALLED_AI_LAB" --jev-configured
"$INSTALLED_PYTHON" check_mcp.py --executable "$INSTALLED_AI_LAB"
# Before installation/upgrade, seed an owned root with the prior interpreter:
"$PRIOR_PYTHON" -I check_release_data.py seed --root "$OWNED_ROOT" --record "$BEFORE_JSON"
# After checks, verify retained files and the accepted installed payload:
"$INSTALLED_PYTHON" -I check_release_data.py verify --root "$OWNED_ROOT" --record "$BEFORE_JSON" --binding "$RELEASE_BINDING"
```

These are the current web-only release checkers (`packaging/check_cli.py`,
`packaging/homebrew/check_web.py`, `packaging/check_mcp.py`, and
`packaging/check_release_data.py`, `packaging/check_upgrade_web_owner.py`). Historical checkers
for retired terminal/service/standalone-Qwen flows do not define the current
command surface. Validate setup migration, downloads/reuse/corruption/cancel/
retry, runtime install, service ownership and eager web lifetime using the
corresponding installed Python test modules and real owned CPU process fixtures.
Run each test module in a separate process to isolate backend workspace state.
Reconcile the three discovered public commands and recursive subcommand help
with `ai_lab.cli.PUBLIC_COMMANDS`; the `--completions bash|zsh|fish` flag must emit valid scripts;
the removed `completions` subcommand must be rejected. Capture errors and missing optional hosted-key behavior.

Run the TextGrain browser scripts against both clean and upgraded installed
code with `AI_LAB_DECODER_CODE` pointing to that installation's site-packages,
using copied fixtures and `-I` outside the checkout. Verify fixture status reports
installed `comparison_app` and `ai_lab.mcp_tools` paths. Also exercise retained
Completion/SynthID, Decoder, Decisions and Models browser flows. Keep original
failed attempts in evidence and require passing corrected reruns.

Before literal upgrade, run the actual prior web CLI with owned CPU providers.
Keep its process and data root while installing the candidate into the same
installation, exercise the retained owner, stop it explicitly, then start the
candidate on the released socket and recheck profiles and provider lifetimes:

```sh
"$PRIOR_PYTHON" -I check_upgrade_web_owner.py --executable "$STABLE_AI_LAB" --root "$OWNED_ROOT" --output "$OWNER_EVIDENCE" --web-checker "$COPIED_WEB_CHECKER" -- UPGRADE_COMMAND_AND_ARGUMENTS
```

The source-installed lane wraps `uv pip install`; the Homebrew lane wraps a
literal `brew upgrade --build-from-source iamorlando/ai_lab/ai_lab`. This checker
performs no native inference and must never use a user-owned running service.

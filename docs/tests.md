# AI Lab 0.1.14 release validation matrix

This is a durable test specification, not an execution report or release PASS.
Final execution uses the accepted combined source and immutable package supplied
by root. The separate shared item 6 builder/reviewer reports are the authority for
current status, source/artifact hashes, results, findings and unavailable inputs.

## Authority, inputs and evidence

The installed `ai-lab --json` discovery and `ai_lab.cli.PUBLIC_COMMANDS` are the
public surface authority. Recursively exercise `--help` for every discovered
command/subcommand, retain the JSON discovery, and reconcile changes against
this matrix. The public commands are exactly `weights`, `models`,
`apis`, `chat`, `decisions`, `completion`, `services`, `decoder`, `skills`, `mcp`,
`completions`, `web`, and `setup-python-experiments`. Hidden compatibility aliases
are additional upgrade checks; their success never substitutes for public paths.

For every row record: case ID, exact source SHA, wheel/sdist SHA-256, installation
kind (clean or upgrade), absolute executable/interpreter, command, terminal size
and keys where relevant, dependency provenance, expected and observed result,
exit status, sanitized evidence path, and cleanup outcome. Use PASS, FAIL,
BLOCKED_INPUT or NOT_RUN; do not mark unavailable native/hosted work SKIP/PASS.
A group with several enumerated variants requires an outcome for each applicable
variant. Optional hosted credentials and uninstalled external clients are not
release prerequisites: test truthful missing-key/unavailable behavior and record
live integration as NOT_RUN with its limitation. Live upstream CLM is explicitly
out of scope for this app patch; no Cargo/native source rebuild is required.

Evidence classes:

- **CLI/CPU**: actual installed console entrypoints, real owned local session API
  processes and persistent files; no model/native start or provider requests.
- **PTY**: actual installed entrypoint in a terminal, keyboard/button actions,
  rendered output and process exit. Headless mounted widget tests supplement it.
- **FIXTURE**: explicit owned HTTP/process/download dependencies or attributed
  recorded native traces. Never label these as new native generation.
- **LIVE**: separately granted, serialized reviewer lane; actual pinned backends,
  bounded generation/decision/detection calls with endpoint/process provenance.
- **HOSTED**: separately granted credentials and request/cost limits. No SDK or
  hosted call is authorized by this matrix alone.

All mutable roots, client configs, skill destinations, caches and processes must
be owned scratch resources. Supply a minimal environment without inherited
provider keys, endpoint overrides, Python paths or Herdr integration. Inject only
synthetic sentinel secrets for redaction checks, and report their absence as a
boolean, never values. Keep native/runtime pins unchanged. Stop only processes
started by the current test; verify PID exit and released sockets. Do not touch
user weights, Cargo targets, credentials, installed client configuration, main,
tags, tap or published assets.

## Package and upgrade gate

| ID | Execution | Required observable result / evidence |
| --- | --- | --- |
| PKG-01 | Root supplies the accepted final feature set, combined SHA, wheel/sdist and hashes; reviewer independently builds that exact source in its own worktree. | Record build commands, dependency lock and package hashes; differences from root bytes are explained. No modified source or uncommitted payload. Root owns publication builds. |
| PKG-02 | Install final wheel into an empty isolated environment; run outside checkout with sanitized environment. | `ai-lab --version` is literally `AI Lab 0.1.14`; console script and `ai-lab-mcp` come from that installation; installed modules/resources do not resolve to checkout. Bundled templates, schemas, UI, pins and notices exist. |
| PKG-03 | Build/install supplied sdist in a separate empty environment. | Same public discovery and bundled resources; repeat CLI/CPU suite against resulting installed executable. Build/install failure is a release blocker. |
| PKG-04 | Independently install actual published **0.1.13** artifact, record hash and literal version; create saved DeepSeek/Qwen profiles, settings and persistent sessions using its CLI/API. | Record pre-upgrade registry/session snapshots and owned tiny weight/runtime sentinel hashes. Relabeling a 0.1.14 environment is not an upgrade. |
| PKG-05 | Upgrade that same environment from 0.1.13 to root's final 0.1.14 package without deleting the data root. | Literal version changes; profiles, seeds, watermark settings, session history, weights and receipts survive. Run the full public matrix again; clean and upgrade outcomes remain separate. |
| PKG-06 | Keep an **actual 0.1.13 owned session API** alive from a separate retained old environment while using the upgraded CLI. | Published 0.1.13 already accepts `model_name`: new Completion picker/name/ID and session calls preserve catalog identity, show failures visibly, retain persistent state and keep the old API unchanged throughout the proof; clean only the verified test-owned helper afterward. Do not relabel this owner model-only. Record both installed versions, PIDs, socket/URL and transcript. A simulated legacy handler is only supplemental. |
| PKG-07 | Stop old owned API; start final owned API using the same data root; reload sessions and models. | Persistence is real across process restarts; no duplicate models or lost settings; all owned PIDs/sockets cleaned. |
| PKG-06b | Separately run a genuinely older model-only session API (owned strict-schema fixture or exact old source). | Use accepted item 3 `67f65fb` behavior: GET the existing owner's session schema before POST, validate the supported model-only shape and exact catalog identity, then send one resolved-ID mutation. No speculative `model_name` POST, no 422 mutation retry. Unsupported schemas, ambiguous catalogs and genuine errors remain visible; provenance stays distinct from published 0.1.13. |
| PKG-08 | Reviewer verifies root's tap/formula/CI/public-asset validation results against the final hashes. | Root supplies this evidence; item 6 does not edit/push/publish these resources or claim it from a wheel install. |

Use isolated package environments and explicit artifact paths. Record the exact
installer command and resolved dependency set; no user/global installation or
implicit update from an index. If a required old artifact, final package, offline dependency or granted backend
is unavailable, list it explicitly as BLOCKED_INPUT. Record a missing shell
separately with root deciding its final gate status; do not install external
clients or require optional credentials merely to complete this matrix. No request to obtain credentials implies authorization to use
them; root must grant the bounded live lane separately.

## Public entrypoints and terminal flows

Each PTY row runs at 120×40 and 80×24; Models delete additionally runs at 50×18.
Inspect visible text and keyboard reachability, not merely process liveness.
Run each applicable row on both clean and upgraded installed packages.

| ID | Public command / actions | Required behavior and evidence |
| --- | --- | --- |
| CLI-01 | Bare `ai-lab`, `--help`, `--version`, `--skill`, `--json`; recursive public `--help` | Exit 0; exact 13-command discovery with no hidden aliases advertised; every public action/choice present; current guide and readable help. New flags/actions fail matrix reconciliation until covered. |
| CLI-02 | Global and command-local `--json`; invalid command/action/choice, missing required arguments, mutually exclusive flags | Machine errors are JSON on stderr with nonzero status; no traceback, native start, writes or accidental TUI. `--root` and `AI_LAB_ROOT` resolve owned roots; paths with spaces work. |
| MOD-01 | `models`; list, create, update, delete `--help`; `models list --json` | Real API inventory and Models screen agree with registry. Built-in rows cannot become accidental saved deletion/create targets. Empty inventory is usable. |
| MOD-02 | `models create --name NAME --underlying-model FAMILY [--seed SEED] [--watermark-file FILE]` | deepseek/qwen plus canonical DeepSeekR1/Qwen3-8B spellings; default/decimal/hex seed; plain and supported watermarks; names with spaces/case/brackets; returned key is persisted, duplicate/ambiguous invalid requests fail without mutation. |
| MOD-03 | `models update ID --underlying-model FAMILY`, `--scheme`, `--watermark-file` | Backend and settings persist across actual API restart; immutable name/seed preserved. Missing updates, invalid fields/scheme and `--scheme none` produce safe visible errors. |
| MOD-04 | `models delete ID`; new `models delete --name NAME` | Actual registry deletion through installed CLI/current and persistent legacy API; unrelated profiles, weights, runtime receipts, session records and model runs survive. Unknown/ambiguous names, built-ins and busy/409 leave registry unchanged. |
| MOD-05 | Bare `models delete` terminal picker; cancel; empty inventory; non-TTY/no-target `--json` | Picker chooses existing saved model; confirm actual deletion and success. Cancel/empty/non-TTY do no writes. Root's accepted item 5 contract supplies final keys. |
| MOD-06 | Models screen: New/Create/Open/Edit/Save/Delete/Refresh/help/Exit | Delete currently highlighted row after opening another row earlier; success/error visible and table refreshed. Button works at 80×24; Ctrl+D at 50×18 while Input focused. Busy deletion preserves registry and UI. Verify disk before/after, not mocked DELETE calls. |
| CPL-01 | Bare `completion` | Opens Completion directly with in-screen model picker; no preceding selector app. Empty inventory explains how to proceed with available selection/model manager, without invisible writes. Picker cancel/switch/error leaves screen alive. |
| CPL-02 | `completion --model ID`, `--name NAME`; picker selection/switch | Correct saved model, backend, seed, watermark and temperature; name matching remains safe and errors useful. Main help and relevant Chat/Completion usage omit “Exact model name”. Unknown/ambiguous selectors visible; no crash or silent fallback. Re-run on persistent old API. |
| CPL-03 | `completion --prompt TEXT`, `--prompt-file FILE`, `--prompt-file -`, `--session-name`, `--scheme`, `--watermark-file`, `--temperature`, `--max-tokens`, `--no-wait`, `--timeout` | Raw whitespace preserved over real API; file/stdin equivalent; proper trace persistence. Bounds (empty/too long prefix, 0/257 tokens, invalid temperature/scheme/file), timeout and missing backend produce controlled errors. FIXTURE transport first; LIVE fresh native trace later. |
| CPL-04 | `completion --session-action create/list/get/wait/stop/append/select`; `--session`, `--revision`, `--step`, `--token-id`, `--layer` | Each action uses actual API and persisted session. Identity/temperature retained on resume; conflicts reject stale revision; captured step/token/layer changes synchronize, append uses selected token, stop settles. Include final layer -1 and unavailable/invalid data without fabricated probabilities. |
| CPL-05 | `completion --view all/chat/tournament/probabilities/tokens --session ID` | Every view attaches to same session. Terminal tabs/buttons work at all sizes; trace, match choice/action, probability and token details render supported data. Saved/resumed and standalone views preserve session. No tournament invented for non-tournament scheme. |
| CPL-06 | Completion screen Run/Append/Stop, match navigation/selection, token selection, probability/layer selection, refresh, help, resize, Exit | Joined keyboard/button sequence with actual API and attributed recorded native fixture; verify selected match/token/action and probabilities against captured trace and persisted selection, logprob presence/absence truthful. Backend failure visible; switch model without exiting; 120×40 → 80×24 → compact → wide resize bounded. |
| CPL-07 | `completion --layout tmux/herdr` with model or existing session; `--launch` | Printed plans quote paths/names/session safely. Plan-only has no topology mutation. Actual pane launch is a separately root-approved disposable layout, never current Herdr layout. All panes attach same session and owned panes clean up. |
| CPL-08 | `completion --schemes`, `--api-schema`, `--api-snapshot`; `--api-call GET/POST/PATCH/DELETE PATH [--body-file FILE/-]` | Bundled discovery works without API start; snapshot and CRUD hit actual owned API; JSON file/stdin preserve payload. Invalid path outside `/api/lab/` rejected. No service/native launch for informational schema/schemes. |
| CPL-09 | `completion --service-action status/start/stop/run` | Actual private CPU session helper: stopped status, owned start/health, reuse PID, foreground run, stop and restart persistence. Foreground SIGINT/termination cleanup; website-owned helper not wrongly stopped. This is not backend/native services proof. |
| CHAT-01 | Bare `chat`; `--model deepseek/qwen/ID`, `--name NAME`, picker cancel/empty/switch | Actual terminal selection and agent entrypoint; saved profile inheritance preserved. Invalid/ambiguous choice/backend unavailable displays controlled error. No model starts from opening UI. |
| CHAT-02 | `chat` conversation Send/Stop/Exit, multiline, second turn, seed/temperature/scheme/watermark/session-name/max-tokens/timeout | Two bounded conversation turns on each generation backend; transcript/history and cancellation verified. FIXTURE HTTP proof followed by LIVE pinned DeepSeek/Qwen proof. Unsaved overrides do not mutate profiles. |
| CHAT-03 | `chat --self-mcp`; `--mcp-config FILE`; `--tool-choice auto/required`; `--allow-tool TOOL`; Ctrl+T | Actual own stdio MCP discovery → native-wire tool call → visible Allow/Deny → real owned tool result → assistant continuation; denial, timeout, tool error and cancellation recover. Required mode each turn, runtime mode change and own exact-tool preauthorization checked. FIXTURE first, bounded LIVE later; no silent approval bypass. |
| CHAT-04 | `chat --pane PANE --prompt TEXT/--prompt-file FILE/- [--session-id ID] [--wait] [--timeout]`; `--herdr-tab` | Validation/error paths safe offline; actual targeting/stale identity/activity/approval wait and separate tab creation need root's disposable Herdr grant. Preserve current layout. Hidden `agent`/`agent-prompt` compatibility only supplemental. |
| DEC-01 | `decisions`, `--model contrastive/clm-upstream/laya/jev/discovery-label`, `--mode ask/rank` | Actual PTY opens intended in-scope provider/mode; provider refresh; upstream label is parser/discovery coverage only (no live request); unavailable/local versus hosted status truthful; no implicit start/SDK call. Reject non-TTY/JSON gracefully. |
| DEC-02 | Decisions question controls: noul/choice/score, rank options, add/remove, Run/Cancel/refresh, request/response/snippet tabs, copy/import/export/result save | Actual UI → owned HTTP fixture with typed bodies/result; invalid/malformed/empty/timeout/cancel errors visible. Distinguish draft from submitted evidence, sanitized key handling. Repeat native CLM and Laya in LIVE lane; hosted missing-key/unavailable behavior is required, optional actual hosted integration needs a separate grant. Live upstream CLM is excluded. |
| DCR-01 | `decoder`, `decoder --name NAME`, picker/reload/restore profile | Real terminal profile selection uses supported saved generation model; no name/seed/backend mutation; unavailable/unsupported/ambiguous selection visible; interactive-only errors clear. |
| DCR-02 | Decoder paste/edit text, scheme/known key/settings/threshold controls, Decode/Cancel/reload, request/result tabs, copy/export, Exit | Empty/invalid text/settings rejected; detection request maps selected DeepSeek/Qwen profile; match/no-match/insufficient verdicts and score/logprob availability truthful. Owned fixture evidence then LIVE known-key generated-text detection; exported evidence redacts key. |
| WGT-01 | `weights`, `weights --json`, `weights list [--json]`, `weights --doctor` | Downloaded/available inventory and runtime repair status independent; source/base provenance available. Opening/refresh/doctor do not download/hash GBs or start APIs; JSON and TUI agree. |
| WGT-02 | `weights install` default/all and each deepseek/qwen/clm/laya; `--yes`; `weights offer [--yes]`; picker selection/cancel | Tiny owned download fixtures exercise checksums, progress, interrupted/resumed partial files, dependency install, idempotent receipts, corrupt/missing weights and rejection. No real model download. Explicitly grant a real download separately if needed. |
| WGT-03 | `weights --setup --yes --no-models`, `--with-models`, `--use-local-source`, `--build-from-source`; Download/repair button | Owned inert runtime archive fixture proves repair with verified weight bytes unchanged, cancellation/retry and safe custom links. Source-build flags parser/plan guarded here; actual source compilation is excluded for this app patch; no Cargo invocation. Runtime download/repair uses inert archive fixtures and accepted item evidence. |
| API-01 | `apis`, `apis --json`; refresh/Exit | Informational connection/provider inventory, env names/configured booleans only; no API health request, native start or SDK import side effect. Synthetic keys and credential-bearing URLs absent from stdout/stderr/UI/export. |
| SVC-01 | `services`, `services --action list [--json]`, `--name NAME`, `--model deepseek/qwen/contrastive/laya/jev` | One backend row/process per family regardless of saved model count; exact selection maps correctly; known foreign/current/prior-root ownership status truthful; opening has no starts. |
| SVC-02 | `services --action start/stop/restart/interrupt` for each local backend, via name and model; corresponding buttons; refresh/logs/Exit | CPU process fixtures exercise every action and foreground cleanup. LIVE lane proves bounded actual DeepSeek/Qwen/native CLM/Laya; Start/Restart no duplicates, Stop/Interrupt stop genuine managed API, Exit preserves externally owned service. Jev is informational and cannot become local process. |
| SVC-03 | Old CLM listener without receipt; prior-data-root registration; foreign/custom listener; stale/PID-reused receipt; rapid cancellation | Item 1 installed ownership guards plus attributed existing checkpoint; serialized LIVE reproduction of managed legacy adoption/restart/stop. Never kill unrelated Laya or unverified foreign processes. Before/after identities and receipts required. |
| SKL-01 | `skills install --agent codex/claude --scope project/user`; explicit `--project`, `--path`, `--force` | All 2×2 target/scope pairs in private paths; actual CLI creates shipped SKILL.md with metadata and canonical guide. Reinstall unchanged, conflicting file preserved, explicit force replaces only target. Invalid args/symlink/hardlink hazards fail unchanged; no real client config. |
| MCP-01 | `mcp config` and `mcp install`, each `--codex/--claude/--claude-desktop/--cursor/--opencode`, user/project scope, explicit config-file/package/force | Actual CLI for all 5×2×2 variants (including documented unsupported scopes as safe errors). Config preview no writes; install uses private target, preserves unrelated settings, handles identical/conflicting/forced entry, private package snapshot/explicit package correctly. Never edit user's config. |
| MCP-02 | `mcp serve` and installed `ai-lab-mcp`; client-launched generated config | Real initialize/initialized/tools-list/tools-call/close over stdio; stdout JSON-RPC only; local tools and schema failures checked. Fixture generation/detection/decisions labelled; no implicit local native start. Wheel/sdist private snapshot matches supplied package. An uninstalled external client is an honest optional integration limit, not a release blocker; own stdio transport remains required. |
| SH-01 | `completions bash`, `completions zsh`, `completions fish` | Generate from actual installed CLI, run syntax checker in each real shell, source and trigger root/subcommand/flag/model-name/session/scheme/location completions. Correct quoting of spaces/brackets/case, no secret/silent service start; names only offered for supported selection/delete contexts. Record any missing shell as unavailable; root decides the final gate disposition. |
| SH-02 | Dynamic completion with no API, active current API and persistent old API; `--root PATH` / `--root=PATH` | Root forwarded correctly; no daemon launched when unavailable, stale service errors quiet; hidden `_complete` produces only expected values. Models create name never gets selection suggestions. Bash/zsh/fish each checked. |
| WEB-01 | `web --no-setup --no-browser --port PORT [--json]`; root with spaces | Actual installed process serves completion/models/decoder/decisions pages, assets, schema and CRUD; existing process reuse, clear URL, occupied-port error, Ctrl+C and owned helper cleanup verified. No native start. |
| WEB-02 | `web --browser`, default app launch; `--no-models`, `--with-models --yes`, setup cancellation/failure | Browser/app command invocation uses owned launcher fixture first; actual visible browser launch and real setup/download require explicit root grant. Saved data survives. Do not infer visible launch from HTTP 200. |
| EXP-01 | `setup-python-experiments --location PATH [--json]` | Actual CLI with local Git/tool fixtures: fresh/reused verified checkout, spaces, origin validation, isolated project .venv, Poetry and uv fallback, dependency failure/retry/cancel, foreign environment untouched. Existing notebook files preserved. |
| EXP-02 | Experiments existing .env/comments/empty values, missing/available synthetic keys, permissions, tracked private files/symlinks/hardlinks, secret-bearing failure output | Synthetic key addition only to private untracked .env; existing values/comments preserved; permissions/private excludes correct; logs/JSON/errors never leak sentinel values. No real key reads or prints. |
| EXP-03 | Actual experiments checkout/environment and notebook smoke from accepted commit | Separate root-approved network/dependency inputs; verify notebook kernel uses checkout .venv and relative/env lookup from notebook working directory. Execute only explicitly selected CPU/offline notebook cells. Model/SDK/hosted cells remain blocked without separate grant. Never equate fake dependency install with functioning notebook environment. |

## Existing checkers and their limits

Run from detached scratch directories with the final installed Python. Re-read
checker CLI help on the accepted combined SHA before execution because item
owners may add flags. Capture stdout/stderr, exit status and generated evidence.
These commands do not grant native/network work. Use the exact `python`,
`executable`, `wheel` and `sdist` paths recorded for each install kind.

| Checker | Invocation arguments after script | Actual scope / remaining gate |
| --- | --- | --- |
| `packaging/check_upgrade.py` | `--phase before/after/cleanup --root ROOT --state STATE` (details below) | Actual old installed API survives external upgrade; profile/session settings and tiny file-preservation mechanics. No Homebrew execution, package installation, native/model or SDK proof inside checker. |
| `packaging/check_cli.py` | `--executable EXE --expected-version 0.1.14 --source-sha SHA --output FILE` | Public subprocess discovery, actual private CPU API CRUD/session lifecycle, install/config paths and PTY entrypoint smoke. Reports its bounded coverage; detailed feature and LIVE rows remain separate. |
| `packaging/check_checker_failures.py` | `--old-executable OLD --executable NEW --source-sha SHA --output-directory NEW_DIRECTORY` | Actual owned CPU owner-crash and timeout regressions, foreign/replaced socket guards, primary/cleanup error separation, and positive retained-owner phases. Supplemental checker reliability evidence; no Homebrew/native proof. |
| `packaging/check_completion.py` (item 3/4) | `--installed --report FILE --evidence DIRECTORY` | Joined public Completion/current/legacy API, picker and original dog recording (`completion-native-fixture.json`); require actual old installed API in PKG-06 as well. |
| `packaging/check_completion_views.py` (item 4) | `--installed --report FILE --evidence DIRECTORY` | Joined/standalone views, match/draw/token choice, step/layer controls, scheme-specific availability and Stop persistence at wide/compact sizes. Keep adjacent `check_completion.py`, `completion-views-fixture.json` and the distinct original dog `completion-native-fixture.json`; historical replay is not fresh generation. |
| Item 5 accepted deletion checker/tests | Read handoff and exact checker `--help` | Actual public picker and Models deletion/current-highlight/busy persistence; fixture-only tests do not close native state preservation alone. |
| `packaging/check_cross_model_profiles.py` | `--python PYTHON` | Owned synthetic HTTP trace/profile inheritance, reload and rejection; no watermark efficacy claim. |
| `packaging/check_cross_model_chat.py` | `--python PYTHON` (plus explicit `--required-only` run) | Real own MCP/HTTP fixture, saved-profile inheritance and required-mode UI/wire; no native inference. |
| `packaging/check_agent.py` | `--wheel WHEEL --sdist SDIST` | Extracted package mounted Agent UI/wire/own MCP fixture; installed PTY and LIVE still required. |
| `packaging/check_decisions.py` | `--wheel WHEEL --sdist SDIST` | Extracted package mounted Decisions/loopback fixture; no public entrypoint or real provider proof alone. |
| `packaging/check_decoder.py` | `--wheel WHEEL --sdist SDIST --installed` | Installed module/terminal/shared-route MockTransport evidence; no real detector HTTP/native proof. |
| `packaging/check_api_skills.py` | `--python PYTHON --canonical --output FILE` | Canonical installed informational/skill/redaction safety fixtures; actual entrypoints covered separately. |
| `packaging/check_services.py` | `--evidence DIRECTORY` | Installed module/mounted UI with fake APIs/processes; actual public lifecycle and native ownership need separate evidence. |
| `packaging/check_storage.py` | `--python PYTHON` | Tiny files, inert archive, cross-interpreter receipt reuse; no real download/native repair proof. |
| `packaging/check_mcp.py` | `--executable EXE` | Actual packaged own stdio tools plus loopback generation fixtures. |
| `packaging/check_mcp_client.py` | `--wheel WHEEL --sdist SDIST --installed` | Real MCP connector and local HTTP fixture, installed bytes verified. |
| `packaging/homebrew/check_web.py` | `EXE` (optional synthetic `--jev-configured`) | Real installed web pages/assets/CRUD/reuse/cleanup. Do not supply `--laya-source` before native grant. |
| `packaging/check_python_experiments.py` | `--python PYTHON --output FILE` | Local Git plus fake Python/dependency command fixtures; does not execute notebooks or prove installed dependencies. |

Run accepted item-specific regression suites as supporting guards, recording
exact counts. Do not replace terminal/API evidence with import/unit assertions.
Reconcile new actions/flags discovered in the final package before signing off.

The generation-model test module must distinguish a shared native `default`
alias from explicitly named CPU fixture endpoints. Exercise actual
`WatermarkRuntime.ensure_server` for both families with no owned receipt and a
valid mocked completion/trace response, guarding against native start/stop.
Wrong aliases and empty health must stop after the health GET; explicit fixtures
must still reject `default` and the opposite fixture family. Error assertions
use `services --action start --model FAMILY`. Run
`harness/tests/test_generation_models.py` with the native chat, generation launch
and MCP generation test modules; these are HTTP/ownership fixtures, not native
generation evidence.

Keep `check_cli.py` and its sibling `check_upgrade.py` together; they share the
stdlib ownership/transport helpers. CLI/PTY children use an explicit owned
forwarding endpoint, so owner death cannot auto-start a replacement. The public
stop command alone uses direct Unix discovery (`start=False`, then one shutdown
POST). Record any unexpected owner exit as FAIL even when cleanup succeeds,
including an exit with code zero before checker shutdown begins. Record whether
the owner was live on entry and the checker initiated shutdown; an already-exited
owner cannot satisfy the required public stop case. Test this with a separate
unmodified public stop command, for both public-stop and signal-cleanup modes. Failed
CLI runs retain their private scratch/logs, and their 0600 JSON report identifies
that directory. Scratch removal follows verified cleanup and report persistence.
API shutdown waits 10 seconds, then 5 seconds after SIGTERM and 5 after SIGKILL;
each signal requires renewed exact process and available socket attestation.
Test a real SIGSTOP owner, verify bounded final termination and original stale
socket cleanup, and refuse a changed identity before the final signal. Cleanup
attempts record their signals, timeouts, exit/socket outcome and any failure,
including attempts that must retain unverified resources.
Both checkers record timeouts as failed cases with command, duration and timeout;
CLI reports include sanitized partial output, while upgrade reports point to a
private sanitized diagnostic file. Neither traceback nor raw timeout output is
printed to shared logs. The five-second readiness probe also records sanitized
partial output before its owned API is cleaned. Every launched PTY records its sanitized partial
transcript, terminal size, keys, elapsed time, timeout stages and child exit from
`finally`, even when termination raises. Preserve primary and cleanup errors
separately. Test a real SIGTERM-ignoring child and a declared final-signal failure
fixture; recover only the harness-owned child afterward.

Run `check_checker_failures.py` in the candidate upgrade job, where the retained
old physical `Cellar/.../libexec/venv/bin/ai-lab` and the new installed 0.1.14
entrypoint both exist. The clean job has no 0.1.13 input and does not run this
two-version regression. Pass those exact absolute paths as `--old-executable`
and `--executable`, the candidate source SHA as `--source-sha`, and a new short
private directory as `--output-directory` (for example `/private/tmp/i6-faults`).
Keep adjacent `check_cli.py` and `check_upgrade.py`; no additional fixture files
are required. It uses only stdlib support and generates its own inert fixtures.
`ps`, `lsof`, loopback/Unix sockets and permission to signal its own children are
required; it installs nothing. Allow several minutes for real 40/35-second
timeout probes, stopped-owner shutdown and hung-PTY probes, multiple actual
BEFORE phases, AFTER and idempotent CLEANUP.
Each BEFORE/AFTER/CLEANUP sequence has a separate owned root/state and report;
the suite never reuses the candidate job's persistent upgrade root/state. It
intentionally kills only attested test owners, verifies rejected replacement/
foreign identities, then invokes explicit cleanup with the original receipts.
It retains failed and successful evidence. Its phase context is explicitly
`isolated-env`: checker regression proof is separate from the job's literal
same-install Homebrew transaction, even when it uses installed keg executables.

## Retained-owner upgrade checker: CI contract

Run the checker by absolute path from `RUNNER_TEMP` (or another detached directory).
Its `--phase before`, `--phase after` and `--phase cleanup` interface is stable for
CI. The before phase defaults to `--context homebrew`; the supplemental two-venv
exercise must explicitly use `--context isolated-env` and is never a literal
Homebrew-upgrade result. No installation or `brew` command exists in this checker.

The root/CI job owns the actual same-install `brew upgrade` between phases,
retention of the old keg/Python/dependencies, old/new brew receipts, and binding
of source and immutable artifacts. The pinned published 0.1.13 sdist SHA-256 is
`9f679b5b5a9cc2f28128a885457eaee2ad54c8a4281762ab62b595d5a7bd673b`.
Record it with root's old package/receipt evidence; do not mistake a checker
wheel/environment test for validation of that sdist or Homebrew transaction.

Create a short private scratch directory (0700) with a new empty child data root.
Keep state/output JSON outside that root in an owned parent that is not writable
by other users; the files themselves are created as 0600. Data/state paths
must be absolute and canonical; the checker allows the system `/tmp` alias but
refuses user-controlled links, reused state, nonempty roots, linked state files,
foreign owners and substituted PIDs. A short root keeps the Unix socket under
100 bytes and inside the owned root. Use fresh report filenames.

```sh
# Root sets these to approved absolute paths and records package/receipt hashes.
# OLD_EXE is the retained versioned Cellar/.../libexec/venv/bin/ai-lab itself,
# never an opt/bin link that brew upgrade can retarget.
python3 "$CHECKER" --phase before --executable "$OLD_EXE" \
  --root "$UPGRADE_ROOT" --state "$UPGRADE_STATE"

# Root/CI performs and records the actual same-install brew upgrade here.
# Keep the old keg and its interpreter/dependencies intact until proof completes.

python3 "$CHECKER" --phase after --executable "$NEW_EXE" \
  --root "$UPGRADE_ROOT" --state "$UPGRADE_STATE" \
  --source-sha "$FINAL_SOURCE_SHA" --output "$UPGRADE_REPORT"

# Invoke from CI's failure/finally cleanup as well; no executable is required.
python3 "$CHECKER" --phase cleanup \
  --root "$UPGRADE_ROOT" --state "$UPGRADE_STATE"
```

BEFORE verifies literal `AI Lab 0.1.13`, requires a stable installed entrypoint,
starts one actual old CPU session API, and records PID, start identity, command,
UID, process group, socket inode, executable/package hashes and version. Public
old CLI calls create saved DeepSeek/Qwen profiles with synthetic watermark
settings, different seeds, and persistent sessions selected by name and ID.
Tiny inert `.models/upgrade-checker` and `.runtime/upgrade-checker` files have
explicit mechanics-only hash receipts. They are never advertised as valid native
models or executables. File hashes, size, permissions, ownership, inode and mtime
are snapshotted, together with actual saved state and pinned resource files.

AFTER verifies literal `AI Lab 0.1.14` and the unchanged old owner/package/socket
before any data mutation. Homebrew context additionally requires versioned
0.1.13 and 0.1.14 kegs of the same Cellar/formula. It queries the old saved state,
updates one profile setting explicitly, creates a new saved profile and switches
CLI selections by creating separate sessions using name/ID. Existing sessions
retain their original profiles/settings; retargeting an existing session is
rejected. This is CLI/API session routing proof, not a Completion picker UI test.
The checker checks on-disk state and unchanged sentinel bytes/metadata, then
stops only its verified old helper and asserts the process and socket are gone.

A short-lived owned loopback bridge forwards real requests/responses to the old
Unix socket; it returns no synthetic success data. Supplying `AI_LAB_SERVER` to
CLI children disables automatic helper startup, so an exited/replaced owner
fails rather than silently starting 0.1.14. Ownership is checked around every
request; no old API is restarted to pass. The bridge forbids generation routes.
All child environments omit inherited keys, provider endpoints and Herdr state;
reports store output hashes and private diagnostic paths, never raw profile keys
or dependency diagnostics. Timeout diagnostic files are 0600 and redact the
checker-generated synthetic watermark keys.

AFTER attempts cleanup on failure when ownership remains proven. Explicit
CLEANUP also handles a retained helper when the external upgrade/job failed and
is idempotent once cleanup completed. It never signals an unverified/reused PID
or unlinks a foreign/replaced socket. If the original owner has died, CLEANUP can
remove its exact recorded stale socket only after validating the original
receipts, socket dev/inode/UID, PID absence, no live socket holder and a refused
connection. Recheck PID/socket identity immediately before unlinking. A changed
identity or inconclusive inspection fails closed and retains evidence. AFTER
keeps its primary failure in `error` and any independent cleanup failure in
`cleanup_error`; cleanup success never turns a failed proof into PASS.
Keep the original state/ownership receipts
for cleanup; copying or editing them is not a supported recovery procedure.
Exit 0 means only the requested bounded phase passed; neither it nor the report
claims the whole release gate or verifies the external Homebrew transaction.

The fish guard can be run against the actual installed `/opt/homebrew/bin/fish`;
generation alone is insufficient. Syntax check, sourcing and root completion
must pass without workspace mutation. This does not authorize dependency repair.

## Serialized native and external-input request to root

Root must supply final source/artifacts and accepted item contracts first. Then
assign **one reviewer lane** with an explicit time window, owned root, allowed
pinned model paths, endpoint/port/PID ownership, maximum tokens and call counts.
Request DeepSeek and Qwen bounded Chat, Completion trace/session/view
and Decoder checks; native CLM and Laya ask/rank and lifecycle checks; own MCP
tool-call/approval/continuation in the same lane. Judge functioning transport/generation, correct model routing, persistence and
truthful trace/detector output, without requiring exact factual reasoning or
repeated prompt trials. Detector results may legitimately be insufficient;
report that result honestly without inventing a positive detection. Record exact model/runtime hashes and actual outputs.

Separately request: 0.1.13 artifacts/dependencies and retained old API environment;
real bash/zsh/fish; any disposable Herdr/tmux launch surface; browser launch;
experiments checkout/dependencies and permitted CPU notebook cells. Live upstream CLM is excluded.
Jev/hosted SDK integrations are optional and need separate explicit grants; test
missing-key behavior and disclose unavailable live integration without treating
optional credentials or external-client installations as release blockers. Existing live checkpoint
reports may be cited with original SHA/date/provenance but are not fresh proof
of the combined release.

Root merges/publishes only after the final combined gate and independent reviewer
report. Item 6 builder never pushes or marks the full release PASS. Builder/reviewer
reports identify exact committed source, clean-worktree status, commands/results
and remaining limits; publication authority stays with root.

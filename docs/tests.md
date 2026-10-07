# AI Lab 0.1.15 release checks

This matrix describes the web-only release. It replaces the terminal-screen
matrix from 0.1.14. A listed check is a requirement, not an execution result.
Execution reports bind the final source, wheel, sdist and installed files.

The release owner explicitly requires local verification and no GitHub CI run
for this release. Hosted CI is future work. The host's Homebrew/Command Line
Tools incompatibility was previously waived; local package and formula-recipe
checks must not be described as a physical Homebrew install.

## Package and upgrade

- Build a wheel and sdist from the clean committed final source. Verify their
  payloads and installed modules against that exact source; keep native pins and
  dependency versions unchanged.
- Install the wheel and the sdist independently into fresh locked environments.
- Install the actual published 0.1.14 artifact, retain its data root, and upgrade
  that same environment to 0.1.15. Verify literal versions before and after.
- Preserve profiles, watermark keys, sessions and existing weight paths/content.
  No model download is permitted in these checks. Test setup's compatible weight
  reuse and missing/corrupt/runtime-repair paths separately.
- Run installed checks outside the checkout. Verify imports come from the tested
  environment. Render the formula from the accepted archive and check its Ruby
  syntax, three-command assertions and dependency recipe locally.

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

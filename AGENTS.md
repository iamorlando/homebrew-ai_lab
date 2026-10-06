# AI Lab repository policy

This policy applies to AI Lab source and to its Homebrew tap. In the source
repository, [docs/tests.md](docs/tests.md) is the durable release test matrix and
command reference. In the tap, use that document from the exact source commit
being packaged; do not assume the tap contains the source tree. Keep the matrix
current when public behavior changes. A test specification is not a test result.

## Release gate

Every Homebrew update, including packaging-only revisions, MUST have committed
source, a normal non-force push of the source and tap candidate commits, and a
passing release test suite before publication. Build from clean, committed
source; record the source SHA, tap SHA, version, dependency lock and artifact
SHA-256 values. Never publish uncommitted payloads or substitute different bytes
after validation. A changed candidate requires validation of the new candidate.

Before publishing release assets, tags or the public formula update:

1. Build the wheel and sdist from the exact candidate source. Verify byte binding
   from source through wheel/sdist to installed modules and bundled resources,
   accounting explicitly for generated metadata. Record artifact hashes,
   executable/interpreter paths and import locations. Run installed tests outside
   the checkout with a sanitized environment so source imports cannot mask a
   broken package. Install the wheel and independently build/install the sdist.
2. Test BOTH a clean install and a literal upgrade from the actual immediately
   prior published version in the same installation, retaining its data root.
   Record the old artifact hash and literal version before upgrading and the new
   literal version afterward. Include actual Homebrew clean-install and upgrade
   paths with the candidate formula/archive, not only Python package installs.
   Use owned test installations; do not relabel a new install as an upgrade or
   delete old data to make the upgrade pass. Exercise retained old API owners and
   restart/persistence cases as specified in `docs/tests.md`.
3. Run the full release matrix on clean and upgraded installed packages: every
   public command, subcommand, flag/action, UI button and keyboard flow, API/MCP
   path, shell completion, error/cancel/retry path and release checker. Reconcile
   installed `ai-lab --json`, recursive `--help` and source
   `ai_lab.cli.PUBLIC_COMMANDS` against the matrix. Unit tests, imports, headless
   widgets and fixture replays supplement actual installed CLI, terminal, web and
   owned local API process evidence; they do not replace it.
4. Run source checkers under `packaging/`, including
   `packaging/homebrew/check_web.py`, with the installed interpreter/executable
   and exact arguments from `docs/tests.md` and each accepted checker's `--help`.
   In the tap, the distributed checkers live under `scripts/` (for example,
   `scripts/check_web.py`); verify they match the accepted source checkers and use
   those paths. Run `brew test iamorlando/ai_lab/ai_lab` against the candidate
   installation and require actual install CI to pass for the candidate tap commit.
   That CI must install the candidate formula and run installed checks, not only
   lint Ruby, inspect a workflow, import source or report a queued job as passed.
   Use an owned local/staged candidate before publication; verify that eventual
   public URLs and checksums serve the same validated bytes.
5. Record exact commands, exit statuses, outputs/evidence, hashes, installation
   kind and process cleanup. Keep clean/upgrade and CPU/fixture/live results
   separate. Report PASS, FAIL, BLOCKED_INPUT or NOT_RUN truthfully. Required
   missing inputs or unexecuted required cases leave the release gate incomplete.
   Optional hosted credentials/external clients follow the matrix's explicit
   scope: test unavailable behavior and disclose limits without inventing new
   release prerequisites. A documentation-only change is never full-app or
   full-release PASS.

## Existing weights and user data

- Preserve saved models/profiles, keys, settings, conversations and other user
  data across installs, upgrades and repairs. Saved models may be migrated or
  deleted only when a genuine schema change requires it. Record the incompatible
  schema/fields, explicit reason, affected records, migration steps, backup and
  recovery/rollback procedure, and verify the outcome. Prefer lossless migration;
  limit unavoidable changes to affected data. Never wipe a data root as an upgrade
  shortcut or modify unrelated user data.
- Unless the underlying model weights change, compatible existing verified
  weights MUST be reused and work. An application, Python, dependency, runtime or
  receipt change must not force a gigabyte-scale weight redownload. Distinguish
  installed weights from runtime/dependency readiness; repairing a binary or
  dependency does not make its weights missing.
- Test preexisting verified weights across literal upgrade, clean-install
  adoption of an existing weight store, cancellation and retry. Assert zero
  weight-download calls and unchanged weight bytes/hashes; verify file identity
  where applicable and explain any necessary path/identity change. Also verify
  profiles, keys, settings and conversations survive. Use owned test data and
  approved existing weight paths, never destructive experiments on user data.
- Prove actual bounded runtime use of the reused weights in the serialized live
  lane, recording model/runtime provenance and outputs. Tiny fixtures and download
  spies prove reuse mechanics only; recorded native traces are not fresh native
  generation. If the live lane has not run, report that remaining gate explicitly.
- Keep corrupt, missing and incomplete-weight repair honest: detect corruption,
  preserve valid files, resume partial downloads when supported, and verify
  replacements. Zero-download assertions apply to compatible verified weights;
  do not disable integrity checks or claim corrupt files are usable to pass them.
  Record the actual defect and required repair/download separately.

## Work ownership and runtime limits

Work only in the assigned isolated worktree/branch. Preserve native/runtime pins
and locked dependencies unless changing them is explicitly in scope. Do not run
Cargo or rebuild native runtimes when their pins are unchanged; reuse verified
prebuilt artifacts. Do not edit other worktrees, shared source roots, Cargo
targets, weights, credentials, main, tags or release assets as a feature builder.

Use deterministic fixtures and real owned local API processes for CPU end-to-end
tests. Native/model/GPU starts and SDK/hosted requests need a separate orchestrator
grant specifying the owned endpoints, permitted weights, time/call/token bounds
and cleanup. Only one live lane runs at a time. A test command or matrix entry
does not itself grant live execution.

Stopping task-related running processes/servers when necessary for upgrade or
validation is already authorized. Verify process identity and ownership,
coordinate with the lane owner, preserve persistence, and leave unrelated
processes alone. Clean up owned test processes and verify released sockets.
Do not add approval flows or ask again for already-authorized fixes/actions;
honor the separate live-lane boundary.

Commit finished changes and freeze a clean worktree. Give the independent
reviewer the exact committed SHA, changed files, reproducible commands/results,
findings and limits. Review starts after builder freeze, in the reviewer's own
worktree; findings return to the builder. Builders do not push. Reviewers own
normal non-force feature pushes after their checks pass. The orchestrator owns
the combined merge and publication after the combined release gate passes.

## Context7 documentation

Use Context7 MCP for current library, framework, SDK, API, CLI tool and cloud
service documentation, including syntax, configuration, version migration,
library-specific debugging and setup, even for familiar tools. Prefer it over
web search for library documentation.

1. Start with `resolve-library-id`, supplying the library name and the user's
   full question, unless the user supplied an exact `/org/project` library ID.
2. Select by exact name, relevance, snippet coverage, source reputation
   (High/Medium preferred) and benchmark score. Retry alternate names/queries if
   results are unsuitable; use a version-specific ID when a version is requested.
3. Call `query-docs` with that ID and the full question, not isolated keywords;
   use the fetched documentation in the answer.

Do not use Context7 for business-logic debugging, refactoring, code review,
writing scripts from scratch or general programming concepts.

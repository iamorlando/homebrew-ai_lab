# Watermark decoder terminal

`ai-lab decoder` opens a Textual terminal app with a picker for the same saved
DeepSeek/Qwen generation profiles used by the website. To preselect a profile:

```sh
ai-lab decoder --name "Exact generation profile"
```

Names are exact, case-sensitive public generation profile names. No flags are
required. Profile IDs, backend aliases and Decisions providers are not names.
Use `--root` or `AI_LAB_ROOT` to select an existing configured workspace. The
command rejects `--json` and redirected stdin/stdout before constructing the
backend. Root integrates this command and the 0.1.12 release; the decoder builder
supplies the parser/dispatch hooks without editing CLI or version files.

Paste/edit text in **Text**, select a profile in the top picker, then use
**Decode** or Ctrl+D. Ctrl+D submits even while the text editor has focus and
preserves the exact text. In **Configuration**, the scheme and fields inherit saved
settings. The saved original key stays in the backend: the masked key field is
blank, with an optional original-key override. Scheme changes reset the field
schema while retaining any entered override key; they preserve text. All six
shared token watermark schemas, descriptions, paper links, enum/boolean/numeric
fields and payload symbols are available. Vocabulary is read-only and the shared
validator enforces the tournament depth constraint. No key is generated.

The detection-options disclosure provides prefix token skipping, stop token IDs,
tokenizer special tokens, match p-value cutoff and minimum scored tokens.
**Restore profile** or Ctrl+R resets scheme, fields, key override and detection
options to saved/default values without changing text. Plain profiles require an
explicit scheme and original key. Overrides never write to profiles.

**Evidence** shows the exact selected profile/backend/scheme, configuration
source, verdict, match, supplied confidence, p-value, scored tokens, minimum,
cutoff, strength, method and allowlisted native statistics. Confidence is
`1 - p_value` from a known-key test or conservative bound against unwatermarked
text; it is not a posterior probability of authorship. A match does not establish
watermark ownership or forgery. Insufficient evidence displays unavailable
confidence and p-value, never a success percentage. Existing detector limitations
and scheme-specific unsupported tests are preserved.

Editing inputs marks old evidence **STALE**. A result arriving after an input
change is discarded. Failed attempts retain the last successful result and its
own sanitized request. Model/backend/scheme identity mismatches and inconsistent
confidence/verdict/cutoff evidence fail before presentation. Reloading profiles
invalidates old evidence even if public fields look unchanged.

Escape or **Cancel** stops waiting; a native API may still finish its current
request. Cancelling a queued decode immediately makes retry available; late
cleanup or evidence from that cancelled run cannot replace a newer run.
Retry with **Decode**, use **Reload profiles** after discovery errors,
and exit with Ctrl+Q or **Exit**. Discovery and detection use the existing
HerdrReporter automatically in a valid current Herdr environment; exit releases
it. Ordinary terminals require no lifecycle flags.

The sanitized request/response disclosure and **Copy sanitized evidence** omit
keys. Key inputs stay masked, are never fetched from saved profiles, and are
redacted from public errors and ordinary JSON. There is no automatic export or
persistent draft. Copy requires current evidence. Pasted text appears in copied
request evidence, so choose whether to copy it.

Opening performs catalog discovery only. It does not start APIs, install models,
hash model weights, provision/migrate the workspace, require a website/daemon,
or use hosted fallback. Start the selected model separately when the shared
backend gives `ai-lab services --action start --model deepseek` or `ai-lab services --action start --model qwen`
guidance. The only ordinary filesystem write is the existing shared workspace
configuration lock; saved profiles, keys, manifests and templates remain read-only.

## Shared implementation and integration

`ai_lab.decoder_terminal.add_parser(subparsers)` registers `decoder`, optional
`--name`, and a locally recognized but rejected `--json`.
`ai_lab.decoder_terminal.run(args, root) -> int` rejects noninteractive use before
startup and runs `DecoderApp`. Root must dispatch before setup/Client.connect.

`DecoderService` invokes the actual shared `/api/decoder/models` and
`/api/decoder/detect` routes in `harness/detection_lab.py` through HTTPX
ASGITransport. A narrowly scoped, root-approved `decoder_tools` dependency
injection supplies a read-only LabTools subclass, inheriting the actual
`generation_profile`, `effective_watermark`, `detect_text` and
`detect_watermark` implementations without `prepare()` or a Decisions runtime.
The default website constructor is unchanged. No new route, schema or native
behavior is introduced. Shared WorkspaceLock coordinates other cooperating
consumers; this terminal host owns no chat/generation tasks and needs no OpenCode
session helper. All per-request native HTTP contexts close normally; exit closes
the ASGI client and lifecycle reporter, including cancellation.

Presentation mirrors `harness/ui/decoder-evidence.mjs`; it validates and formats
backend evidence and does not calculate detector scores. Detector schemes,
validation and p-values come from the existing backend. Chat, agent, storage,
Decisions modules, pins and release version are untouched.

## Web parity checklist

| Authoritative web behavior | Terminal proof |
| --- | --- |
| Exact saved profile identity and DeepSeek/Qwen routing | Actual shared-route tests and mounted profile switching |
| Private saved key, inherited scheme/settings | Catalog redaction, full native request assertions, read-only snapshots |
| Run-only settings/key/scheme; restore; preserve full text | Mounted schema/override/restore and backend assertions |
| Shared field schemas and detector options | Six mounted schema transitions, strict shared-validation rejection |
| Actual evidence and confidence definition | Supplied 0.17/0.83 evidence check; actual-route detection; mounted evidence |
| Insufficient/error/identity mismatch | Unavailable p/confidence, sanitized errors, rejected mismatched result |
| Old evidence stale after changes | Mounted stale/late-result rejection and reload invalidation |
| Manual readiness and no fallback | Both backend stopped guidance and no-start/download/hash sentinels |
| Retry and key-free ordinary raw view | Immediate/queued pre-entry cancel, guarded late cleanup, retry/exit; paired sanitized request/response |
| Decode keyboard shortcut | Focused TextArea Ctrl+D preserves exact text and reaches the shared route |
| Unchanged ordinary web routes | Existing seven decoder route tests and four JS evidence tests |

## CPU proof and attribution

Run from the checkout with the existing Python environment:

```sh
python -m unittest discover -s tests/ai_lab -p 'test_decoder*.py' -v
python -m unittest discover -s harness/tests -p test_decoder.py -v
node --test harness/tests/decoder-evidence.test.mjs
python packaging/check_decoder.py --wheel /path/ai_lab-VERSION-py3-none-any.whl --sdist /path/ai_lab-VERSION.tar.gz
python packaging/decoder_proof.py
```

The mounted fixtures run real Textual widgets and the actual ASGI routes and
WatermarkRuntime HTTP adapter with explicit fake DeepSeek/Qwen endpoints.
Native statistics are synthetic. Screenshots label **HTTP FIXTURE** and are
terminal/route proof, not model inference, watermark accuracy or GPU proof.
The package probe runs isolated Python against extracted wheel bytes, verifies
module hashes, mounts the app and detects with both fake backends. It uses no
network sockets or SDK. Root/reviewer owns integrated public-command checks and
independent non-force push after PASS; the builder does not push.

Mounted SVG proof is saved under `output/ai-lab/decoder-terminal-*.svg` by the
reproducible proof script. Screenshots contain fixture text and no real key or
profile. Actual models are deliberately outside this verification scope.

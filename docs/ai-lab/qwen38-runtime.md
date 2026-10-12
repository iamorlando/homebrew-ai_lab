# Qwen3.8-27B runtime and artifact provenance

AI Lab's `qwen38` family is the conversational **Qwen3.8-27B**, separate from
legacy `qwen` / Qwen3-8B and the CLM decision encoder. Its weights and tokenizer
live in `.models/qwen3.8-27b` and `.models/qwen3.8-27b-assets` respectively.
The conversational integration uses the text backbone; image/video inputs and
MTP are outside this integration.

## Immutable download inputs

The [official model](https://huggingface.co/Qwen/Qwen3.8-27B/tree/1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0)
is pinned at `1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0`.
The [Q4_K_M conversion](https://huggingface.co/bartowski/Qwen3.8-27B-GGUF/tree/0c92138c51f112d2f0dc84d5f6d1ebe4b9912b9a)
is pinned at `0c92138c51f112d2f0dc84d5f6d1ebe4b9912b9a`.
The quantizer's metadata identifies the official model as its source. The
published [tensor layout](https://huggingface.co/bartowski/Qwen3.8-27B-GGUF/blob/0c92138c51f112d2f0dc84d5f6d1ebe4b9912b9a/layouts/Qwen3.8-27B-Q4_K_M.tensor-types.txt)
uses supported Q/K and floating-point types, rather than unsupported IQ types.
The following checksums bind the download manifest; weights were **not** downloaded
or hashed locally during this audit. The GGUF SHA and size come from the pinned
Hub LFS metadata; every listed small asset was downloaded and hashed locally.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `Qwen3.8-27B-Q4_K_M.gguf` | 17442399968 | `880a52af8317974f7b4b064a6bc29ff49e188b91aa218e08eea3078b6b1cc673` |
| `config.json` | 4312 | `191e0af232104ed8b65258cf3fb2b842e288008baca7633c11b82a1ac7203aab` |
| `tokenizer.json` | 12809320 | `0997f410c57a1f4e53b09e4be8f4a172d90edd9564368fb0847030937229b9f3` |
| `tokenizer_config.json` | 17928 | `b11349aafa7cdc6a320767cf7ceb29ed82f7eda5d65e8e0819e76f0ce947bf27` |
| `generation_config.json` | 202 | `e70c136c1b78ddc1fb0905bac8e733a4dc448d4f852a5dd75143fffc70be550e` |
| Upstream `chat_template.jinja` | 8952 | `c3cf9e34abf4f9e36c2d72165aa9c132d3e2a725b6c2586aaa3a8af9d7a81041` |

The model output has **248320** rows, including padding. The official tokenizer
has **248077** distinct token IDs, `0..248076`; its base vocabulary has 248044
entries plus 33 added tokens. Use the padded output dimension for watermark
vocabulary configuration, and the model's own tokenizer for token IDs and text.
`generation_config.json` provides EOS IDs **248046 and 248044**; keep both.

## Existing native runtime

No runtime pin or dependency change is required by this architecture audit:

- mistral.rs: `edc4950d31f1247ed641176e1cf0c9d8ce4d0274`
- llm_watermarking: `af89e9ecdb8f9a9640fd48a331c4cdc2b35e76e1`
- Release binary SHA-256: `d5f2947a3d377173f6d6782062bb948956e9c26c56f84fb8f096bf9be798163d`

The official config reports `Qwen3_5ForConditionalGeneration` / `qwen3_5`.
At that native commit, `mistralrs-core/src/pipeline/gguf.rs` resolves `qwen35`
without a projector as a text model. `gguf/normal_config.rs` unwraps the nested
`text_config`; `gguf/qwen_multimodal_bindings.rs` maps the packed Gated DeltaNet
weights to `Qwen3_5TextLoader`. The official native context is 262144 tokens;
AI Lab's existing 8192-token serving cap remains below it. Extra vision/MTP
artifacts are unnecessary for ordinary text generation.

The native launch follows the same owned-server pattern as DeepSeek:

```sh
mistralrs serve -m "$AI_LAB_ROOT/.models/qwen3.8-27b" \
  -f Qwen3.8-27B-Q4_K_M.gguf \
  --tok-model-id "$AI_LAB_ROOT/.models/qwen3.8-27b-assets" \
  --jinja-explicit "$AI_LAB_ROOT/qwen38-chat.jinja" \
  --host 127.0.0.1 --port 11440 --max-seqs 1 --prefix-cache-n 0 \
  --paged-attn off --max-model-len 8192 --no-ui --token-source none
```

This is a command contract, **not evidence of a successful model launch**.
All paths must already be installed and verified. Leave the model directory free
of a companion projector to retain text-only loading. Quantized file size is not
a promise about total memory required: loading, activations and caches also need
memory. A failure must preserve the downloaded weights and report its reason.

Watermarking, including TextGrain and SynthID, uses the runtime's common sampler
and detection endpoints after model loading. Architecture support alone does not
prove live generation or watermark detection for this particular checkpoint.

## AI Lab chat template

`qwen38-chat.jinja` is adapted from the pinned official template above, under the
accompanying [Apache-2.0 license](licenses/Qwen3.8-27B-LICENSE). Its SHA-256 is
`ab8504a2f40b37824f1d0eb382dfba6438beb65f5006d96def9d3d4f532862f6`.
The changes are limited to a provenance comment, forcing `enable_thinking=false`
for AI Lab's existing answer-only completion contract, and clear validation of
missing tool names or invalid argument maps. Missing/null/empty tool arguments
produce an argument-free call. Null assistant content remains supported by the
upstream content renderer.

Qwen3.8's XML `<tool_call><function=...><parameter=...>` format is retained.
The pinned native `pipeline/chat_template.rs` parses valid OpenAI JSON-object
argument strings before rendering, detects the Qwen format from template markers,
and uses `tools/parsers/qwen.rs` for extraction and required/named-call grammar.
No extra parser-selection launch flag is needed. Invalid JSON argument strings
fail explicitly rather than silently disappearing. Typed parameter values are
recovered using the supplied tool schema.

For one system/user exchange, the prompt is:

```text
<|im_start|>system
{system.strip()}<|im_end|>
<|im_start|>user
{prompt.strip()}<|im_end|>
<|im_start|>assistant
<think>

</think>

```

The official template trims system/user content. Detection's generation-prefix
builder must apply the same trimming. Prior assistant turns retain the upstream
thinking delimiters; no new thinking is requested. The unmodified upstream
thinking controls accept `low`, `medium`, `xhigh` and default to `xhigh`, but are
not exposed by this answer-only integration.

## Validation recorded on 2026-10-12

CPU-only template checks:

```sh
python -m unittest harness.tests.test_qwen38_template -v
```

**PASS: 6 tests**, covering exact prefix/whitespace, multi-turn history, null
assistant content, native-normalized JSON arguments, typed XML parameters,
parallel calls/results and useful malformed-history errors. The same cases also
passed with the **MiniJinja 2.14.0** prebuilt Python binding, matching the engine
version in the native Cargo.lock. It was installed only into an owned `/tmp`
test directory, without changing application dependencies or running Cargo.
These are template-engine tests, not HTTP/model inference.

The verified existing CPU debug test binary
`mistralrs_core-859abbafd96f3197`, SHA-256
`0d617aa1cbb9af99f956a230af9b24e3dfb7704b0c561d7319e044101407c718`,
was reused without rebuilding:

| Exact test filter | Result |
| --- | --- |
| `tools::parsers::qwen::tests` | PASS, 8 tests |
| `tools::tests::qwen_xml_arguments_follow_the_tool_schema` | PASS, 1 test |
| `pipeline::chat_template::tests` | PASS, 20 tests |

Metadata, original small assets and native CPU logs are retained in
`/private/tmp/qwen38-runtime-audit-20261012/`. The native handoff and test-artifact
provenance are in `/private/tmp/mistral-textgrain-runtime-edc4950d-af89e9ec/`.
That initial CPU audit did not download weights or start models. The native
acceptance below supersedes its earlier **NOT_RUN** status for the listed cases.

## Actual native acceptance on 2026-10-12

**PASS: bounded Qwen inference smoke**, using the installed wheel from application
commit `3f5b941df2a45da4398a5e0d8ba0adde40c0062a`, outside the source checkout,
on a 64 GiB Apple Silicon Mac running macOS 27.0. This is not a full release gate.
The [machine-readable evidence](qwen38-native-validation.json) records installed
module paths, artifact hashes, outputs, call limits and cleanup.

The installed `setup install qwen38 --yes --json` command downloaded and locally
hashed the complete 17,442,399,968-byte GGUF and every listed asset. Their hashes
match the table above. It installed the existing verified runtime without Cargo
or pin changes. AI Lab then automatically started the selected Qwen backend at
`127.0.0.1:11440`, with all 64 model layers on Metal. Initial readiness took
215.339 seconds, including integrity checks and first-use Metal compilation;
a subsequent startup took 19.342 seconds. A sampled startup stack confirmed
real model warmup waiting for Metal's shader compiler, rather than a failed load.

| Actual installed path | Result |
| --- | --- |
| Plain selected-Qwen completion | PASS: `6 × 7` returned `42` |
| Native XML tool calls and result continuation | PASS: typed `17, 25` arguments; results returned by call ID; final answer `42` |
| Real MCP stdio through installed handlers | PASS: selected Qwen returned `17` for `9 + 8`; borrowed owner unchanged |
| Saved KGW profile generation, trace and detector | PASS: 93 generated tokens, 24 trace steps, 90 scored tokens |
| Saved SynthID tournament profile generation, trace and detector | PASS: 64 generated tokens, 24 trace steps, 60 scored tokens |
| Saved TextGrain profile generation, trace and detector | PASS: 64 generated tokens, 24 trace steps, 60 scored tokens |
| Repeat setup using the actual downloaded weights | PASS: zero download/network calls; unchanged bytes, hashes and file identities |
| Cleanup | PASS: owned native processes exited, port released, receipts removed, original profile bytes restored |

The short watermark samples all returned `no_match` at the configured threshold.
These checks verify actual generation, native traces and finite detector evidence;
they do not establish statistical detection power. No SynthID or tournament
implementation was changed.

The first tool check incorrectly required exactly one call. Qwen returned two
valid parallel calls with distinct IDs, which the API supports. The original
failed report is retained; a corrected, separately bounded two-request rerun
validated every call and the final answer. The retry wrapper also initially
mistook a transient socket bind failure for incomplete cleanup because it omitted
`SO_REUSEADDR`. Separate process/listener checks and the production bind policy
confirmed cleanup; both records are retained.

The padded GGUF vocabulary triggers the runtime's embedded-tokenizer fallback.
All official token IDs and BPE merges agree, and recorded native trace positions
match the official tokenizer for all three generations. Two limits remain: the
fallback recognizes extra GGUF padding-label strings and uses EOS `248046`,
while the ignored official generation config also lists `248044`. Ordinary
completion and tool turns stopped correctly in this run; the secondary EOS and
literal padding-label inputs are not covered by that success.

Reproduce with an installed candidate interpreter, verified weights in an owned
root, and a separately authorized serialized native lane:

```sh
"$INSTALLED_PYTHON" -I packaging/check_qwen_native.py \
  --root "$OWNED_ROOT" --output "$EVIDENCE_DIR/qwen-native.json" \
  --start-through-app --mcp-wire
```

Keep `packaging/check_qwen_mcp_wire.py` beside the checker. It never downloads
weights; full smoke bounds are 528 generated tokens, 600 seconds for startup
and 180 seconds per case. `--only-tool-roundtrip` runs only the two tool turns
with a 192-token bound. Retained local evidence is under
`/private/tmp/qwen38-live-20261012/`.

No deliberate out-of-memory, long-context, live browser-click, DeepSeek/CLM,
macOS 15, literal-version upgrade or Homebrew run was performed in this lane.
No GitHub CI ran. Weight reuse here is actual repeat setup, not an upgrade claim.

# Decisions in the terminal

Run `ai-lab decisions` to choose an available decision model. Use `ai-lab decisions --model laya` to select one at launch, or `ai-lab decisions --model jev --mode rank` to start in ranking mode. Decisions accepts canonical provider identities and existing discovery labels such as `Laya (ONNX)` and `CLM upstream`. Saved generation-profile names and short provider aliases are not accepted. There is no Decisions `--name` flag.

The app runs the existing shared Decisions HTTP routes in process. It needs no website or AI Lab daemon. Opening discovers configuration and does not download or start any model. For a local provider, start its API separately with `ai-lab services --action start --model laya`, `--model contrastive`, or `--model clm-upstream`. If it is not installed, use the installation guidance shown beside the picker. Jev becomes available when the shared backend finds `TYPESAFE_API_KEY`, `JEV_API_KEY`, or the existing workspace credential handoff. Refresh providers after changing configuration. The selected provider stays selected if it becomes unavailable; submission never retries or falls back to another provider.

The Request tab contains the provider picker, five web example presets, and shared state/context. Turn on **Parse state as JSON** to send an object or array. In Ask, add, remove, rename, or change the type of each question. Instructions accept text or JSON. Criteria use an editable JSON object for noul true/false descriptions or named choice options, and an ordered JSON array for score rubric levels. This compact terminal editor accepts the shared API's nested JSON descriptions and null choice descriptions. It rejects duplicate IDs/object keys, malformed JSON, missing instructions, invalid criteria, and requests over 100 KB before provider dispatch. Choice needs at least two named options; score needs 2–10 ordered levels.

In Rank, edit the context, optional ranking instructions, and candidates, one per line. Blank lines are ignored; candidate text is otherwise sent verbatim. Rank uses the shared API's probability ordering, including stable ordering for ties.

Click **Run** or press **Ctrl+Enter**. The request is frozen while it runs, with elapsed time and an available **Cancel** button. **Escape** invalidates the request before cancelling its HTTP operation; work already received by an external provider may continue. Any late response from a cancelled or closed request is discarded and cannot publish results. A second Run while busy sends nothing. **Ctrl+Q** exits and closes owned tasks and clients. **Ctrl+R** refreshes providers. Scroll and Tab move through forms in small terminals; Run and Cancel stay visible at 50×18.

Results show returned model identity, provider latency, round-trip time, usage, p(true)/p(false), choice distributions and returned confidence, expected score and its rubric distribution, or ranked candidates with probabilities. Confidence and score are displayed as returned. RL fields such as `rl_agent.act_probability` appear as auxiliary metadata and never replace the primary probabilities. The JSON tab keeps the submitted request paired with its raw shared API response, and shows the unsent draft in a separate preview. Known configured keys are redacted. Editing fields, changing modes, loading a preset, or importing a draft preserves the submitted pair until another Run. A stale note in Results, JSON, and Export explains when the draft differs; the copy controls explicitly distinguish the submitted request, response, and draft preview.

The Snippets tab supplies curl and standard-library Python examples for the corresponding web HTTP endpoints at `127.0.0.1:8080`. Start `ai-lab web` separately to execute those examples; the terminal app itself does not need it. Copy sends the displayed JSON or snippet through the terminal clipboard protocol. If your terminal blocks clipboard access, export instead.

Drafts and results stay in memory. The Export tab saves a private JSON bundle with mode `0600`; it refuses existing files and symlink targets. **Save current draft** writes the unsent request with no response. **Save submitted result** writes the original submitted request with its matching response and timing, even after the draft changes. Each export records whether the draft differs from the submitted request. Import reopens the bundle's request without submitting it or loading its response; an existing submitted pair stays intact. An imported provider remains explicit even if unavailable. Raw API requests can also be imported. Rank import checks that joining the candidate list and parsing it back through the editor gives exactly the original list, before changing any draft field. It rejects all lossy line separators (including Unicode), trailing separators, and whitespace-only candidate identities.

When launched in a valid current Herdr pane, the app uses the existing lifecycle reporter automatically: idle, working, idle, then release on exit. Reporting failure is nonfatal and does not alter provider requests. It creates no agent chat input channel and changes no chat behavior.

## Web parity checklist

| Web capability | Terminal implementation / adaptation | Proof |
| --- | --- | --- |
| Provider discovery, labels, selection, retry | Same `/api/decisions/models`; optional `--model`; UI picker; explicit refresh; unavailable selection retained | Mounted discovery/retry tests; no provider I/O on opening |
| Local Contrastive, upstream CLM, Laya, hosted Jev | Same `DecisionRuntime`, `allow_start=False`; credentials stay in backend; no hidden routing | Mounted ask + rank for all four; exact URL/model/header/count assertions |
| Text or JSON state | TextArea plus JSON switch; shared schema restricts JSON to object/array | Mounted JSON ask/rank and validation fixtures |
| Multiple typed questions | Editable cards with ID, type, instructions, add/remove; one request for all cards | Mounted three-type edit/add/remove test |
| noul true/false descriptions | Optional JSON object, blank omits criteria | Nested JSON criteria fixture |
| Choice options / descriptions | Editable JSON map; arbitrary supported nested descriptions and null | Shared-schema and duplicate-key tests |
| Score ordered rubric | Editable JSON array, 2–10 levels | Mounted rubric edit and limit tests |
| Ranking context, instructions, candidates | Rank tab, verbatim one-line candidates; shared rank endpoint; lossless import check before draft mutation | Mounted JSON rank, all splitlines separators, import→Run identity and probability ordering tests |
| Presets | Support, trajectory verifier, PR review, best-of-N, tool routing | Presets reused by mounted workflows and screenshot proof |
| Validation | Shared Pydantic models plus web editor completeness rules; finite JSON and duplicate safeguards | Invalid JSON/type/criteria/ID/size fixtures, no dispatch |
| Submit, status, elapsed time, cancel | Fixed action bar, async HTTP task, frozen request, cancellation invalidates the request before teardown | Mounted delayed/late-provider cancel and exit fixtures; publication guarded by request identity |
| Probability, choice, score, rank result views | Numeric values plus Unicode bars; confidence and score kept as returned | Hand-authored p=.2372, confidence=.2781, RL=.99; rank p=.8 |
| Latency/model/usage | Shared response header plus measured round trip and response fields | All-provider and wheel fixtures |
| Raw request and response | Immutable submitted pair and separate current draft preview; known-key redaction; failed response diagnostic | Mounted edit/mode/preset/import, pair equality, separate copy/export and key tests |
| curl / Python snippets and copy | HTTP examples, terminal clipboard, private file alternative | Snippet syntax / copy fixture |
| Share link / draft restore | Explicit private draft or submitted-result export/import replaces browser URL/localStorage; nothing persisted automatically | Mounted separate exports, permissions, no-overwrite, no auto-submit |
| Stale result indication | Draft compared with the submitted request; visible in Results, JSON and Export and recorded in bundles | Mounted stale evidence/copy/export regression |
| Desktop/mobile responsiveness | Scrollable terminal forms and fixed controls at normal and 50×18 sizes | Mounted tests and SVG screenshots |

## Verification and limits

Run the CPU fixtures with:

```sh
python -m unittest tests.ai_lab.test_decisions_terminal -v
python -m unittest discover -s harness/tests -p test_decisions.py -v
node --test harness/tests/decisions.test.mjs
python -m tests.ai_lab.decisions_terminal_proof --output output/ai-lab/decisions-terminal
uv build --offline --out-dir /tmp/decisions-build
python packaging/check_decisions.py --wheel /tmp/decisions-build/ai_lab-0.1.11-py3-none-any.whl --sdist /tmp/decisions-build/ai_lab-0.1.11.tar.gz
```

The version in the example is the builder's exact 0.1.11 base; root owns the 0.1.12 bump. The package checker extracts the actual wheel into an isolated directory, verifies source hashes and bundled shared-backend imports, mounts Textual, and runs ask/rank against a real loopback fake provider. Mounted hosted tests intercept Jev's official URL with `httpx.MockTransport`; they make no hosted network or SDK call. The proof is UI/API/package integration on CPU, not native inference or GPU performance. Existing native-runtime manifests and binaries are unchanged and provide no new inference attribution for this patch. Root and reviewer own final public parser/dispatch/package verification after integration.

The shared rank API returns ranked probabilities and usage, and does not retain the upstream answer's auxiliary RL fields. The terminal faithfully displays that existing response; it adds no provider/schema interpretation. Clipboard delivery depends on terminal support, and rank import is limited to one-line candidates. The shared backend reads provider configuration from its launch environment and the existing Jev handoff; environment changes in a different shell require relaunching the terminal app. Explicit private export/import replaces automatic browser persistence and share URLs.

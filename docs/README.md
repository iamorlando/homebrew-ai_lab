# AI Lab

The public launcher lists exactly thirteen surfaces: `weights`, `models`, `apis`,
`chat`, `decisions`, `completion`, `services`, `decoder`, `skills`, `mcp`,
`completions`, `web`, `setup-python-experiments`. Bare `ai-lab` shows help; `ai-lab --json` returns discovery.
`apis` is informational only, and `skills install --agent codex --scope project`
installs the current advanced guide. Screens never offer weights automatically.
For advanced session/trace/API flags, use `ai-lab --skill` for its complete flag reference.

AI Lab provides conversational DeepSeek/Qwen chat through `ai-lab chat` and the
website's raw-prefix Completion experiment through `ai-lab completion`. They share saved
generation profiles and the pinned `iamorlando/mistral.rs` server. Native logits
and captured tournament traces support token inspection.

For a saved model, use `ai-lab chat --name "Model name"`; names are
case-sensitive and names with spaces need quotes. The saved backend, seed and
watermark settings are inherited. Herdr lifecycle reporting is automatic in the
current pane. MCP tools and a separate `--herdr-tab` are optional.

The terminal apps open with these basic commands:

```sh
ai-lab decoder                        # generation-profile picker
ai-lab decoder --name "Exact generation profile"
ai-lab decisions                      # available-provider picker
ai-lab decisions --model laya
```

The terminal decoder inherits the selected profile's saved watermark settings
and allows a scheme override for decoding. Decisions supports typed ask/rank
workflows. Its providers (`laya`, `contrastive`, `clm-upstream`, `jev`) have no
saved profile names; select one in the picker or with `--model`. Opening Decisions
does not start/download models; start local provider APIs separately with
`ai-lab services`. The web decoder remains available through `ai-lab web` →
sidebar **Watermark decoder** at `/decoder`.

## Install and use

Requires Apple Silicon and macOS 15 or newer. Homebrew installs the Python and
`uv` dependencies; local model downloads remain optional.

```sh
brew tap iamorlando/ai_lab
brew install iamorlando/ai_lab/ai_lab
ai-lab --version                       # target: AI Lab 0.1.14
ai-lab weights offer                 # keyboard model picker
ai-lab web                            # opens the app in its own window
```

For an existing installation, run `brew update` and
`brew upgrade iamorlando/ai_lab/ai_lab`. Stop an older website with Ctrl+C in its
launch terminal and start `ai-lab web` again to load this release. Profiles,
watermark keys, models, and recordings remain in the workspace.
See [Updating AI Lab](upgrading.md) for version checks, runtime repair, existing
CLM server recovery, and cleanup that preserves your data.

To use the agent tools, configure one client and restart that client:

```sh
ai-lab mcp install --codex             # or --claude, --cursor, --opencode
# Refresh an existing AI Lab MCP entry after upgrading:
ai-lab mcp install --codex --force
```

The client starts MCP through `uvx`; no website or CLI daemon needs to run.
Jev is the default decision model. An available `TYPESAFE_API_KEY` or
`JEV_API_KEY` is saved privately during MCP installation. To share this
repository's existing models and saved key, set
`AI_LAB_ROOT=/path/to/deepseek` before installing MCP and launching model APIs.

Local APIs are started explicitly in a separate terminal:

```sh
ai-lab services --action list --json
ai-lab weights install laya          # asks before downloading
ai-lab services --action start --model laya               # local decisions
ai-lab services --action start --model deepseek           # DeepSeek generation and watermark detection
ai-lab weights install qwen --yes    # official Qwen3-8B Q4_K_M, verified SHA-256
ai-lab models create --name Qwen --underlying-model qwen --seed 42
ai-lab services --action start --model qwen               # separate owned API on 127.0.0.1:11439
ai-lab weights install clm --yes     # CLM/Qwen weights and both CLM servers
ai-lab services --action start --model contrastive        # native Contrastive decisions
```

Ask your agent to list models, answer decision questions, explain watermark
schemes, create a watermarked DeepSeek profile, or detect a watermark in supplied
text. `detect_watermark` accepts a saved model name/key or explicit scheme, key,
and settings. `update_watermarked_model` saves overrides for future sessions;
`get_model_config` can retrieve the saved watermark key explicitly. See
[MCP tools and examples](#mcp-for-agent-clients) for the full contract.

## Set up Python experiment notebooks

```sh
ai-lab setup-python-experiments --location ~/dev/ai_experiments
# Machine-readable result, containing key names and presence only:
ai-lab setup-python-experiments --location ~/dev/ai_experiments --json
```

`--location` is the exact checkout directory, relative to the current directory
when given a relative path. Setup clones `iamorlando/ai_experiments` using normal
Git authentication, or reuses a verified matching clone without fetching or
pulling. It refuses unrelated nonempty directories and linked/shared write files.
Git and uv are required. The repository's Python requirement selects a compatible
interpreter (currently Python 3.14), and Poetry installs its actual declared
dependencies into that checkout's `.venv`. If Poetry is absent, an isolated uv
tool supplies it. The caller's active environment and installer overrides cannot
redirect the environment. Setup can download Python and Python dependencies.

Available `TYPESAFE_API_KEY` is copied from the existing CLI credential helper,
which also accepts `JEV_API_KEY`; optional `CLM_API_KEY` comes from the launch
environment. Setup adds only missing names to `.env`, preserving existing values,
empty assignments and comments. New `.env` files use mode 0600; existing private
permissions are preserved, and group/world access is removed. `.env` and `.venv`
must be untracked and locally excluded from Git before keys are written. The
result reports key names/presence, never values. Missing keys do not block setup.

Open and run the notebooks yourself, selecting this `.venv` as their Python
kernel. Setup does not launch Jupyter, execute notebooks, call hosted providers,
start model APIs or provision native runtimes. Rerun the same command to finish
an interrupted install; existing notebooks and settings are preserved.

## Open the website

```sh
ai-lab web
# From this repository:
./ai-lab web
```

This launches the website at `http://127.0.0.1:8080/completion` in its own window
using an existing Chrome, Edge, Brave or Chromium installation. The CLI prepares
a private, persistent browser profile inside the workspace automatically; no app
installation or browser setup is needed. If no compatible browser is available,
the page opens in your default browser. The same completion brackets, model configuration,
watermark experiments, detection, paired conversations and results pages are
included. The terminal views and the default `ai-lab` command are unchanged.

The website runs in the foreground. Keep its terminal open; Ctrl+C stops the
website and its owned session helper. Model profiles, recordings, CLI sessions,
and the inference runtime remain in the selected workspace. If this workspace's
website is already on the requested port, the command opens that existing site.

```sh
ai-lab web --browser                    # regular tab in your default browser
ai-lab web --port 8090 --no-browser
ai-lab --root /path/to/deepseek web
ai-lab web --yes --no-browser --json
```

For a permanent app shortcut, open the site in a regular browser and choose
**Install app** in the top bar, or use the browser's installation menu. Chrome
and Edge require their standard confirmation; Safari on macOS Sonoma or later
uses **File → Add to Dock**. The site includes its app manifest and icons, and
installed shortcuts open in standalone windows. Keep `ai-lab web` running in the
same workspace and on the same port. If the website is stopped, the installed
app shows the launch command and reconnects when it starts. Workspace pages and
API results are always fetched live; the app does not cache private model inputs.

Opening AI Lab's managers/screens never offers weights or starts a model API.
Bare `ai-lab` prints the canonical launcher. Ordinary `ai-lab web` skips inference
setup; `--yes` or `--with-models` explicitly opts into provisioning. The existing
website's pinned OpenCode helper may be installed by its launcher; it is separate
from model weights/inference. UI assets ship with the package, and saved data
stays outside Homebrew's Cellar.

Open `ai-lab weights` to inspect downloaded and available models. Choose
**Download / repair**, or run `ai-lab weights offer`, to open the explicit model
picker. Use **↑/↓** to move, **Space** to select, **A** to select/clear all,
**Enter** to set up selections, **Esc** to skip, and **Ctrl+C** to cancel.
The picker shows missing bytes and server dependencies for DeepSeek, Qwen, CLM
and Laya. After an upgrade, it also includes downloaded models whose runtime
needs repair. Verified weights are reused; runtime-only repair downloads zero
weight bytes; runtime binaries or dependency packages may still be downloaded.
The inventory's **Weights** and **Runtime** columns are independent: a model can
be **Downloaded** with **Repair required** and **0** missing weight bytes.
No other screen opens this offer automatically. Missing or checksum-invalid
weights still need replacement; inspect the reported data root before accepting.

Downloads use an overall bar and a current-file bar that update in place, with
transfer speed and estimated time on wider terminals. Verification and dependency
installation appear in the same display. Package-manager output is saved in
`ROOT/.state/ai-lab/model-install.log`; failures point to that log. Existing files
are checksum-verified and reused; interrupted model downloads resume. Your
selection or skip is remembered; use weights offer to reopen it explicitly. Jev uses your API key and needs no model download.

```sh
ai-lab weights list --json
ai-lab weights install laya             # picker for this model
ai-lab weights install clm laya --yes    # explicitly accepts both
ai-lab weights install --yes            # explicitly sets up all catalog models
ai-lab weights offer                    # reopen the model picker
ai-lab web --with-models --yes            # downloads optional models, then opens UI
ai-lab web --no-models                    # opens without inference downloads
```

`--no-setup` skips inference provisioning even when requested by another flag.
Scripts require `weights install ... --yes` or explicit `web --with-models --yes`
to download models. Inspect `weights list --json` first. CLM's isolated PyTorch/Transformers environment needs roughly another
1 GB. Laya's npm packages need roughly 250 MB; AI Lab downloads a verified Node
runtime for Apple Silicon if Node.js 20+ with npm is unavailable. Model files
and dependencies remain in the workspace and survive CLI upgrades.

## Decisions

Open **Decisions** in the website navigation, or visit `/decisions`. The Ask and
Rank editors follow the [CLM playground](https://github.com/Contrastive-LM/CLM):
text or JSON state, Noul/Choice/Score questions, editable criteria, examples,
probability bars, and JSON/curl/Python views. Copy link preserves the inputs in
the URL fragment without running the request. Inputs are also remembered in
this browser. Shared links contain the state and questions.

**Contrastive** calls native CLM through the local Mistral `/v1/systemone` API.
Install and start it with:

```sh
ai-lab weights install clm --yes
ai-lab services --action start --model contrastive
```

CLM installation downloads and verifies three parts: the published CLM
projection checkpoint, its Qwen3-8B encoder weights, and a prebuilt CLM-capable
Metal server. It also prepares the independent upstream Python server. Both
CLM implementations share the downloaded weights. Existing files are verified
and reused, and interrupted weight downloads resume. No Rust, Xcode, manual
binary placement, or environment-variable configuration is required.

After upgrading an older installation that already has the CLM/Qwen weights,
`ai-lab services --action start --model contrastive` automatically installs or updates the native
server before starting the API. `ai-lab services --action list --json` reports
`weights_present` separately from `installed`, and includes the install command.

The native server is installed at `.runtime/decisions/mistralrs`, with verified
provenance in `.runtime/decisions/build.json`. It loads local files from
`.models/clm-v0.1-8b/`, runs offline, and listens on loopback port 11436. The
launcher stays in the foreground; Ctrl+C stops the server it started.
Logs are in `.state/decisions-mistral.log`.
The first startup and inference can take a few minutes while the encoder loads
and Metal compiles its kernels. The CLI prints the log path during startup.

The native runtime reserves memory for encoder workspace and moves layers to
the CPU when the GPU budget cannot hold them. Apple Silicon GPU and CPU layers
share the same physical RAM budget. Encoder batches shrink and unused Metal
scratch buffers are reclaimed under memory pressure. These adjustments preserve
weights and precision; CPU offloading can increase latency. The full Qwen3-8B
encoder still needs enough system memory to hold its weights and workspace.

For an explicitly managed custom installation, `AI_LAB_DECISIONS_BINARY` selects
another executable. `AI_LAB_DECISIONS_URL` selects the native runtime's loopback
HTTP origin and port. Services can launch and manage native CLM there when the
endpoint is free. Services also recognizes verified older native CLM launches
and ownership records in supported prior data folders. A process whose identity
cannot be verified stays controlled by its original launcher. See
[Updating AI Lab](upgrading.md) for upgrade and recovery steps. Optional
`AI_LAB_DECISIONS_MODEL` selects a name from its decision-model list;
`AI_LAB_DECISIONS_API_KEY` supplies local server authentication.

**CLM upstream** runs the unmodified upstream API, schema, projection heads, and
probability calculation at revision `bb42c6c5bf914fd449bed2f6ca65be80602cb1f7`.
Install its shared weights and isolated environment through the CLI:

```sh
ai-lab weights install clm
```

An open Decisions page refreshes available models automatically. Select **CLM upstream**
in Decisions and press Run; the website starts the reference API on loopback
port 8700 and its independent Qwen3-8B encoder on port 8090. The encoder uses
Transformers/PyTorch on the Mac's MPS device, raw text tokenization, causal
attention, bfloat16 weights, and last-token pooling. Upstream's documented
vLLM/CUDA encoder requires Linux and an NVIDIA GPU, so this is an independent
Mac reference rather than a reproduction of that CUDA backend. Both CLM
implementations reuse the local Qwen weights and published checkpoint, without
sharing inference code or computed embeddings. The preset text and question
criteria stay unchanged when switching models.

The source archive is pinned by revision and SHA-256; setup does not install
vLLM or change the application's Python environment. API and encoder logs are
`.state/clm-upstream.log` and `.state/clm-upstream-encoder.log`. An owned server
stops with the website. To run it separately (including its original playground
at `http://127.0.0.1:8700/`):

```sh
.venv/bin/python harness/clm_upstream.py serve
```

For an already-running upstream API, set `AI_LAB_CLM_UPSTREAM_URL` to its
loopback HTTP origin before launching the website. It must expose `clm-latest`;
the raw-embedding ablation and native Mistral server cannot substitute for it.
`AI_LAB_CLM_UPSTREAM_API_KEY`, if needed, stays on the website server.

**Laya (ONNX)** uses [@receptron/laya](https://github.com/receptron/laya), version
0.1.2, in an independent local Node.js server. It loads the pinned English
`receptron/laya-onnx` bundle at revision
`68f27dfe5a27a54fb2b1fefc432f43f972e90868` through ONNX Runtime 1.22.0 on the CPU.
Install explicitly with `ai-lab weights install laya` or choose it in `ai-lab weights`.
The package, locked npm dependency graph, server code, and manifest live under
`.runtime/decisions/laya/`; weights live under `.models/laya/`.

Selecting Laya and pressing Run starts its server on loopback port 8710 and uses
the same state, questions, criteria, and ranking editor. Model loading uses
local files, with no implicit model downloads during requests. An owned server
stops when the website exits; its log is `.state/laya.log`. For an external Laya
server, set `AI_LAB_LAYA_URL` to its loopback HTTP origin, with optional
`AI_LAB_LAYA_API_KEY`. That server must expose `laya` at `/v1/models` and accept
`/v1/systemone` requests. The bundled server identifies its workspace to prevent
reusing a different workspace's model process.

The English checkpoint fits each state-plus-question into 512 tokens and
reserves 192 tokens for the question/options header. It truncates long states
using the upstream package's behavior; options that cannot fit return an error.
Probabilities retain the package's four-decimal precision.

**Jev** is configured automatically when `ai-lab web` finds a nonempty
`TYPESAFE_API_KEY` (or `JEV_API_KEY`) in your launch environment. The CLI syncs
it to `.state/ai-lab/jev-api-key` with owner-only file permissions (0600) in the
private workspace state directory (0700), including when it reuses an existing
website. The website reads the latest key for discovery and each Jev request;
enabling or rotating a key does not require a website restart. Launching from
an environment without a key preserves the previously synced key. The saved
key stays in the workspace's ignored `.state/` directory, outside UI assets,
logs, command arguments, and API responses.
An open Decisions page checks available providers on focus and every ten seconds,
so model installs and CLI credential handoffs appear without a manual reload.
Selecting Jev and pressing Run sends the state and questions to TypeSafe's
`https://api.typesafe.ai/v1/systemone` with `jev-latest`. Credentials stay on the
server. Contrastive requests never use that endpoint. Provider failures are
shown directly; they do not cause automatic fallback to another model.

The API is discoverable in `/docs` and `/openapi.json`:

- `GET /api/decisions/models` lists available choices without credentials.
- `POST /api/decisions/systemone` accepts `model` (`contrastive`, `clm-upstream`, `laya`, or `jev`),
  `state`, and named `questions`.
- `POST /api/decisions/rank` accepts `model`, `context`, optional `question`,
  and an `answers` array. It uses a Choice question and returns ranked candidates.

Native CLM allows 2048 tokens per state-plus-question or candidate. Requests
larger than 100 KB are rejected before contacting either provider. The local
model uses the original Qwen3-8B encoder and published CLM heads.

## MCP for agent clients

Python chat hosts can launch AI Lab's own MCP server without a config file,
with optional external stdio servers and approval-aware tool continuation.
See [the local MCP connector](mcp-client.md) for its configuration and interface.

```sh
ai-lab mcp install --codex
ai-lab mcp install --claude
# Also available: --claude-desktop, --cursor, --opencode
```

The client launches a Python stdio MCP process on demand with `uvx`. No website,
CLI daemon, or separately managed MCP listener is required. `uvx` must be
installed before the client launches MCP; Homebrew installs it as a runtime
dependency. The first connection installs Python 3.13 if necessary and resolves
the MCP package dependencies. It never downloads model weights implicitly.

The installer follows the client-config approach used by
[jev-mcp-server](https://github.com/wangkuangkuang/jev-mcp-server), using each
client's stdio format. It stages a reproducible wheel containing this installed
AI Lab release's public Python code and app assets in the workspace. The `uvx`
entry points to that wheel, so the setup works before PyPI publication and
survives Homebrew removing an older Cellar. Weights, saved prompts, results and
credentials are excluded from the wheel. Keep the selected workspace available.
After updating the CLI, rerun `mcp install` with `--force` to update its snapshot.
Existing MCP connections should be restarted after installation.

| CLI target | Default user config |
| --- | --- |
| `--codex` | `$CODEX_HOME/config.toml`, or `~/.codex/config.toml` |
| `--claude` (Claude Code) | `~/.claude.json` |
| `--claude-desktop` | `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS |
| `--cursor` | `~/.cursor/mcp.json` |
| `--opencode` | `$XDG_CONFIG_HOME/opencode/opencode.json`, or `~/.config/opencode/opencode.json` |

Other settings and MCP servers are preserved. Edited configs receive a private
backup; Codex TOML comments are preserved too. A different existing `ai-lab`
entry requires `--force`, which replaces only that entry. Installation leaves
the client's tool approval settings under its existing policy.

```sh
ai-lab mcp config --codex --json            # inspect the entry without editing a client config
ai-lab mcp install --claude --scope project # writes .mcp.json in this workspace
ai-lab mcp install --codex --force          # update an existing entry after a CLI upgrade
ai-lab --root /path/to/deepseek mcp install --cursor
ai-lab mcp install --codex --config-file /path/to/config.toml
```

Project scope supports Codex (`.codex/config.toml`), Claude Code (`.mcp.json`),
and Cursor (`.cursor/mcp.json`). `--package` can override `uvx --from` with a
published package spec or wheel URL instead of staging the installed CLI.

Jev is the default decision provider and needs no local process or weight
download. The installer saves an available `TYPESAFE_API_KEY` or `JEV_API_KEY`
privately in the workspace, just like the web launcher. The client configuration
contains only the workspace path, never the API key. MCP reads the saved key on
each request, so a later installation or web launch can rotate it without
restarting MCP. With no saved key, MCP can use a key inherited from its client.
Jev stays in the catalog when credentials are absent and reports that it needs
configuration; it does not fall back to a local model.

Start local model APIs yourself in a separate terminal:

```sh
ai-lab services --action list --json                 # includes undownloaded/stopped models
ai-lab weights install laya --yes
ai-lab services                           # opens the model-aware manager
ai-lab services --action start --model laya                     # one API
ai-lab services --action start --model deepseek                 # one shared API
ai-lab services --action start --model contrastive             # native CLM
```

Explicit start/restart stays in the foreground. Ctrl+C stops only APIs it owns,
leaving borrowed APIs alone. Opening the manager discovers services without
starting or downloading them. Script mutations require one explicit target.
Several saved profiles share one backend API. Stop/restart/interrupt require
verified workspace identity; interrupt stops the entire owned service.

DeepSeek and Qwen APIs started by another launcher are reused only when their
saved launch settings, binary hash and loaded chat-template hash match the current
version. After upgrading, an API with missing or older template identity is
reported as unavailable even if it still responds as `default`. Stop that API
through its original launcher (Ctrl+C in that terminal), then run
`ai-lab services --action start --model deepseek` or `ai-lab services --action start --model qwen` again. Updating the
template file alone cannot change a running model's in-memory template. AI Lab
does not stop or restart another launcher's API to repair this mismatch.

`--jev` needs no local process. Local inference uses the same pinned runtimes,
weights, loopback endpoints and logs as the website. `weights install clm`
provisions both native and upstream CLM runtimes. When existing CLM weights are
present, `services --action start --model contrastive` repairs a missing native runtime automatically.

MCP probes and calls already running model APIs. It never starts a local model
or the CLI daemon, including during a download tool call. The website retains
its existing model launch behavior. Both CLMs can require substantial memory
when started together because they each load their own Qwen encoder.

| MCP tool | Operation |
| --- | --- |
| `list_models` | Lists all six backends, installed/running status, missing weight sizes, launch commands, and saved profiles. |
| `create_seeded_model` | Creates a named DeepSeek or Qwen profile with a decimal or hexadecimal seed. |
| `create_watermarked_model` | Creates a persistent DeepSeek or Qwen profile with a scheme, optional seed, optional key, and overridable settings. |
| `get_model_config` | Reads all saved profile settings; `include_watermark_key=true` explicitly retrieves its watermark key. |
| `update_watermarked_model` | Saves partial key, scheme, or setting overrides for future sessions while preserving the model ID, name, and seed. |
| `generate_text` | Generates actual text with DeepSeek/Qwen or a saved profile, inheriting its seed/watermark with optional unsaved overrides. |
| `detect_watermark` | Tests supplied text using a saved profile or explicit DeepSeek/Qwen scheme/key; returns a verdict, confidence, p-value, token count, and native evidence. |
| `download_models` | Downloads missing weights, verifies/resumes files, and installs server dependencies. Both CLMs share one weight family; Jev has none. |
| `explain_watermarks` | Explains the six schemes, exact fields, and linked papers, including membership and tournament differences. |
| `answer_decisions` | Answers named Noul, Choice or Score questions via Jev by default, or explicit `laya`, `contrastive`, or `clm-upstream`. |
| `rank_decisions` | Ranks candidate actions/answers through the selected provider's Choice API. |
| `inspect_next_token` | Uses a saved DeepSeek/Qwen profile and exact raw prefix, with optional per-call scheme/key/settings overrides, then saves the native trace and returns an `inspection_id`. |
| `list_results` | Lists saved MCP inspections, CLI sessions and website watermark experiments with their source IDs. |
| `get_green_red_lists` | Returns captured native token membership, optionally for a SynthID layer, with capture limits. |
| `get_tournament_results` | Returns the saved production tournament and any separate teaching simulation. |

Profiles share `harness/models.json` with the website and terminal interface;
they select either DeepSeek or Qwen weights through `underlying_model`. If the website is running,
profile creation and updates use its publication transaction. Without it, they
write the registry directly under the workspace lock. Restart a website launched
with an older CLI before updating profiles through MCP. New SynthID profiles
default to depth 4 and production tournament generation.

Every supported watermark setting is overridable through `settings`; use
`explain_watermarks` for each scheme's fields and validated ranges. A `key` must
contain 64 hexadecimal characters. An explicit tool `key` overrides `settings.key`;
otherwise saved profiles reuse their key, and creation generates one if absent.
The key and resolved settings are stored in `harness/models.json` with mode `0600`
and survive client restarts. Ordinary responses hide the key; request
`get_model_config(model="my-model", include_watermark_key=true)` to retrieve it.
This option returns only the watermark key, never Jev/API credentials.

For example, these MCP calls create a profile, save a change, and detect text
using that profile's persisted key and settings:

```text
create_watermarked_model(name="my-model", scheme="kgw", settings={"delta": 3})
update_watermarked_model(model="my-model", settings={"green_fraction": 0.25})
detect_watermark(text="...", model="my-model")
```

To test text from elsewhere, pass `model="deepseek"` or `model="qwen"`, its original `scheme`,
`key`, and matching `settings`. Detection and `inspect_next_token` accept
per-call overrides without changing the profile. `update_watermarked_model`
saves changes for future sessions; omitted fields retain their saved values.
Changing schemes retains the key and resets scheme-specific fields. Existing
generation sessions keep their original configuration snapshots.

Detection uses the selected native backend tokenizer/API, which must already be running.
It returns `matches`, `verdict` (`match`, `no_match`, or `insufficient`),
`tokens_scored`, `p_value`, `confidence`, and `stats`. Confidence is `1 - p_value`
from a known-key statistical test or conservative bound, not a posterior
probability of authorship. The defaults are `p_value_threshold=0.001` and
`min_tokens=20`; these, `prompt_len`, `eos_token_ids`, and `add_special_tokens`
can all be overridden. Short or unscorable text reports `insufficient`.

The website's **Watermark decoder** at `/decoder` (also `/detection`) exposes this
same detector for pasted text and named generation profiles. Select the profile
that generated the text: its saved scheme/settings are displayed, while its key
stays on the server. A scheme change or explicit key/settings override affects
only the current decode; it never saves profile changes. **Restore profile
settings** clears overrides. Changing models resets the configuration and
preserves the pasted text. For a plain profile, supply the original scheme and
key; the decoder never creates one. Start the selected API manually with
`ai-lab services --action start --model deepseek` or `ai-lab services --action start --model qwen` if the page asks.
Results show the effective model/scheme, native statistics, known-key confidence
and p-value, or insufficient evidence. Edited text/configuration marks previous
results stale; an API failure leaves the inputs and last successful result
available for retry. The optional generation/edit/inspection experiment remains
below the decoder. HTTP fixture results are explicitly labeled and are not
native model evidence.

Decision models such as Jev, Laya, and CLM do not generate text watermarks.

For trace tools, pass the `inspection_id` as `source_id`, or use `list_results`
to select a CLI `session` or website `watermark` source. Website watermark
experiments also require their `agent_id`. Steps are zero-based. Green/red lists
cover captured membership, not the full vocabulary. SynthID defaults to the
last captured probability layer or production round. In a production round,
green/red entries are actual tournament entrants with their native `draw_id`
and `g_value`; candidates without captured scores are reported separately.
Truncated or absent tournament matches are reported
directly and never reconstructed. No running API is required to read saved results.
With SynthID's default five-token n-grams, prefixes shorter than four tokens
report warmup and do not produce a production bracket.

For SDK development and a real isolated `uvx` stdio smoke check:

```sh
uv sync --frozen --extra mcp
.venv/bin/python packaging/check_mcp.py
```

## Run from this repository

```sh
uv sync --frozen
./ai-lab                        # canonical public launcher
./ai-lab models                 # interactive model configuration
./ai-lab completion --model seed-1 --scheme synthid
```

Bare `ai-lab completion` opens Completion with an in-screen saved-model picker.
`--name "Model name"` or `--model ID_OR_NAME` preselects a saved model; `--session ID`
resumes an existing session. Switching back to a model reuses its session in this
screen. Refresh preserves recorded results and the current unsent prefix. With
no saved models, open `ai-lab models`, create one, and Refresh. Opening does not
create a profile or generate tokens. Backend errors stay visible in the screen.

The workspace has a prompt/answer editor, probability bars, a scrollable native
bracket, and selectable tokens. `Ctrl+Enter` runs, `Ctrl+A` appends the selected
token and inspects again, `Ctrl+S` stops after the current token, `F1` opens help,
`F2` focuses the model picker, `Ctrl+P` returns to Completion, `Ctrl+T` shows the
bracket, `Ctrl+O` shows probabilities, and `Ctrl+K` shows tokens. `F3` and `F4`
focus the captured-step and probability-layer selectors in every view, including
standalone panes. `F5` focuses the current panel's scrollable details; use arrows,
Page Up/Down, Home/End or the mouse to read them. `Ctrl+Q` closes the pane.
Small windows switch to one panel at a time with view buttons; short panes retain
compact Run, Append, Stop and token-count controls. Closing a pane does not stop
its session or the background service.

Selecting a match shows its recorded scores, winning draw, tie-break reason and
input draw probabilities. Enter on a draw inspects its token; Append is a
separate action. Inspection never changes the recorded winner. Token details
show captured final log probabilities when available, explicitly labeled as final
even while viewing a probability layer. Tournament sampling has no captured
final marginal probability or log probability; unavailable values remain marked.

A plain `ai-lab` prints the thirteen canonical public surfaces. Explicit
`ai-lab weights --setup` runs setup. Setup explains the
5.03 GB weight download, downloads the pinned prebuilt Metal runtime,
and verifies model, tokenizer, template, archive, and binary hashes. It needs
Apple Silicon and macOS 15 or newer. Users do not need Xcode, the Metal developer
toolchain, Rust, Docker, or OpenCode. Homebrew manages Python and the CLI's own
dependencies. A package installation does not silently download weights.

Both public forks are compiled into the server at their exact `sources.json`
commits. Metal kernels use the macOS Metal framework on first use; no developer
tools run on the user's machine. The release binary links only to macOS system
libraries. `ai-lab weights --doctor --json` reports the supported OS and download size.
The first server startup prepares Metal kernels and can take several minutes.

## Homebrew

AI Lab has its own [Homebrew tap](https://github.com/iamorlando/homebrew-ai_lab).
The Homebrew package is named `ai_lab`; the executable is `ai-lab`.

```sh
brew tap iamorlando/ai_lab
brew trust --formula iamorlando/ai_lab/ai_lab
brew install ai_lab
ai-lab
```

The repository also provides an install/update wrapper that offers model downloads
immediately after Homebrew finishes:

```sh
sh packaging/install.sh install
sh packaging/install.sh update
# Explicit choices for automation:
sh packaging/install.sh update --yes
sh packaging/install.sh update --no-models
```

Bare `brew install` / `brew upgrade`, direct wheel installation, and ordinary
CLI launches do not offer model downloads. Open `ai-lab weights` or run
`ai-lab weights offer` explicitly. The wrapper's `--yes` explicitly accepts the
weights offer; its default prints the weights-manager instruction.

For a direct package install, download the wheel from the
[release](https://github.com/iamorlando/homebrew-ai_lab/releases/latest), then run:

```sh
uv tool install --force --python 3.13 ./ai_lab-0.1.14-py3-none-any.whl
uv tool update-shell                  # if the executable directory is not on PATH
ai-lab --version
ai-lab weights offer                # optional models; keyboard picker
```

Installed copies store data in `~/.local/share/ai-lab` (or `AI_LAB_HOME`). Source
runs default to this checkout. To share website models and the existing DeepSeek
installation, pass `--root /path/to/deepseek` before the subcommand or export
`AI_LAB_ROOT`. Runtime paths remain outside Homebrew's Cellar and survive upgrades.

Root selection stays deterministic: global `--root` wins over `AI_LAB_ROOT`.
Source runs otherwise use the checkout; installed runs use `AI_LAB_HOME` when set,
then `~/.local/share/ai-lab`. An explicit root or either environment override never
silently falls back to another root. Inspect the exact selected root and missing
filenames with `ai-lab weights list --json`; normal list output also distinguishes
verified weights from runtime setup.

When files are absent at the installed default, the picker/status can point to
size-matching files in the source checkout, `~/dev/deepseek`, `~/dev/ai_experiments`,
or the installed default. These hints are **unverified** until their SHA matches.
For another prior location, put at most eight absolute paths in a JSON array at
`<selected-root>/.state/ai-lab/model-roots.json`. Discovery inspects these exact
locations only. Choose a root with `ai-lab --root /path weights list --json`.
Accepted setup at the default installed root can attach checksum-verified model
files from a single known root using symlinks. Keep that source directory available.
It never moves or deletes the source weights, imports its runtime metadata, or
merges profiles/secrets. Existing target files/partials stay untouched by reuse;
ambiguous roots and wrong hashes require an explicit choice. Custom manifests and
templates remain user-owned and disable automatic attachment.
Initialization and automatic repair reject links below the selected root in
managed state/profile paths before writing files or changing directory modes.
This includes `.state`, `.state/ai-lab`, `harness`, and `harness/models.json`, even
when a link is dangling. Model startup/discovery use the same early boundary;
foreign cache/profile trees stay untouched. An explicitly selected root may itself
be a link to the workspace you chose.

Verification uses private receipts in
`<selected-root>/.state/ai-lab/weight-verification.json` (file mode `0600`, directory
`0700`). Unchanged files reuse the prior checksum across CLI launches. Receipts
include the resolved path, catalog digest, device/inode, size, and nanosecond
mtime/ctime. A first check or changed file is hashed again; large checks announce
the verification. These receipts trust the local cache owner, not arbitrary public
or symlinked cache files. Removing the receipt triggers fresh verification.

## Update an existing installation

```sh
brew update
brew upgrade iamorlando/ai_lab/ai_lab
ai-lab --version                      # target: AI Lab 0.1.14
ai-lab weights offer                  # optional downloads / runtime repairs
ai-lab mcp install --codex --force     # refresh this client's packaged tools
```

Restart your MCP client after refreshing its entry. Stop an older website with
Ctrl+C in its launch terminal, then start `ai-lab web` again. Homebrew upgrades
preserve downloaded weights, saved profiles, watermark keys, and results outside
its Cellar. Open `ai-lab weights` explicitly after installing/upgrading to
inspect available models. Hosted Jev remains available with its configured key. MCP never starts local model APIs automatically.
Completion negotiates supported older same-owner application APIs automatically;
routine updates do not require manually stopping that API or deleting its state.
See [Updating AI Lab](upgrading.md) for the full recovery and cleanup steps.

Verified weights with an outdated runtime are not missing downloads: status shows
`weights_present: true`, `missing_bytes: 0`, and `dependencies_ready: false`.
The explicit offer includes both missing/invalid weights and downloaded models
that need runtime repair. Select only the models you want; verified files are
reused unchanged. `ai-lab services --action start --model deepseek` (or `--model qwen`) can repair only their shared
published, checksummed runtime before starting the owned API, with no weight or
asset download and no compilation. Custom source/runtime overrides need explicit
setup. A running borrowed API is left alone; port/process ownership checks remain
in effect. Missing/corrupt weights produce a root-specific error listing files.
The older CLM Qwen safetensors are encoder weights; Qwen completion still needs the
distinct `Qwen3-8B-Q4_K_M.gguf` (5,027,783,488 bytes). Shared tokenizer/config files
are reused.

Release storage proof is self-contained for tap CI:
`/installed/venv/bin/python -I packaging/check_storage.py` (or pass `--python` to
the script). It exercises tiny scratch weights, an in-memory runtime artifact,
bounded reuse, and fresh-interpreter receipts. It makes zero weight-download calls,
real network requests, model starts, GPU or SDK calls, and imports no source tests.

Normal setup downloads a verified prebuilt runtime instead of compiling on the
user's machine and reuses existing verified files. Both public forks retain
their pinned revisions. Setup updates an unchanged 0.1.0 source manifest while
preserving saved data. Custom source manifests remain under your control.

Developers with custom runtime pins can opt into compilation:

```sh
ai-lab weights --setup --build-from-source --yes
```

Source builds require Rust via rustup and Apple's Command Line Tools. Full Xcode
is not required. `--use-local-source` also selects this path and records local
source provenance. Normal setup never silently falls back to a source build.

## Models

The interactive editor uses the website's field metadata: name, DeepSeekR1 or Qwen3-8B,
optional decimal/hexadecimal seed, scheme, generated or supplied key, and each
scheme's settings. Names are unique; seedless profiles remain seedless. Selecting
a saved profile displays its settings; **Completion** launches its token workspace; **Save settings** updates backend/watermark settings while preserving its name and seed; change the name to make a copy. Deleting a
profile preserves recorded sessions, but that profile cannot start new runs.
See [model profiles and watermarking](model-profiles.md) for choosing either
family, creating watermarked profiles, and an isolated installed-package check.

```sh
ai-lab models list --json
ai-lab models create --name seeded --seed 0x600D_C0FFEE --json
ai-lab models create --name marked --watermark-file watermark.json --json
ai-lab completion --schemes --json
```

A session requires a saved profile. Use `--name 'My model'` to select its exact
name (including case), or `--model MODEL_ID` for its ID. `--model` retains legacy
exact-name support. Do not combine these flags. Names remain unique without
regard to case when profiles are created; selection uses their saved spelling.
Unknown or ambiguous selections fail with guidance to list models. Use
`--session-name experiment` to label the new session; session commands previously
used `--name` for this label. `models create --name` still names the new profile.
`--scheme model` (the default) inherits its saved watermark. `--scheme none`
disables watermarking. A named scheme reuses matching profile settings or creates
fresh temporary settings and a key. Fresh SynthID sessions default to actual
tournament sampling at depth 4. Existing profiles retain their policy and depth.
`--watermark-file` overrides settings for the explicitly named scheme. Session
configuration remains fixed; make a new session to change it.

## Separate tmux or Herdr panes

```sh
ai-lab completion --session-action create --name seeded --scheme synthid --session-name experiment --json
# Use the returned id for every pane:
ai-lab completion --view chat --session SESSION_ID
ai-lab completion --view tournament --session SESSION_ID
ai-lab completion --view probabilities --session SESSION_ID
ai-lab completion --view tokens --session SESSION_ID
```

Or create the layout automatically:

```sh
ai-lab completion --layout tmux --name seeded --scheme synthid --launch --json
# The result includes the tmux attach command.
ai-lab completion --layout herdr --name seeded --scheme synthid --launch --json
```

Herdr must already have a running session. Both layout commands print their plan
without opening panes when `--launch` is omitted. The commands use quoted argument
lists, so model/session values are not interpreted as shell fragments. Existing
panes and workspaces are not replaced. All AI Lab panes follow the same selected
step and token. Selecting an alternative never changes the recorded winner.

The bracket follows recorded source IDs. Duplicate draws remain distinct, missing
matches are labeled, and collapsed subtrees show the real advancing draw. Capture
is bounded at 255 matches; it never changes generation depth. Actual tournaments
have no computed marginal after-watermark distribution, so those values display
as unavailable. Full-vocabulary model probabilities are never normalized over only
the captured alternatives. The probability round selector exposes captured SynthID
updates, and the token table labels green/red or favored/unfavored membership. Token text is escaped so leading spaces stay visible.

## Automation and API discovery

For multi-turn local assistant chat, choose a saved model:

```bash
ai-lab models list --json
ai-lab chat --name "Model name"
# Or select a built-in generation family:
ai-lab chat --model qwen
ai-lab chat --model deepseek
```

Start the selected native API in another terminal with `ai-lab services --action start --model qwen`
or `--model deepseek`. The agent reports an unavailable model with its launch command;
it never starts/downloads a model or switches to a hosted service. `--name`
selects an exact saved profile and inherits its seed and watermark settings.
Use the name exactly as saved, including case, and choose either `--name` or
`--model`. These generation families/profiles are separate from decision providers
such as Laya, native/upstream Contrastive and Jev.
`--scheme none` disables watermarking for this chat without changing the profile;
`--seed`, `--watermark-file`, `--temperature` and `--max-tokens` are unsaved overrides.
The window shows the selected profile, backend and watermark scheme. It displays
progress while waiting for the native response and retains successful conversation
history. Stop with Ctrl+C/Escape and exit with Ctrl+Q. Failed/canceled turns stay
visible and are excluded from subsequent history. `ai-lab completion` provides
the next-token inspection workspace.

In Herdr, the running agent automatically reports lifecycle state in the current
pane. No flag is required. To open a separate tab instead, optionally use
`ai-lab chat --name "Model name" --herdr-tab`; add `--json` only when you
need the new tab/pane identifiers for automation.

Optional `--self-mcp` connects the shipped AI Lab MCP server without a config file:

```sh
ai-lab chat --name "Model name" --self-mcp
```

Its decision tools require an explicit local provider (`laya`, `contrastive` or
`clm-upstream`) and a separately running local API. The assistant requests real
tools through native tool calls, receives actual MCP results and continues the
answer. Each call asks Allow/Deny unless its exact own tool name was explicitly
preauthorized with `--allow-tool TOOL`. For example,
`--self-mcp --allow-tool answer_decisions` preauthorizes only that own tool.
`--mcp-config FILE` optionally connects external stdio servers; combine it with
`--self-mcp` to include both. No hosted key is needed for the built-in offline
connection.

Tools default to `auto`: the model decides whether to call a function and may
reply with text. Select `--tool-choice required`, click the window's visible
Tools control, or press Ctrl+T to require at least one native tool call for the
next submitted user turn. Required needs a configured MCP connection and still
uses ordinary validation and Allow/Deny. The visible choice remains selected
for subsequent user turns until you switch it; it is locked while a turn runs.
Only that turn's first native request uses required. Requests after actual tool
results use auto so the assistant can answer. Empty discovery or a required
response without genuine calls fails visibly without dispatch or automatic retry.
Plain chat remains available with no MCP connection.

Native tool-call enforcement does not guarantee correct arguments or sound
model reasoning. Inspect returned tool evidence and visible failures when
assessing an answer.

Custom AI Lab agent windows in Herdr use an explicit prompt bridge:

```bash
ai-lab chat --pane PANE_ID --prompt "Your message" --wait --timeout 30 --json
```

Use `--session-id UUID` to require a known chat session, or `--prompt-file FILE`
(`-` for stdin) to preserve a longer prompt. The bridge checks the exact live
AI Lab pane/session and its private input channel, then submits to the app.
It rejects busy, blocked, stale and exited targets. It never writes prompt text
to a terminal or falls back to a shell. The reply identifies the accepted request
and session; `--wait` observes working followed by settlement, or a real approval
block. A timeout is an uncertain outcome: inspect the window before retrying.
Delivery uses the target window's visible Tools choice, with no hidden mode
change. `--herdr-tab` preserves the launch command's `--tool-choice` option.

Herdr 0.9.1 supports the `ai-lab` custom lifecycle label but its native
`herdr agent prompt` accepts only built-in agent kinds. Use the bridge above
for custom AI Lab windows. A pending tool approval must be answered in the
window's Allow/Deny dialog. Stop with Ctrl+C or Escape; exit with Ctrl+Q.

Inspired by Herdr's [CLI](https://herdr.dev/docs/cli-reference/) and
[socket API](https://herdr.dev/docs/socket-api/), AI Lab exposes structured commands,
a versioned local API, persistent sessions, shell completion and an agent guide:

```sh
ai-lab --json
ai-lab completion --api-schema
ai-lab --skill
ai-lab completions zsh > ~/.zfunc/_ai-lab
```

`completion --api-schema`, `--skill`, help, and shell-script generation work before setup and do
not launch a server. Dynamic shell completion suggests saved names for `--name`,
model IDs for `--model`, and session IDs from a running service without starting
one. Names with spaces complete as a single value. `models create --name` accepts
a new name and does not suggest saved profiles.
Dynamic lookups honor the global `--root PATH` or `--root=PATH`; quote workspace
paths containing spaces to complete names and session IDs from that workspace.

```sh
ai-lab completion --name seeded --scheme synthid \
  --prompt 'the quick brown fox jumps over the lazy' --json
ai-lab completion --session SESSION_ID --prompt-file prefix.txt --no-wait --json
ai-lab completion --session-action wait --session SESSION_ID --timeout 1200 --json
ai-lab completion --session-action get --session SESSION_ID --json
ai-lab completion --session-action select --session SESSION_ID --step 0 --token-id 5562 --revision REV --json
ai-lab completion --session-action append --session SESSION_ID --revision REV --json
ai-lab completion --session-action stop --session SESSION_ID --json
```

An existing session keeps its profile, scheme, and temperature. Do not supply
`--name` or `--model` when using `--session`; create a new session to change models.

`--prompt-file -` reads stdin without trimming whitespace. The default is one
next-token decision, matching the website. `--max-tokens 1..256` repeats inspection
on the growing raw prefix and updates attached panes after each decision. Each
prefix is retokenized and a fixed model seed resets for each decision; this is not
a continuous native sampling request. Position-based watermark schemes advance
with each appended token. A new prompt resets the position.

Session mutations can use a revision to reject stale pane actions. Selection and
append require a revision; complete optionally takes `--revision`. JSON success
goes to stdout; JSON errors go to stderr with exit 1 (invalid command syntax uses
exit 2). A wait timeout leaves generation running. Stop finishes the in-flight
native decision before releasing the shared inference lock.

`ai-lab completion --api-call METHOD /api/lab/... --body-file request.json` invokes the same
endpoints as the TUI. `completion --api-snapshot` lists models and sessions. Session responses
omit watermark keys; model configuration responses include them for editing.
To create a session directly, send either `{"model_name":"seeded"}` or
`{"model":"MODEL_ID"}` to `POST /api/lab/sessions`. Exactly one selector is
required; the JSON field `name` continues to label the session.
Session files have mode 0600 inside a mode-0700 directory.

## Service lifecycle

When the website is running at port 8080 for the same root, AI Lab attaches to its
`/api/lab` endpoints and shares its model-publication and generation locks. Restart
an older website process once to load the new routes. For other ports, set
`AI_LAB_SERVER=http://127.0.0.1:PORT` and use the matching root.

Otherwise AI Lab automatically starts a private Unix-socket service. Inference
starts only when a completion needs it. Commands verify the service's application,
API version and root before attaching. Startup and daemon locks prevent duplicate
services, and each workspace has its own socket. A long root path uses a private,
user-owned socket directory in `/tmp`. State remains under `ROOT/.state/ai-lab`.

```sh
ai-lab weights --doctor --json
ai-lab completion --service-action status --json
ai-lab completion --service-action stop
```

Only an idle, private AI Lab service can be stopped this way. It leaves the
inference runtime available for other local clients. The website uses its own
launcher. If it starts after the private service, it forwards AI Lab requests to
that existing session owner. A shared file lock serializes configuration and
completion work across both processes; CLI model writes publish through the live
website so its aliases remain current. For a custom website port, set
`AI_LAB_SERVER` before starting the private service as well as in CLI shells.
Read-only requests reconnect after a service transition. Mutations are never
automatically replayed. Incomplete runs are marked interrupted on recovery. Logs are in `.state/ai-lab/server.log` and
`.state/mistral-server.log`.

## Build, test and release

Build the runtime from the exact public forks with the tap's `Build pinned
runtime` workflow (`packaging/runtime/build.yml`). It targets Apple Silicon
macOS 15, links only system libraries, and uses `MISTRALRS_METAL_PRECOMPILE=0`
so Metal kernel compilation uses the OS framework. Copy the resulting runtime
descriptor to `ai_lab/runtime.json`, adding the immutable release asset URL.
The same workflow builds the independent native CLM server from
`packaging/runtime/contrastive-sources.json`; its descriptor lives at
`ai_lab/decisions-runtime.json`. To build it locally:

```sh
python3 packaging/runtime/build.py --kind contrastive \
  --sources packaging/runtime/contrastive-sources.json \
  --checkout .runtime/contrastive-release/forks --output .runtime/contrastive-release/dist
```

Publish `ai_lab-contrastive-runtime-macos-arm64.tar.gz` at the descriptor's
immutable release URL before publishing the CLI that refers to it. The CLM
runtime is installed independently of the completion runtime and has its own
source pins, executable checksum, and `decision_support` provenance check.
Publish the runtime archive with the application artifacts; its SHA-256 and
both source pins are checked before the executable can replace an installation.

```sh
uv sync --frozen
uv run python -m unittest discover -s tests/ai_lab -v
uv run python -m unittest discover -s harness/tests -p 'test_*.py'
uv build
python3 packaging/homebrew/generate.py dist/ai_lab-0.1.14.tar.gz --version 0.1.14
```

The generator writes `dist/homebrew/ai_lab.rb` with the actual archive checksum and
the dedicated AI Lab tap release asset URL. The archive excludes saved model profiles
and state; the wheel bundles only shared backend code and pinned public assets.
Publish the exact archive at that URL, then copy the generated formula into the
AI Lab tap's `Formula/ai_lab.rb`. No repository push or release is automatic.
For a local Homebrew build, pass `--url file:///absolute/path/to/archive.tar.gz` to
the generator and use the resulting formula in a local tap. Rebuild and regenerate
if any release content changes.

Generation profiles persist `underlying_model: DeepSeekR1` or `Qwen3-8B`; the CLI also accepts `deepseek` and `qwen`. Existing IDs, seeds and watermark keys are preserved. Select the backend when creating a profile on the Models page or in the TUI. On the website, the model row’s backend selector updates that profile without changing its key or watermark configuration. Raw next-token inspection offers the same two backends. Qwen tokenizer/config assets are shared with the CLM encoder, but generation readiness requires the separate official GGUF weights and verified completion binary. Each API refuses a port owned by another workspace and its launcher stops only processes it started.

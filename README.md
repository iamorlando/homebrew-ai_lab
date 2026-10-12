# AI Lab

A local web app for DeepSeek and Qwen3.8-27B generation, CLM decisions, and MCP tools for agent clients.

```sh
brew install iamorlando/ai_lab/ai_lab
ai-lab setup install deepseek clm --yes
ai-lab web
```

For an existing installation:

```sh
brew update
brew upgrade iamorlando/ai_lab/ai_lab
ai-lab --version
ai-lab web
```

Version 0.1.17 adds Qwen3.8-27B and starts model APIs on demand. Stop the older AI Lab
launcher before opening the updated website. Keep your existing data directory;
this update does not require deleting profiles, keys, sessions or weights.

Opening the website loads no model. Select DeepSeek or Qwen3.8-27B for generation,
or CLM for Decisions; the selected installed API starts when first used and remains
available until the web process exits. Keep its terminal open while using the app. Compatible downloaded weights are reused.
Missing weights are installed explicitly with `ai-lab setup install FAMILY --yes`; opening the website
does not silently download models.

- **Completion:** the existing token probabilities, tournament and completion view.
- **Decisions:** typed Ask and Rank requests with native CLM or Jev.
- **Watermark decoder:** generate from a named model on the left; copy or paste
  text on the right and inherit the writing model's watermark configuration.
  Change the decoding model, scheme, key or settings to compare results.
- **Models:** create and configure saved DeepSeek or Qwen3.8-27B profiles.

Install Qwen3.8-27B with `ai-lab setup install qwen38 --yes`, then select it in
Completion or when creating a model. MCP accepts `model="qwen38"` or a saved
profile. Qwen3.8-27B is separate from CLM and its older Qwen3-8B encoder files.

The public commands are `web`, `mcp`, `setup`, and machine-oriented `services`. Terminal screens and the
Comparison and Watermarking pages have been removed. The Completion page remains
unchanged; Decisions retains its existing controls with CLM and Jev.

Jev uses `TYPESAFE_API_KEY` or `JEV_API_KEY`. The key stays on the server.
CLM runs locally using the pinned Mistral runtime and its CLM/Qwen weights.
If CLM cannot fit in memory, restart its launcher with
`AI_LAB_CLM_ISQ=q4k ai-lab web` to quantize the encoder while loading. Existing
weights remain unchanged. Qwen3.8-27B reports an actionable startup failure if
it cannot run on the machine; selecting it never silently falls back to DeepSeek.

```sh
ai-lab mcp install --codex
ai-lab mcp install --claude
```

See the [usage guide](docs/ai-lab/README.md),
[upgrade instructions](docs/ai-lab/upgrading.md), and
[release test matrix](docs/tests.md).

Models, keys and sessions default to `~/.local/share/ai-lab`, outside Homebrew's
Cellar. Keep `AI_LAB_ROOT` or `--root` unchanged when using a custom workspace.
Native setup uses verified prebuilt Metal servers on Apple Silicon macOS 15+;
users do not need Rust or Xcode.

For source development, run `uv sync --frozen` and `./ai-lab web`.
Native runtime revisions and checksums remain pinned in `sources.json`,
`ai_lab/runtime.json` and `ai_lab/decisions-runtime.json`.

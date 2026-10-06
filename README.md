# AI Lab (`ai_lab`)

AI Lab 0.1.11 provides a local web app, terminal inspection panes, and agent tools for decisions and watermarking. Requires Apple Silicon and macOS 15 or newer. Homebrew installs Python and uv; users do not need Xcode or Rust for normal setup.

```sh
brew tap iamorlando/ai_lab
brew install iamorlando/ai_lab/ai_lab
ai-lab --version                       # AI Lab 0.1.11
ai-lab downloads offer                 # keyboard picker for optional models
ai-lab web                            # opens the app in its own window
```

The package is `ai_lab`; the executable is `ai-lab`. The website opens at `http://127.0.0.1:8080/completion`. Keep its terminal open and press Ctrl+C to stop it. Use `ai-lab web --no-setup` for hosted Jev or saved results without downloading DeepSeek. A compatible installed Chrome, Edge, Brave, or Chromium opens the app in its own window; the page also offers browser installation.

AI Lab provides a model editor, prompt/answer view, native tournament brackets, probability bars, and token inspection. All panes share the same session and selected token.

The first interactive launch offers missing DeepSeek (5.03 GB), Qwen (5.04 GB), CLM (16.47 GB), and Laya (1.69 GB) models and their dependencies. Use **↑/↓** to move, **Space** to select any combination, **A** for all/none, **Enter** to download, or **Esc** to skip. The picker shows the combined missing weight size. Download bars update in place, with speed and ETA on wider terminals; verification and dependency installation share the same display. Existing files are verified and reused, and interrupted model downloads resume. Your choice is remembered for the release. `ai-lab downloads offer` reopens the picker. Use `downloads install ... --yes` to bypass selection in scripts. Models, recordings, profiles, and watermark keys live outside Homebrew in `~/.local/share/ai-lab`; set `AI_LAB_ROOT=/path/to/deepseek` before MCP installation or model launch to share an existing repository workspace.

## Update

```sh
brew update
brew upgrade iamorlando/ai_lab/ai_lab
ai-lab --version                       # AI Lab 0.1.11
ai-lab downloads offer
ai-lab mcp install --codex --force     # refresh an existing client entry
```

Restart your MCP client after refreshing its entry. Stop an older website with Ctrl+C, then launch `ai-lab web` again to load the updated routes and assets. Saved workspace data is preserved.

The optional [install/update wrapper](scripts/install.sh) offers model downloads immediately after Homebrew succeeds:

```sh
sh scripts/install.sh install
sh scripts/install.sh update
sh scripts/install.sh update --no-models
```

Bare Homebrew installs and upgrades offer models on the next interactive CLI launch.

## Agent tools through MCP

```sh
ai-lab mcp install --codex
# Or --claude, --claude-desktop, --cursor, --opencode
```

Restart the client. It launches a Python stdio MCP process through `uvx` on demand; no website or CLI daemon needs to run. The installer stages this release's public code and assets privately, so the entry survives Homebrew upgrades. After each upgrade, rerun installation with `--force` to refresh the snapshot. Other client settings and MCP servers are preserved.

Jev is the default hosted decision model and needs no local process. An available `TYPESAFE_API_KEY` or `JEV_API_KEY` is saved privately during MCP installation or web launch. Client configuration and API responses do not contain the credential.

Start local APIs yourself in another terminal:

```sh
ai-lab models status --json
ai-lab downloads install laya          # asks before downloading
ai-lab models run --laya
ai-lab models run --deepseek           # generation and detection
ai-lab models run --qwen               # Qwen generation and detection
# Or start all installed local APIs:
ai-lab models run
```

MCP exposes 15 tools: model discovery/downloads, seeded/watermarked DeepSeek and Qwen profiles, native generation, saved configuration reads/updates, scheme descriptions with papers, decision answers/ranking, native token inspection, saved results, green/red lists, production tournament results, and watermark detection. Decisions support Jev, Laya, native CLM, and pinned upstream CLM.

Watermark creation accepts an explicit key and every supported scheme setting. Keys and settings persist across sessions. `update_watermarked_model` saves overrides; `get_model_config` retrieves the key only when requested explicitly. `detect_watermark` accepts text plus a saved model or explicit scheme/key/settings and returns native evidence, p-value, confidence, and `match`, `no_match`, or `insufficient`. Confidence is statistical evidence, not a posterior authorship probability. Per-call overrides do not change the saved profile. MCP never starts local model APIs.

Native Contrastive setup installs its verified prebuilt Metal runtime together with
the CLM checkpoint and Qwen3-8B encoder weights. No compiler or manual executable
setup is needed:

```sh
ai-lab downloads install clm --yes
ai-lab models run --contrastive
```

Existing CLM/Qwen downloads automatically install or update the native runtime on the
next `ai-lab models run --contrastive` launch. Version 0.1.10 reserves encoder
workspace, adapts batches under memory pressure, and uses CPU layers when the
GPU budget is too small. Model weights and precision are preserved; CPU
offloading can increase latency. Follow the
[Decisions setup guide](docs/README.md#decisions).

## Local chat and saved models

Open a chat agent for either DeepSeek or Qwen. Each can call AI Lab's own MCP
server, including a separately running local decision provider. Start the
selected model API and Laya in separate terminals, then open the agent:

```sh
ai-lab models run --qwen
ai-lab models run --laya
ai-lab agent --model qwen --self-mcp --herdr-tab
```

Qwen uses automatic tool selection. For a DeepSeek turn that requires a tool,
choose **Tools: Required**, press **Ctrl+T** while idle, or launch with
`ai-lab agent --model deepseek --self-mcp --tool-choice required`. Required
requests a structured call on the first response; responses after tool results
use automatic mode. **Allow/Deny** controls approval. Automatic mode can return
text without calling a tool. See the [MCP chat guide](docs/mcp-client.md).

Use `--name 'Exact saved name'` to choose a saved profile. Its seed, watermark
scheme, private key and settings apply to either family. The legacy `--model`
selection remains supported. The [model profile guide](docs/model-profiles.md)
includes creation, generation, chat, MCP and override examples. Qwen chat uses
its own GGUF download; the Qwen encoder installed with CLM serves decision
inference.

The website's **Watermark decoder** accepts text and a saved model, inherits
its watermark settings, and lets you try a different scheme without saving
overrides. Its confidence is statistical known-key evidence, not an authorship
probability. Tournament views initially select an available match and provide
match controls for navigating the bracket.

## Agent discovery

```sh
ai-lab help --json
ai-lab api schema
ai-lab --skill
ai-lab completion zsh
```

These commands work before model setup. The local service starts automatically when needed.

[Usage, panes, automation, and API guide](docs/README.md) · [Releases and source packages](https://github.com/iamorlando/homebrew-ai_lab/releases)

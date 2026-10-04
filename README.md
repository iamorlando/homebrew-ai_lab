# AI Lab (`ai_lab`)

AI Lab 0.1.7 provides a local web app, terminal inspection panes, and agent tools for decisions and watermarking. Requires Apple Silicon and macOS 15 or newer. Homebrew installs Python and uv; users do not need Xcode or Rust for normal setup.

```sh
brew tap iamorlando/ai_lab
brew install iamorlando/ai_lab/ai_lab
ai-lab --version                       # AI Lab 0.1.7
ai-lab downloads offer                 # asks before downloading optional models
ai-lab web                            # opens the app in its own window
```

The package is `ai_lab`; the executable is `ai-lab`. The website opens at `http://127.0.0.1:8080/completion`. Keep its terminal open and press Ctrl+C to stop it. Use `ai-lab web --no-setup` for hosted Jev or saved results without downloading DeepSeek. A compatible installed Chrome, Edge, Brave, or Chromium opens the app in its own window; the page also offers browser installation.

AI Lab provides a model editor, prompt/answer view, native tournament brackets, probability bars, and token inspection. All panes share the same session and selected token.

The first interactive launch offers missing DeepSeek (5.03 GB), CLM (16.47 GB), and Laya (1.69 GB) models and their dependencies. Accept to download; existing files are verified and reused. Declining is remembered for the release. `ai-lab downloads offer` asks again. Models, recordings, profiles, and watermark keys live outside Homebrew in `~/.local/share/ai-lab`; set `AI_LAB_ROOT=/path/to/deepseek` before MCP installation or model launch to share an existing repository workspace.

## Update

```sh
brew update
brew upgrade iamorlando/ai_lab/ai_lab
ai-lab --version                       # AI Lab 0.1.7
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
# Or start all installed local APIs:
ai-lab models run
```

MCP exposes 14 tools: model discovery/downloads, seeded/watermarked DeepSeek profiles, saved configuration reads/updates, scheme descriptions with papers, decision answers/ranking, native token inspection, saved results, green/red lists, production tournament results, and watermark detection. Decisions support Jev, Laya, native CLM, and pinned upstream CLM.

Watermark creation accepts an explicit key and every supported scheme setting. Keys and settings persist across sessions. `update_watermarked_model` saves overrides; `get_model_config` retrieves the key only when requested explicitly. `detect_watermark` accepts text plus a saved model or explicit scheme/key/settings and returns native evidence, p-value, confidence, and `match`, `no_match`, or `insufficient`. Confidence is statistical evidence, not a posterior authorship probability. Per-call overrides do not change the saved profile. MCP never starts local model APIs.

Native CLM needs a separately configured CLM-capable runtime; the shared CLM download provisions its weights and upstream server. Follow the [Decisions setup guide](docs/README.md#decisions).

## Agent discovery

```sh
ai-lab help --json
ai-lab api schema
ai-lab --skill
ai-lab completion zsh
```

These commands work before model setup. The local service starts automatically when needed.

[Usage, panes, automation, and API guide](docs/README.md) · [Releases and source packages](https://github.com/iamorlando/homebrew-ai_lab/releases)

# AI Lab (`ai_lab`)

Local DeepSeek completions, model configuration, and synchronized terminal inspection panes for tmux and Herdr.

```sh
brew tap iamorlando/ai_lab
brew trust --formula iamorlando/ai_lab/ai_lab
brew install ai_lab
ai-lab
```

The Homebrew package is `ai_lab`. Run it with `ai-lab`.

AI Lab provides a model editor, prompt/answer view, native tournament brackets, probability bars, and token inspection. All panes share the same session and selected token.

First launch guides you through downloading approximately 5 GB of DeepSeek weights and building the pinned inference server. Local inference requires Apple Silicon macOS, full Xcode with Metal, and Rust via rustup. Models and sessions live outside Homebrew, in `~/.local/share/ai-lab`; set `AI_LAB_ROOT` to share an existing website workspace.

## Agent discovery

```sh
ai-lab help --json
ai-lab api schema
ai-lab --skill
ai-lab completion zsh
```

These commands work before model setup. The local service starts automatically when needed.

[Usage, panes, automation, and API guide](docs/README.md) · [Releases and source packages](https://github.com/iamorlando/homebrew-ai_lab/releases)

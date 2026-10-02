# AI Lab (`ai_lab`)

Local DeepSeek completions, model configuration, and synchronized terminal inspection panes for tmux and Herdr.

```sh
brew tap iamorlando/ai_lab
brew trust --formula iamorlando/ai_lab/ai_lab
brew install ai_lab
ai-lab
```

The Homebrew package is `ai_lab`. Run the terminal interface with `ai-lab`, or open the existing website with `ai-lab web`. The website opens at `http://127.0.0.1:8080/completion`; keep the terminal open and press Ctrl+C to stop it. Use `ai-lab web --port 8090 --no-browser` to choose another port without opening a browser.

AI Lab provides a model editor, prompt/answer view, native tournament brackets, probability bars, and token inspection. All panes share the same session and selected token.

First launch downloads a verified prebuilt inference server and approximately 5 GB of DeepSeek weights. Requires Apple Silicon and macOS 15 or newer. Users do not need Xcode, the Metal developer toolchain, or Rust. Models and sessions live outside Homebrew, in `~/.local/share/ai-lab`; set `AI_LAB_ROOT` to share an existing website workspace.

## Agent discovery

```sh
ai-lab help --json
ai-lab api schema
ai-lab --skill
ai-lab completion zsh
```

These commands work before model setup. The local service starts automatically when needed.

[Usage, panes, automation, and API guide](docs/README.md) · [Releases and source packages](https://github.com/iamorlando/homebrew-ai_lab/releases)

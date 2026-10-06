# AI Lab (`ai_lab`)

AI Lab 0.1.12 provides local DeepSeek/Qwen chat, saved models, decision tools,
watermark decoding, and token inspection. Requires Apple Silicon and macOS 15
or newer. Homebrew installs Python and uv; normal setup needs no Xcode or Rust.

```sh
brew tap iamorlando/ai_lab
brew install iamorlando/ai_lab/ai_lab
ai-lab
```

The package is `ai_lab`; the executable is `ai-lab`. Bare `ai-lab` shows the
available commands. Opening a manager or screen does not download model weights
or start inference APIs.

| Command | Purpose |
| --- | --- |
| `ai-lab weights` | Inspect downloaded weights and choose explicit downloads. |
| `ai-lab models` | Create and edit saved generation models and watermark settings. |
| `ai-lab apis` | Inspect supported API connections and required environment variables. |
| `ai-lab chat` | Open conversational chat with a generation-model picker. |
| `ai-lab decisions` | Ask typed questions or rank candidates with a decision provider. |
| `ai-lab completion` | Open token completion, tournament, and probability views. |
| `ai-lab services` | Manage the APIs shared by saved models and decision providers. |
| `ai-lab decoder` | Decode watermark evidence for a selected saved generation model. |
| `ai-lab skills install` | Install the shipped advanced CLI guide for agent clients. |
| `ai-lab mcp install` | Install AI Lab's MCP connection for agent clients. |
| `ai-lab completions` | Generate Bash, Zsh, or Fish completion scripts. |
| `ai-lab web` | Open the existing web application. |

## Saved models and chat

Use the weights manager if the backend is not downloaded. Existing weight files
are verified and reused; missing weights and runtime repairs are reported
separately. Qwen generation needs its own GGUF checkpoint; the Qwen encoder
downloaded for CLM is used for decision inference.

```sh
ai-lab weights install qwen --yes
ai-lab models create --name "My Qwen" --underlying-model qwen
ai-lab services --action start --name "My Qwen"
```

Start keeps its terminal open until Ctrl+C. Open another terminal for chat:

```sh
ai-lab chat --name "My Qwen"
```

Names are exact and case-sensitive; quote names containing spaces. A saved model
retains its selected DeepSeek/Qwen backend, seed, and watermark settings. Create
without a watermark file for an unwatermarked model, or use the model manager to
configure watermarking. `ai-lab chat` without a name opens the model picker.

Services start, stop, restart, and interrupt actions require a selected target.
Saved profiles share one underlying API per family. Interrupt stops the selected
owned service and affects every profile using it; foreign services remain
read-only. See the shipped guide for scripted service actions.

## Decisions, decoder, and completion

```sh
ai-lab decisions
ai-lab decoder
ai-lab completion
```

Decisions selects an available decision provider in its screen; optional
`--model laya` selects Laya. It supports typed questions, scoring, choices, and
ranking candidates. It does not use saved generation-model names. Local decision
APIs must already be running; hosted Jev requires `TYPESAFE_API_KEY` or
`JEV_API_KEY` and no local process. `ai-lab apis` shows supported connections and
which environment variables are needed without revealing their values.

Decoder and completion select saved generation models in their pickers, or
accept `--name "Exact saved name"`. Decoder inherits the model's scheme and lets
you try run-only overrides without changing its saved settings. Confidence is
statistical known-key evidence, not an authorship probability. Completion keeps
the existing raw-prefix, token, tournament, and probability workflows, including
advanced persistent-session and synchronized-view arguments in the guide.

Neither terminal app requires the website. Local inference APIs must already be
running. Native Contrastive uses verified prebuilt Metal servers:

```sh
ai-lab weights install clm --yes
ai-lab services --action start --model contrastive
```

## MCP and agent skills

Attach AI Lab's own MCP server to local chat with one optional argument:

```sh
ai-lab chat --name "My Qwen" --self-mcp
```

Start the decision provider separately when calling its local tools. Tool calls
show Allow/Deny approval. Tools: Auto/Required switches with Ctrl+T while idle;
required mode requests a native call on the user turn and returns to auto after
tool results. Model reasoning and automatic tool adherence can vary.

Chat reports to the current Herdr pane automatically. `--herdr-tab` opens another
tab; guarded prompt orchestration uses chat's `--pane` and `--prompt` arguments.

Install integrations for external agent clients:

```sh
ai-lab mcp install --codex
ai-lab skills install --agent codex --scope user
```

MCP also supports `--claude`, `--claude-desktop`, `--cursor`, and `--opencode`.
The skill installer supports `--agent claude` and project or user scope. The MCP
client starts a stdio process through uvx on demand; no website is needed. The
skill contains the exact shipped CLI guide. Existing client settings and sibling
skills are preserved; replacing different skill content requires `--force`.

MCP exposes 15 tools for model discovery and downloads, saved model settings,
generation, decision answers/ranking, token inspection, saved results,
tournaments, and watermark detection. Keys remain private unless requested
explicitly. MCP does not start local inference APIs.

## Web and data

```sh
ai-lab web
```

The website opens at `http://127.0.0.1:8080/completion`. Keep its terminal open and
press Ctrl+C to stop it. A compatible browser opens the app in its own window.
The website also has a Watermark decoder page at `/decoder`. An ordinary web
launch skips inference setup; explicit download options remain in its help.

Weights, recordings, saved models, and watermark keys live outside Homebrew in
`~/.local/share/ai-lab`. Set `AI_LAB_ROOT=/path/to/deepseek` to use an existing
repository workspace. Upgrading the CLI preserves those files.

## Update and discovery

```sh
brew update
brew upgrade iamorlando/ai_lab/ai_lab
ai-lab --version                       # AI Lab 0.1.12
```

After upgrading, refresh existing MCP entries or agent skills with `--force` and
restart the MCP client. Stop an older website with Ctrl+C, then start it again to
load the updated application. Inspect weights in their manager if needed.

The optional [install/update wrapper](scripts/install.sh) opens the weight picker
after Homebrew succeeds. `--yes` explicitly accepts downloads; `--no-models`
skips that offer. Bare Homebrew installs and upgrades do not offer downloads
when an ordinary CLI screen opens.

```sh
ai-lab --json
ai-lab --skill
ai-lab completion --api-schema
ai-lab completions zsh
```

These discovery and shell commands work before model setup. Detailed advanced
arguments are in the shipped guide and each command's `--help`.

[Usage and API guide](docs/README.md) ·
[Releases and source packages](https://github.com/iamorlando/homebrew-ai_lab/releases)

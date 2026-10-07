# AI Lab web app

## Install and use

```sh
brew install iamorlando/ai_lab/ai_lab
ai-lab setup install deepseek clm --yes
ai-lab web
```

Install both model families before launching the website. Web startup starts both
DeepSeek and CLM APIs; both remain available while the web process is running,
including while idle, using Decoder, or calling CLM from Python.
Existing compatible weights are reused. Keep the website terminal open and use
Ctrl+C to stop it. AI Lab cleans up APIs it started, preserving borrowed services.

`ai-lab web --port 8081` chooses another web port. `--no-browser` runs the site
without opening a browser. `ai-lab --root /path/to/workspace web` selects an
existing workspace; use the same root when installing its weights.

## Screens

**Completion** keeps its existing prefix, next-token probabilities, tournament,
layer and token selection controls.

**Decisions** keeps its Ask/Rank interface. Choose **CLM** for local native
inference or **Jev** for TypeSafe. Jev appears when the server can find a nonempty
`TYPESAFE_API_KEY` or `JEV_API_KEY`; credentials are never embedded in generated
browser request examples. Laya and upstream CLM are no longer offered.

**Watermark decoder** has two columns. On the left, select a saved model, enter a
prompt, and generate text. Copy that output into the right column, or paste other
text. Select its writing model to inherit the saved scheme, key and settings.
The decoding model and settings are independent: deliberately change them to
compare the evidence, then reset to the model's saved configuration. These changes
do not edit the saved model. Saved keys stay on the server unless explicitly
retrieved through a key-aware configuration operation.

Detection is statistical. A displayed value such as 98% evidence can be below a
99% detection threshold. That means the threshold was not reached, not that a key
was missing. Short text may provide insufficient evidence. A detection result is
not a guarantee of authorship or a calibrated probability that a model wrote it.

**Models** creates named DeepSeek profiles, with or without a watermark.
A profile selects an inference family and configuration; it does not require its
own separate inference server.

## Setup and persistent data

`ai-lab setup --help` lists download and repair actions. The download catalog
covers DeepSeek and native CLM. Runtime repair is separate from weight
availability; a changed Python installation or application version does not
invalidate compatible model files.

Default data is in `~/.local/share/ai-lab`. `AI_LAB_ROOT` or `--root` selects another
root. Keep your existing selection across upgrades. Do not delete `.models`,
`harness/models.json`, keys or sessions to upgrade the application.

## MCP for agent clients

```sh
ai-lab mcp install --codex
ai-lab mcp install --claude
```

Use `--force` to replace an existing AI Lab entry after upgrading, then restart the
client. `ai-lab mcp config --codex --json` previews configuration without writing
it; `ai-lab mcp serve` serves JSON-RPC on stdio. `ai-lab --skill` describes the
shipped MCP tools. Their arguments can select named model profiles and override
watermark configuration without changing the saved profile.

## Public command surface

Only `web`, `mcp` and `setup` remain. Interactive terminal commands, terminal
managers, shell-completion commands, Comparison and Watermarking screens are
removed. Older scripts using those commands must use the website or MCP tools.

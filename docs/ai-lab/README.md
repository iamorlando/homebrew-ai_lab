# AI Lab web app

## Install and use

```sh
brew install iamorlando/ai_lab/ai_lab
ai-lab setup install deepseek clm --yes
ai-lab web
```

Install the models you want to use. Qwen3.8-27B is available with
`ai-lab setup install qwen38 --yes`. Opening the website loads no model; the
selected installed API starts on its first operation and remains available while
the web process runs. A model startup failure leaves the website usable.
Existing compatible weights are reused. Keep the website terminal open and use
Ctrl+C to stop it. AI Lab cleans up APIs it started, preserving borrowed services.

`ai-lab web --port 8081` chooses another web port. `--no-browser` runs the site
without opening a browser. `ai-lab --root /path/to/workspace web` selects an
existing workspace; use the same root when installing its weights.

## Screens

**Completion** selects DeepSeek or Qwen3.8-27B and keeps its prefix, next-token
probabilities, tournament, layer and token selection controls. Each backend uses
its own tokenizer and vocabulary; SynthID tournament behavior is unchanged.

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

**Models** creates named DeepSeek or Qwen3.8-27B profiles, with or without a watermark.
A profile selects an inference family and configuration; it does not require its
own separate inference server.

## Setup and persistent data

`ai-lab setup --help` lists download and repair actions. The download catalog
covers DeepSeek, Qwen3.8-27B (`qwen38`), and native CLM (`clm`). Runtime repair is separate from weight
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
watermark configuration without changing the saved profile. Use
`underlying_model="qwen38"` when creating a Qwen profile, or `model="qwen38"`
for an unprofiled generation/detection request. CLM remains a decision model.

## Public command surface

`web`, `mcp`, `setup`, and `services` are public. `services` provides explicit
machine-oriented discovery and foreground lifecycle actions for Herdr; see
[services](services.md). It opens no terminal screen. Interactive terminal
commands and the Comparison and Watermarking screens remain removed.

# Choose a model and keep its watermark settings

AI Lab has two local generation families: DeepSeek R1 (`deepseek`) and Qwen3-8B
(`qwen`). A saved profile stores its underlying model, optional seed and optional
watermark configuration. Changing the selected profile changes the real model
endpoint as well as the seed and watermark settings.

For conversational chat with an existing saved model, use
`ai-lab chat --name "Exact model name"`. The name is case-sensitive; quote spaces.
The agent inherits its saved backend, seed and watermark settings. List exact
names with `ai-lab models list --json`. Built-in families use `--model deepseek`
or `--model qwen`; choose either `--name` or `--model`.

Herdr lifecycle reporting in the current pane is automatic. Tools via
`--self-mcp` and a separate tab via `--herdr-tab` are optional.
`ai-lab completion` is the token/completion workspace. The terminal decoder
opens a profile picker with `ai-lab decoder`, or selects an exact saved profile
with `ai-lab decoder --name "Exact generation profile"`. It inherits saved
watermark settings and allows a scheme override for decoding.
The Decisions terminal app opens an available-provider picker with
`ai-lab decisions`, or selects a provider with `ai-lab decisions --model laya`.
Typed ask/rank requests use `laya`, `contrastive`, `clm-upstream` or `jev` when
available. Decision providers have no saved profile names. The web decoder is
also available through `ai-lab web` → sidebar **Watermark decoder** at `/decoder`.

Inspect available weights and APIs before launching:

```sh
ai-lab services --action list --json
ai-lab weights list --json
```

If weights are missing, install the family you want explicitly. Downloads are
large; this command asks for the selected family's assets and runtime:

```sh
ai-lab weights install qwen --yes --json
ai-lab services --action start --model qwen
```

Use `deepseek` and `--model deepseek` for DeepSeek. Launch commands stay in their own
terminal and own their API process. Do not stop someone else's server to free a
port. The Models page and `ai-lab models` editor offer both underlying models.

After an update, a generation API launched earlier can require a restart so it
loads the current chat template. AI Lab checks the template recorded at launch;
updating its file alone does not reload a running process. Follow the reported
restart guidance: Ctrl+C in that API's original launcher, then run the selected
`ai-lab services --action start --model deepseek` or `--model qwen` again.

Create named plain and seeded profiles:

```sh
ai-lab models create --name 'Qwen plain' --underlying-model qwen --json
ai-lab models create --name 'DeepSeek fixed' --underlying-model deepseek --seed 0x2A --json
ai-lab models list --json
```

For a watermarked profile, select a scheme in the editor, generate a private key,
set the scheme's parameters and save. The CLI accepts the same configuration as
a JSON file. `ai-lab completion --schemes --json` lists supported schemes and exact fields.
For example, create separate private KGW keys without putting them in shell
history, then save a watermarked profile for each family:

```sh
python3 - <<'PY'
import json, os, secrets
for family in ('deepseek', 'qwen'):
    with open(f'{family}-watermark.json', 'x', opener=lambda path, flags: os.open(path, flags, 0o600)) as file:
        json.dump({'scheme': 'kgw', 'key': secrets.token_hex(32), 'delta': 3}, file)
PY
ai-lab models create --name 'DeepSeek marked' --underlying-model deepseek --seed 42 --watermark-file deepseek-watermark.json --json
ai-lab models create --name 'Qwen marked' --underlying-model qwen --seed 43 --watermark-file qwen-watermark.json --json
```

Both families accept the same supported schemes. Keep each key and JSON file
private: they are needed for known-key detection. Creation/config
responses may contain the saved key; avoid sharing those responses. Selecting a
scheme does not guarantee that every sample will produce a strong detection.

Select a saved profile by its exact name, quoting spaces:

```sh
ai-lab completion --name 'Qwen marked' --prompt 'The next word is ' --max-tokens 8 --json
ai-lab completion --name 'Qwen marked'
```

These commands open the existing token-completion workspace. `--model MODEL_ID`
also selects a saved profile. `models create --name` names a new profile;
`--session-name` labels a session. The default `--scheme model` inherits the saved
key and all scheme settings. `--scheme none` disables watermarking for a new
session without editing the profile. An explicit scheme can use temporary
settings via `--watermark-file`; switching schemes can create a fresh session
key. A resumed `--session SESSION_ID` retains its original model, seed and
watermark configuration. Create a new session to change those choices.

For a Python chat host, select the same exact saved name with the shipped
`NativeChat` adapter and connect to AI Lab's own MCP tools:

```python
from ai_lab.native_chat import NativeChat
from ai_lab.mcp_client import ai_lab_client, ToolTurn

chat = NativeChat(data_root, model_name="Qwen marked")
try:
    async with ai_lab_client(data_root) as client:
        turn = ToolTurn(client, [{"role": "user", "content": "Use the local decision tool."}], chat.complete)
        result = await turn.run()  # may require host approval; retain this turn to resume
finally:
    await chat.aclose()
```

Use a DeepSeek profile name to choose DeepSeek. The adapter snapshots the saved
backend, seed, watermark key and settings for every request, including the
continuation after an MCP tool result. Unsaved `scheme="none"`, `key`, `settings`
and `seed` overrides affect this chat only. Own MCP starts an owned stdio process
from the installed application; it does not start generation or decision APIs.
Start a local decision provider separately, for example `ai-lab services --action start --model laya`.
The offline connection requires an explicit local provider in decision-tool
arguments. Tools require host approval unless their exact names are explicitly
preauthorized. [The MCP guide](mcp-client.md) covers approval and external servers.

For the multi-turn local assistant, launch a saved profile in a terminal:

```sh
ai-lab chat --name 'Qwen marked'
ai-lab chat --name 'DeepSeek marked'
```

Both commands inherit the profile's saved seed and watermark. `--model deepseek`
or `--model qwen` selects a plain
family directly. Enter or Send submits a message; successful assistant/tool
history is retained for the next turn. Stop cancels the active turn and closes
its owned MCP connection. Exit closes the app's resources. Tools show Allow/Deny
by default; add `--allow-tool answer_decisions` only if you want to preauthorize
that exact own tool. Start the selected generation API separately. Add
`--self-mcp` for the built-in tools and start a local decision API separately if
you use one. Without `--self-mcp`, the assistant runs without the built-in tools.
Chat defaults are temperature `0.8`, up to `1024` output tokens and a `180`-second
request timeout. Tool mode defaults to `auto`, which lets the model decide and
can produce a text reply. To require a native tool call for a user turn, connect
MCP and select `required` with the visible Tools button or Ctrl+T, or launch with:

```sh
ai-lab chat --name 'DeepSeek marked' --self-mcp --tool-choice required
```

The visible selection is captured when you submit and locked while the turn
runs. Required mode applies to its first model request; continuation after actual
tool results uses auto. Normal Allow/Deny still applies. The selected mode
persists for later submissions until you change it. These controls leave the
saved profile's seed and watermark unchanged.

Per-chat controls leave saved profiles unchanged:

```sh
ai-lab chat --name 'Qwen marked' --scheme none --self-mcp
ai-lab chat --name 'Qwen marked' --scheme kgw --watermark-file qwen-watermark.json --seed 99 --self-mcp
```

In Herdr, current-pane lifecycle reporting needs no extra flag. Optionally add
`--herdr-tab` to open a separate agent tab. To submit to that running
custom AI Lab session, use the app's guarded input command:

```sh
ai-lab chat --name 'Qwen marked' --self-mcp --herdr-tab --json
ai-lab chat --pane PANE --prompt 'Use the local decision tool.' --wait --json
```

Replace `PANE` with the launch result's pane ID. The app validates the live
session and idle state, then uses its private input channel. Herdr 0.9.1's native
`agent prompt` does not support custom AI Lab sessions. Optional external stdio
servers use `--mcp-config FILE`; keep their private configuration outside source
control. No agent command downloads weights or starts a model API.

Do not treat a fixture result or plain text resembling a tool request as a native
MCP tool call.
Watermark confidence is a known-key statistical result, not an
authorship probability; short, low-confidence or retokenized samples can remain
insufficient even when a native trace shows the scheme was applied.

For a reproducible installed-package check without model downloads or a GPU:

```sh
.venv/bin/python packaging/check_cross_model_profiles.py --python /path/to/installed/python
.venv/bin/python packaging/check_cross_model_chat.py --python /path/to/installed/python
.venv/bin/python packaging/check_cross_model_chat.py --python /path/to/installed/python --required-only
```

The supplied interpreter must load an installed AI Lab wheel. The checker owns
ephemeral loopback fixture servers, creates six profiles, switches between
families/plain/seeded/marked settings, reloads in a fresh process and rejects a
generic `default` readiness alias. Its synthetic traces are clearly marked
`fixture: true` and prove configuration/transport only. It never starts a native
model process or connects to another workspace's server. The chat checker adds
real own-MCP stdio discovery/calls, NativeChat and installed agent Enter/Send
interactions with matching tool-result continuation through owned generation
and local decision HTTP fixtures. It checks exact private
settings across both families and fresh-process reload, while reporting no keys.
It also checks temporary overrides for all six schemes and `none`, shipped chat
defaults, and all 15 strict tool schemas against actual MCP discovery on every
request and continuation.
The focused `--required-only` check exercises both saved watermarked families,
Ctrl+T and the visible mode button, public Allow, first-required/auto-continuation
and the next auto turn without changing saved settings.
These fixtures prove inheritance and transport; native inference and detector
statistics need separate real-model evidence.

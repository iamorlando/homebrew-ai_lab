# Connect local chat to MCP

AI Lab provides a Python connector for its own MCP server and optional external
stdio servers. The application installs MCP SDK 1.30.0 automatically. The
existing `ai-lab[mcp]` extra remains compatible.

The chat host can connect to the shipped AI Lab tools without asking a user to
write a configuration file:

```python
from ai_lab.mcp_client import ai_lab_client

async with ai_lab_client(data_root) as client:
    catalog = client.catalog()
    schemas = client.model_tools()
```

This launches the current source or installed application with its own Python
interpreter and the explicitly chosen data root. It starts an MCP process, not
a model API, and downloads no models. Start the local decision provider in its
own terminal before calling it, for example `ai-lab services --action start --model laya` or
`ai-lab services --action start --model contrastive`. The offline default requires an explicit
local provider (`laya`, `contrastive`, `clm-upstream`) in decision-tool arguments;
omitted provider or `jev` is rejected before dispatch. No hosted key is needed.
Decision-tool descriptions reflect this connection's local-only policy and
explicit provider requirement. Names, parameters, approval rules and validation
remain unchanged. `offline=False` retains the original hosted-capable server
descriptions; external server descriptions are preserved.

Every tool requires host approval by default. A host may explicitly preauthorize
named tools with `allow_tools=("answer_decisions", "explain_watermarks")`.
Server annotations describe tools but do not authorize actions.

`catalog()` retains the server's original input schemas (and the offline local
provider requirement). `model_tools()` advertises the same functions with
`function.strict=true` and equivalent reference-free transport parameters.
It expands acyclic local JSON Pointers in Draft 2020-12 schemas before the native
runtime nests them under `arguments`. Required fields, enums, nullable unions,
nested objects and dynamic keys retain their declared meaning; optional fields
remain optional. The original validator still checks calls before approval and
MCP dispatch. Expansion is limited to 64 levels, 16,384 visited values and
256 KiB. Cyclic/unresolved/external references, dynamic/anchor/resource scopes
and other schema dialects fail discovery explicitly rather than weaken it.

Strict arguments do not force the model to call a function. The default choice
is `auto`, which lets the model decide. AI Lab 0.1.11's native runtime constrains
strict Qwen-format tool continuations to JSON after a real tool-call opening;
it does not turn a textual reply into a call. Original schema validation still
runs before approval and dispatch.

```python
tool = next(t for t in client.catalog() if t["tool"] == "answer_decisions")
result = await client.call_tool(tool["name"], {
    "model": "laya",
    "state": "The sky is clear.",
    "questions": {"clear": {"type": "noul", "instructions": "Is the sky clear?"}},
})
```

If approval is needed, this returns `status: requires_approval` and an `approval`
object without calling the server. The UI shows the request and supplies
`approve(request)` (a synchronous or asynchronous boolean callback) when it has
the user's decision. Only `True` executes. Denied calls return a denial result.

Add external servers with `ai_lab_client(data_root, external_config=path)`.
The file is read without being changed, and `ai-lab` is reserved for the built-in
server. This conventional JSON example configures a separately installed
server:

```json
{
  "mcpServers": {
    "local-tools": {
      "command": "python",
      "args": ["/absolute/path/to/tool_server.py"],
      "env": {"SERVICE_TOKEN": "${MY_SERVICE_TOKEN}"},
      "cwd": ".",
      "timeout_seconds": 30,
      "allow_tools": []
    }
  }
}
```

`${NAME}` resolves privately from the host environment. Credentials and server
stderr are not put into model transcripts or public error messages. Configured
credential values are redacted from tool results as well. Discovery redacts schema
annotations and omits private defaults while preserving parameter/type identity.
A private parameter name or constraint that cannot be sanitized safely causes
discovery to fail, rather than advertise a different or invalid schema. The process receives
the SDK's default environment plus explicit entries; unrelated credential
variables are not forwarded. Relative working directories resolve from the
config file's directory. Only stdio is supported; a `url` or another `type`
fails clearly. `disabled: true` skips a server. Keep configuration with literal
credentials private and outside source control.

For a model conversation, use `ToolTurn(client, messages, complete)`.
`complete(messages, tools)` must return the real native assistant message with
OpenAI-style `tool_calls`, including call IDs and JSON-string arguments; text
that resembles a call is treated as text. `await turn.run()` returns a completed
transcript or a pending approval. Keep the same instance and resume with
`await turn.run(approve=callback)` so previously executed calls are not repeated.
The connector appends actual results as matching tool messages and asks the
model for its next response. The host owns native model routing, streaming and
approval display.

Default limits are eight assistant rounds, sixteen calls per turn, 180 seconds
per model response, and 30 seconds per MCP request. Results are limited to
1 MiB. Tool failures remain errors and are not retried. Cancellation marks a
turn terminal because an in-flight action may already have happened. Context
exit or `await client.aclose()` cancels owned calls, including approval waits, and cleans up owned MCP
subprocesses; it never stops a model API or an unrelated workspace process.

Use the shipped native callback with either already-running generation backend:

```python
from ai_lab.native_chat import NativeChat
from ai_lab.mcp_client import ai_lab_client, ToolTurn

chat = NativeChat(data_root, model="qwen")  # or "deepseek", saved key/exact name
try:
    async with ai_lab_client(data_root) as client:
        turn = ToolTurn(client, [{"role": "user", "content": "Use the local decision tool."}], chat.complete)
        result = await turn.run()  # host presents any required approval
finally:
    await chat.aclose()
```

Start the selected generation backend explicitly with `ai-lab services --action start --model qwen`
or `--model deepseek`. `NativeChat.complete(messages, tools)` sends the discovery
schemas and actual call/result messages to its native `/v1/chat/completions` API,
returning the server's assistant message. It does not extract tool calls from
text. `selection` exposes backend, profile ID, seed and key-free effective
watermark; `last_result` adds usage/finish reason. The saved profile is snapshotted
at construction. Use `NativeChat(data_root, model_name="Exact saved name")` for
strict case-sensitive name-only selection, including names that coincide with
a different profile ID. `model` and `model_name` are mutually exclusive; omitting
both selects DeepSeek. The legacy `model` key/name/backend behavior is preserved. Omitted watermark controls inherit it; `scheme="none"` disables
watermarking for this chat, and explicit key/settings/seed override only the
snapshot. `temperature`, `max_tokens` and `timeout` are bounded; default values
are .8, 1024 and 180 seconds. Cleanup cancels its in-flight HTTP requests and closes the adapter; it never
stops a native API. HTTP failures report selected-backend guidance without hosted fallback.

DeepSeek's shipped template uses the pinned distilled tokenizer's supported
`<tool_call>`/`<tool_response>` XML protocol, includes tool schemas and serializes
native mapped arguments. With tools declared, it supplies a closed thinking
prefix. Ordinary conversations without tools render byte-identically to the
previous template, including the original thinking prefix; raw completions are
unchanged. AI Lab upgrades only recognized shipped default manifest/template
pairs in a data root, verifying the known descriptor and derivation and checking
any existing template against the old or bundled checksum. An absent default
can be installed with the matching manifest; an exact bundled template can
finish an upgrade interrupted before the manifest was written. Both recovery
paths require the same complete manifest check and exclude symlinks.
The exact previous fc3c3f5 runtime pin and known template descriptor may advance
to their bundled values only when the entire normalized manifest matches the
bundle. This includes the current F3 XML default and preserves the known 0.1.0
migration. Custom manifests/templates and symlinks stay untouched, along with
profiles and watermark keys. Preparation starts, stops and downloads nothing.
For an API already running during an upgrade, stop it in its owning terminal
and rerun `ai-lab services --action start --model deepseek` or `--model qwen` to load the updated runtime
and template. Readiness rejects an old launch; native chat reports this manual
restart guidance before posting a completion.

The terminal agent exposes automatic and explicitly required tool modes:

```sh
ai-lab services --action start --model deepseek
ai-lab services --action start --model laya
ai-lab chat --model deepseek --self-mcp --tool-choice required
```

Run each model API in its own terminal, then open the agent. The visible
Tools: Auto/Required control and Ctrl+T switch modes while idle. Auto is the
default and can return text without calling a tool. Required asks the native
engine for at least one structured call on the first request of each submitted
user turn. Requests after actual tool results use auto so the model can answer.

When the native Text/Qwen engine must force a plain Required call, its fallback
generates one complete structured call and returns it for approval and a result.
The full tool catalog and each tool's schema remain available. Automatic calls
and spontaneous Required calls can still contain multiple calls; named and
allowed-tool native modes retain their existing behavior.

Normal Allow/Deny approval still applies. Required with no MCP connection or
no discovered tools is rejected; a required response without native calls fails
visibly before dispatch. The selected mode is captured on submission and locked
while busy. Herdr prompts use the target window's visible mode.

In the captured automatic DeepSeek test, the model returned prose and bare JSON
without a tool-call opening; it caused zero MCP dispatches. This observation
does not establish that every automatic request fails. Explicit required mode
is a separate user choice; the app never silently retries automatic output in
that mode or parses prose into calls. Native failures and repeated requests
remain subject to the connector's call/round limits, original schema validation
and approval. Calls are never deduplicated or retried to conceal a failure.

The MCP server also provides `generate_text(prompt, model="deepseek", ...)`.
Select `qwen` or a saved profile key/exact name to use its backend and persisted
seed/watermark. Optional `scheme`, `key`, `settings` and `seed` affect only that
call; `scheme="none"` disables watermarking. `capture_trace=True` requests actual
native evidence. Plain backend selection generates unwatermarked text by default.
Generation does not start/download models. `detect_watermark` and
`inspect_next_token` route to the saved profile's backend/tokenizer too.
`create_seeded_model`/`create_watermarked_model` accept `underlying_model="qwen"`;
`update_watermarked_model` can change that backend while preserving saved identity.

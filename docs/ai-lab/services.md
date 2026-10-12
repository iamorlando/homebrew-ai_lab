# Inference APIs and Herdr

Install the family you want with `ai-lab setup install FAMILY --yes`, using
`deepseek`, `qwen38`, or `clm`, then run `ai-lab web`. Opening the website loads
no model. The selected installed API starts when you use it and remains running
until its owner exits. A startup failure reports the selected model and recovery
action while leaving the website available. No model is silently substituted.

Default endpoints are `http://127.0.0.1:11435` for DeepSeek,
`http://127.0.0.1:11440` for Qwen3.8-27B, and `http://127.0.0.1:11436` for CLM.
See [direct API access](api-connections.md). Borrowed compatible APIs remain owned
by their original launcher. Closing a browser tab does not stop the APIs;
Ctrl+C stops the web process and only APIs it owns.

MCP starts only the selected installed API and retains it until that MCP process
exits. Discovery and profile configuration load no model. Missing weights or
runtimes produce setup guidance, with no automatic weight download.

## Explicit service control

Herdr uses the machine-readable service contract. These commands have no
interactive terminal screen:

```sh
ai-lab services --action list --json
ai-lab services --action list --model qwen38 --json
ai-lab services --action start --model qwen38 --json
```

List is read-only discovery: it reports backend identity, readiness, ownership,
endpoint, primary `log_path`, available actions, and saved profiles mapped to the
same backend. Start remains in the foreground; keep its pane open. Ctrl+C stops
only APIs started by that invocation. `--name 'Exact saved profile name'` can
select a backend through a saved profile. Explicit `stop`, `restart`, and
`interrupt` verify ownership before sending signals. All profiles sharing that
backend share the same process, so stopping it affects every such profile.

Qwen3.8-27B’s primary log is `.state/qwen38-server.log`. Its process, endpoint,
weights and profiles remain distinct from DeepSeek and the legacy Qwen3-8B
identity. Herdr consumers should use discovered service rows and their log paths.

## Memory failures

A model that cannot fit in available memory reports the reason and log location;
it does not cause an implicit model switch or weight redownload. Close unrelated
memory-intensive work before retrying. A larger model can require a larger machine.

For CLM specifically, opt in to quantizing its encoder while loading:

```sh
AI_LAB_CLM_ISQ=q4k ai-lab web
# Or an explicit CLM owner in a Herdr pane:
AI_LAB_CLM_ISQ=q4k ai-lab services --action start --model contrastive --json
```

Use the same environment setting for an MCP or Herdr launcher and restart the
owning CLM process to apply it. Original CLM weight files remain unchanged.
This option configures CLM only; it does not select or configure Qwen3.8-27B.

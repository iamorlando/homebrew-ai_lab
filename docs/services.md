# Persistent inference APIs

Run `ai-lab setup install deepseek clm --yes` once, then `ai-lab web`.
Web startup starts both the DeepSeek API and the native CLM API before announcing
readiness. Both stay running for the web process lifetime, including while idle,
when changing pages or profiles, and while other programs call CLM directly.
No model is unloaded when switching between Completion, Decoder and Decisions.

Default endpoints are `http://127.0.0.1:11435` for DeepSeek and
`http://127.0.0.1:11436` for CLM. See [Python access](api-connections.md).
Existing compatible APIs are reused; borrowed processes remain owned by their
original launcher. Closing a browser tab does not stop the APIs. Ctrl+C exits the
web process and cleans up only APIs it started. There is no services command.

Standalone Qwen is not offered. CLM's required Qwen encoder files remain part of
CLM setup. Existing profiles, keys and weights are preserved on upgrade.

MCP execution tools start a supported local API when needed and retain it until
that MCP process exits. Discovery and configuration do not start models. Missing
weights or runtimes produce explicit setup guidance, with no automatic download.

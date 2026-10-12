# MCP clients

Use `ai-lab mcp install --codex` or `ai-lab mcp install --claude` to configure a
client. `ai-lab mcp config --codex --json` previews the configuration. Add `--force`
to refresh an existing entry after upgrading and restart the client.

`ai-lab mcp serve` provides JSON-RPC on stdio. Discovery does not start inference
or download models. Execution tools automatically start a required installed
backend and clean up APIs they own when the server exits. Missing weights require
`ai-lab setup install FAMILY --yes`.

Tools support saved DeepSeek profiles, real generation, watermark inspection
and detection, and CLM/Jev typed decisions. Saved keys are hidden in ordinary
responses; an explicit key-aware configuration request may retrieve them.
Model reasoning and reliable tool selection are capabilities of the model, not
guarantees of the MCP connection. See `ai-lab --skill` for tool arguments.

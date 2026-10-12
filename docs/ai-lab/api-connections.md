# Connections

DeepSeek, Qwen3.8-27B, and native CLM run locally through the pinned Mistral runtime.
`ai-lab web` starts the selected installed API on use and retains it until the
web process exits; no cloud key is required. Readiness is model-specific.
Jev uses the hosted TypeSafe API and requires `TYPESAFE_API_KEY` or `JEV_API_KEY`.
Start `ai-lab web` from the environment with that key; it remains server-side.

Use `ai-lab mcp config --codex --json` to inspect the MCP client connection.
The old informational terminal API manager is no longer a public command.

## CLM from Python

Start CLM by using it in Decisions, or run
`ai-lab services --action start --model contrastive --json` and keep that owner
running. Call CLM directly on port 11436; selecting another model in the browser
does not stop this endpoint. This example uses Python's
standard library and discovers the exact loaded model name:

```python
import json
from urllib.request import ProxyHandler, Request, build_opener

base = "http://127.0.0.1:11436"
http = build_opener(ProxyHandler({}))
with http.open(base + "/v1/models", timeout=10) as response:
    model = json.load(response)["models"][0]["name"]
payload = {
    "model": model,
    "state": "The package arrived on time and in good condition.",
    "questions": {
        "positive": {"type": "noul", "instructions": "Is the customer feedback positive?"}
    },
}
request = Request(base + "/v1/systemone", data=json.dumps(payload).encode(),
                  headers={"Content-Type": "application/json"}, method="POST")
with http.open(request, timeout=180) as response:
    print(json.load(response))
```

If you configured `AI_LAB_DECISIONS_URL`, use that base URL instead. For a server
configured with `AI_LAB_DECISIONS_API_KEY`, send its bearer token in the
`Authorization` header on discovery and requests.

## Generation APIs

DeepSeek serves OpenAI-compatible generation on port 11435; Qwen3.8-27B uses
port 11440. Start the selected backend through web/MCP or explicitly with
`ai-lab services --action start --model qwen38 --json`. Query that endpoint’s
`/v1/models` for its native model identifier; each single-model API may expose
`default`, so the endpoint determines the backend. AI Lab’s MCP `generate_text`
accepts `model="qwen38"`, `model="deepseek"`, or a saved profile ID/exact name.

NativeChat and ToolTurn callbacks borrow an already running API. For direct SDK chat,
start the chosen backend explicitly and keep its launcher open:
`ai-lab --root YOUR_ROOT services --action start --model qwen38 --json`
(use `deepseek` for DeepSeek). Merely opening the website loads no model.

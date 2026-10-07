# Connections

DeepSeek and native CLM run locally through the pinned Mistral runtime.
`ai-lab web` starts both APIs and retains them until the web process exits; no cloud key is required.
Jev uses the hosted TypeSafe API and requires `TYPESAFE_API_KEY` or `JEV_API_KEY`.
Start `ai-lab web` from the environment with that key; it remains server-side.

Use `ai-lab mcp config --codex --json` to inspect the MCP client connection.
The old informational terminal API manager is no longer a public command.

## CLM from Python

Keep `ai-lab web` running. Call CLM directly on port 11436; using DeepSeek or
Decoder in the browser does not stop this endpoint. This example uses Python's
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

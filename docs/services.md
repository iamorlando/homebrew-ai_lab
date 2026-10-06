# Inference services

Run `ai-lab services` in a terminal to see the five servers and providers:
DeepSeek, Qwen, native CLM, Laya and hosted Jev. Select a server row with the arrow keys. Opening the manager discovers
status; starting a service is an explicit action.

Saved profile names and watermark summaries appear as information on their
shared server row and in its details. Keys, seeds and private settings stay hidden.
Several profiles share the same DeepSeek or Qwen server. Start launches that
server once, regardless of how many profiles use it. Existing chat and completion
requests apply the selected profile's own generation settings.

Use `--name "Exact saved name"` to select that profile's shared server row or
`--model qwen` to select a server directly. Names are case-sensitive; a missing name never selects
a different profile. Decision providers use `--model contrastive`,
`--model laya` or `--model jev`.

Native CLM uses `--model contrastive` and the existing local Mistral runtime at
`.runtime/decisions/mistralrs`. It is managed like DeepSeek and Qwen. Laya also
runs locally and has the same service actions. Jev passes requests through to
its hosted API. The separate legacy `clm-upstream` adapter retains its internal
implementation and is omitted from Services.

The manager offers:

- **Start**: launch a stopped service with ready prerequisites. DeepSeek, Qwen
  and native CLM verify existing weights and repair only the published runtime when needed.
  Missing weights and custom runtime/source overrides require explicit setup.
- **Stop**: stop the selected service after verifying workspace ownership.
- **Restart**: stop the selected owned service, then launch it again.
- **Interrupt (stops)**: send the equivalent of Ctrl+C to the selected owned
  service. This stops the whole API and affects every profile using it. There is
  no per-request cancellation that keeps the API running.
- **Refresh / retry**: discover current status again. `R` also refreshes.
- **Cancel wait**: cancel discovery or startup waiting. `Esc` also cancels. If a
  process handle is arriving late, cancellation waits for that handle and stops
  only the newly launched process. An in-progress runtime verification or repair
  settles before cancellation completes; cancellation then prevents model launch.
  Final process-identity capture also settles before cancellation or Exit can
  complete. Only the event loop registers ownership; delayed workers cannot add
  receipts after Exit or affect a later action. Further actions wait for cleanup
  to settle. If a new child's identity cannot be verified, cleanup stays pending
  and Exit reports the issue instead of silently completing.
- **Exit**: stop APIs launched by this manager and leave existing borrowed APIs
  running. `Q` or Ctrl+C also exits.

Actions with missing prerequisites or unverified ownership are disabled. Missing
weights and runtime setup are displayed separately; open `ai-lab weights` to
inspect prerequisites. A hosted Jev connection has no local lifecycle. An API
whose process ownership cannot be verified must be stopped through its original
launcher. DeepSeek, Qwen, native CLM and Laya have durable identity records;
the manager checks them again before sending a signal. If identity changes or shutdown takes
too long, it reports the issue and sends no forced kill.

A healthy API can be running and usable for inference even when it was launched
from another root. Native CLM also checks supported prior model roots for a
verified process receipt. Its details and JSON `origin_root` show the proven
launch root; Stop, Restart and Interrupt control that shared server. Restart uses
the origin's weights and runtime. Stop followed by Start in the same manager
keeps that verified origin. A new manager after shutdown uses its selected root;
use `--root ORIGINAL_ROOT` when you want to start there again. Saved profiles
sharing a backend still use one API.

Native CLM launched by older AI Lab versions can be recovered automatically
without restarting it or writing a receipt during discovery. Recovery requires
the exact loopback listening PID, user, process group and start identity, the
shipped native launch arguments and model path in a supported root, and verified
published runtime bytes mapped by that process. Opening or exiting Services
leaves this existing server running. Health alone never grants lifecycle control.
If these checks cannot prove ownership, the row remains external with actions
disabled. See [updating and preserving your existing setup](upgrading.md) for the
update steps and original-launcher fallback; keep your weights and settings.

`AI_LAB_DECISIONS_URL` selects the native CLM loopback HTTP origin, including a
custom port; it does not make native CLM unmanaged. `127.0.0.1`, `localhost`
(bound as IPv4 loopback), and `[::1]` are supported. Start launches Mistral at that
origin when it is free. An occupied endpoint without a verified receipt or
verified legacy native identity stays external. A changed endpoint or binary leaves an existing owned launch
stale; Stop remains available, and Restart uses the current settings when its
prerequisites are ready. Native ownership is recorded in
`.state/decisions-mistral.json`; its log is `.state/decisions-mistral.log`.
JSON discovery includes an absolute `log_path` for every local service, using
native CLM's proven origin when it differs from the selected root, without
creating or reading the log. Hosted providers have no local log path.

Laya records its verified local process in `.state/laya-server.json` and logs to
`.state/laya.log`. A later manager in the same root can Stop, Restart or Interrupt
that workspace-owned server while its original launcher remains open. When Laya
weights are verified but its Node/ONNX installation is missing, Start uses the
same local setup routine as the weights installer. Missing weights show the
exact `ai-lab weights install laya --yes` command. Managed Laya accepts IPv4
loopback origins (`127.0.0.1` or `localhost`) and configurable ports; its existing
Node server binds IPv4 loopback.

Script actions stay under the same public surface:

```sh
ai-lab services --action list --json
ai-lab services --action list --name "Exact saved name" --json
ai-lab services --action start --name "Exact saved name"
ai-lab services --action stop --model qwen
ai-lab services --action restart --model deepseek
ai-lab services --action interrupt --model deepseek
ai-lab services --action start --model contrastive
ai-lab services --action restart --model contrastive
```

Start and restart stay in the foreground. Keep that terminal open; Ctrl+C stops
only APIs launched by that invocation. Mutation scripts require one explicit
`--name` or `--model`. The interactive manager requires terminal stdin and stdout;
JSON discovery works in scripts without a terminal. The selected data root is
always shown. Existing Herdr lifecycle reporting is automatic.

## Fixture verification and integration

`tests/ai_lab/test_service_manager.py` mounts the actual Textual screen and uses
fake API inventories, launch handles and signals. `packaging/check_services.py`
is a standalone scratch checker for an installed package. Neither proof starts a
model, uses a GPU, downloads weights, compiles a runtime or calls an SDK.
`tests/ai_lab/test_clm_ownership.py` verifies legacy and supported-root discovery,
origin lifecycle control, and rejection of foreign or replaced process identities
using scratch files and fake OS observations.

The support module exports `add_parser(subparsers)` and `run(args, root)`; the
CLI lane owns central registration and dispatch. Runtime-only repair uses the
accepted storage implementation in integrated base
`6801487d8321227f6e8368190fee43f69282c344` directly. Fixture proof exercises its
real file verification, archive checks and installation with tiny scratch files
and an in-memory artifact; no real artifact or weights are downloaded.

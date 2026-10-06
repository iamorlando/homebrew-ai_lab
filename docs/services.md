# Inference services

Run `ai-lab services` in a terminal to see saved generation models and available
decision APIs. Select a row with the arrow keys. Opening the manager discovers
status; starting a service is an explicit action.

Saved profiles show their exact name, underlying API, and whether a watermark
scheme is enabled. Keys, seeds and private settings stay hidden. Several profiles
can share the same DeepSeek or Qwen API. Starting a profile starts that shared API
once. Existing chat and completion requests apply the selected profile's own
generation settings; selecting a row here does not change those settings.

Use `--name "Exact saved name"` to select a generation profile or `--model qwen`
to select an API directly. Names are case-sensitive; a missing name never selects
a different profile. Decision providers use `--model contrastive`,
`--model clm-upstream`, `--model laya` or `--model jev`.

The manager offers:

- **Start**: launch a stopped service with ready prerequisites. DeepSeek and Qwen
  verify existing weights and repair only the published runtime when needed.
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
inspect prerequisites. A hosted Jev connection has no local lifecycle. A decision
API started by another launcher, including a custom endpoint, must be stopped
through that launcher because this manager cannot verify its process identity.
DeepSeek and Qwen workspace services have durable identity records; the manager
checks them again before sending a signal. If identity changes or shutdown takes
too long, it reports the issue and sends no forced kill.

Script actions stay under the same public surface:

```sh
ai-lab services --action list --json
ai-lab services --action list --name "Exact saved name" --json
ai-lab services --action start --name "Exact saved name"
ai-lab services --action stop --model qwen
ai-lab services --action restart --model deepseek
ai-lab services --action interrupt --model deepseek
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

The support module exports `add_parser(subparsers)` and `run(args, root)`; the
CLI lane owns central registration and dispatch. Runtime-only repair uses the
accepted storage implementation in integrated base
`6801487d8321227f6e8368190fee43f69282c344` directly. Fixture proof exercises its
real file verification, archive checks and installation with tiny scratch files
and an in-memory artifact; no real artifact or weights are downloaded.

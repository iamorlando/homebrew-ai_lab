# AI Lab

AI Lab puts the website's model profiles and raw-prefix Completion experiment in
terminal panes. It uses the same pinned `iamorlando/mistral.rs` server, watermark
validation, native logits, and verified production tournament traces. Pair
conversations, detection, and Harbor experiments stay in the website.

## Run from this repository

```sh
uv sync --frozen
./ai-lab                        # first-run setup, then model configuration
./ai-lab models                 # interactive model configuration
./ai-lab chat --model seed-1 --scheme synthid
```

The workspace has a prompt/answer editor, probability bars, a scrollable native
bracket, and selectable tokens. `Ctrl+Enter` runs, `Ctrl+A` appends the selected
token and inspects again, `Ctrl+S` stops after the current token, `F1` opens help,
and `Ctrl+Q` closes the pane. Use Tab, arrows, Enter, Page Up/Down and the mouse to
navigate. Small windows switch to one panel at a time with view buttons; short
panes use the keyboard commands to preserve room for results. Closing a pane does not stop its session or the background service.

A plain `ai-lab` starts setup on first interactive launch. Setup explains the
5.03 GB weight download, checks prerequisites, builds the pinned Metal runtime,
and verifies model, tokenizer, template, and binary hashes. It needs Apple Silicon
macOS, full Xcode with Metal, and Rust via rustup. Completion-only setup does not
need Docker or OpenCode. A package installation does not silently download weights.

## Homebrew

AI Lab has its own [Homebrew tap](https://github.com/iamorlando/homebrew-ai_lab).
The Homebrew package is named `ai_lab`; the executable is `ai-lab`.

```sh
brew tap iamorlando/ai_lab
brew install ai_lab
ai-lab
```

For a direct package install, download the wheel from the
[release](https://github.com/iamorlando/homebrew-ai_lab/releases/latest), then run:

```sh
uv tool install --python 3.13 ./ai_lab-0.1.0-py3-none-any.whl
ai-lab setup --yes
```

Installed copies store data in `~/.local/share/ai-lab` (or `AI_LAB_HOME`). Source
runs default to this checkout. To share website models and the existing DeepSeek
installation, pass `--root /path/to/deepseek` before the subcommand or export
`AI_LAB_ROOT`. Runtime paths remain outside Homebrew's Cellar and survive upgrades.

## Models

The interactive editor uses the website's field metadata: name, DeepSeekR1,
optional decimal/hexadecimal seed, scheme, generated or supplied key, and each
scheme's settings. Names are unique; seedless profiles remain seedless. Selecting
a saved profile displays its settings; **Open** launches its completion workspace; change the name to make a copy. Deleting a
profile preserves recorded sessions, but that profile cannot start new runs.

```sh
ai-lab models list --json
ai-lab models create --name seeded --seed 0x600D_C0FFEE --json
ai-lab models create --name marked --watermark-file watermark.json --json
ai-lab schemes --json
```

A session requires an existing model ID or an exact, unique model name.
`--scheme model` (the default) inherits its saved watermark. `--scheme none`
disables watermarking. A named scheme reuses matching profile settings or creates
fresh temporary settings and a key. Fresh SynthID sessions default to actual
tournament sampling at depth 4. Existing profiles retain their policy and depth.
`--watermark-file` overrides settings for the explicitly named scheme. Session
configuration remains fixed; make a new session to change it.

## Separate tmux or Herdr panes

```sh
ai-lab session create --model seeded --scheme synthid --name experiment --json
# Use the returned id for every pane:
ai-lab view chat --session SESSION_ID
ai-lab view tournament --session SESSION_ID
ai-lab view probabilities --session SESSION_ID
ai-lab view tokens --session SESSION_ID
```

Or create the layout automatically:

```sh
ai-lab layout tmux --model seeded --scheme synthid --launch --json
# The result includes the tmux attach command.
ai-lab layout herdr --model seeded --scheme synthid --launch --json
```

Herdr must already have a running session. Both layout commands print their plan
without opening panes when `--launch` is omitted. The commands use quoted argument
lists, so model/session values are not interpreted as shell fragments. Existing
panes and workspaces are not replaced. All AI Lab panes follow the same selected
step and token. Selecting an alternative never changes the recorded winner.

The bracket follows recorded source IDs. Duplicate draws remain distinct, missing
matches are labeled, and collapsed subtrees show the real advancing draw. Capture
is bounded at 255 matches; it never changes generation depth. Actual tournaments
have no computed marginal after-watermark distribution, so those values display
as unavailable. Full-vocabulary model probabilities are never normalized over only
the captured alternatives. The probability round selector exposes captured SynthID
updates, and the token table labels green/red or favored/unfavored membership. Token text is escaped so leading spaces stay visible.

## Automation and API discovery

Inspired by Herdr's [CLI](https://herdr.dev/docs/cli-reference/) and
[socket API](https://herdr.dev/docs/socket-api/), AI Lab exposes structured commands,
a versioned local API, persistent sessions, shell completion and an agent guide:

```sh
ai-lab help --json
ai-lab api schema
ai-lab --skill
ai-lab completion zsh > ~/.zfunc/_ai-lab
```

`api schema`, `--skill`, help, and completion generation work before setup and do
not launch a server. Dynamic shell completion suggests model keys and session IDs
from a running service without starting one.

```sh
ai-lab complete --model seeded --scheme synthid \
  --prompt 'the quick brown fox jumps over the lazy' --json
ai-lab complete --session SESSION_ID --prompt-file prefix.txt --no-wait --json
ai-lab session wait SESSION_ID --timeout 1200 --json
ai-lab session get SESSION_ID --json
ai-lab session select SESSION_ID --step 0 --token-id 5562 --revision REV --json
ai-lab session append SESSION_ID --revision REV --json
ai-lab session stop SESSION_ID --json
```

`--prompt-file -` reads stdin without trimming whitespace. The default is one
next-token decision, matching the website. `--max-tokens 1..256` repeats inspection
on the growing raw prefix and updates attached panes after each decision. Each
prefix is retokenized and a fixed model seed resets for each decision; this is not
a continuous native sampling request. Position-based watermark schemes advance
with each appended token. A new prompt resets the position.

Session mutations can use a revision to reject stale pane actions. Selection and
append require a revision; complete optionally takes `--revision`. JSON success
goes to stdout; JSON errors go to stderr with exit 1 (invalid command syntax uses
exit 2). A wait timeout leaves generation running. Stop finishes the in-flight
native decision before releasing the shared inference lock.

`ai-lab api call METHOD /api/lab/... --body-file request.json` invokes the same
endpoints as the TUI. `api snapshot` lists models and sessions. Session responses
omit watermark keys; model configuration responses include them for editing.
Session files have mode 0600 inside a mode-0700 directory.

## Service lifecycle

When the website is running at port 8080 for the same root, AI Lab attaches to its
`/api/lab` endpoints and shares its model-publication and generation locks. Restart
an older website process once to load the new routes. For other ports, set
`AI_LAB_SERVER=http://127.0.0.1:PORT` and use the matching root.

Otherwise AI Lab automatically starts a private Unix-socket service. Inference
starts only when a completion needs it. Commands verify the service's application,
API version and root before attaching. Startup and daemon locks prevent duplicate
services, and each workspace has its own socket. A long root path uses a private,
user-owned socket directory in `/tmp`. State remains under `ROOT/.state/ai-lab`.

```sh
ai-lab doctor --json
ai-lab server status --json
ai-lab server stop
```

Only an idle, private AI Lab service can be stopped this way. It leaves the
inference runtime available for other local clients. The website uses its own
launcher. If it starts after the private service, it forwards AI Lab requests to
that existing session owner. A shared file lock serializes configuration and
completion work across both processes; CLI model writes publish through the live
website so its aliases remain current. For a custom website port, set
`AI_LAB_SERVER` before starting the private service as well as in CLI shells.
Read-only requests reconnect after a service transition. Mutations are never
automatically replayed. Incomplete runs are marked interrupted on recovery. Logs are in `.state/ai-lab/server.log` and
`.state/mistral-server.log`.

## Build, test and release

```sh
uv sync --frozen
uv run python -m unittest discover -s tests/ai_lab -v
uv run python -m unittest discover -s harness/tests -p 'test_*.py'
uv build
python3 packaging/homebrew/generate.py dist/ai_lab-0.1.0.tar.gz --version 0.1.0
```

The generator writes `dist/homebrew/ai_lab.rb` with the actual archive checksum and
the dedicated AI Lab tap release asset URL. The archive excludes saved model profiles
and state; the wheel bundles only shared backend code and pinned public assets.
Publish the exact archive at that URL, then copy the generated formula into the
AI Lab tap's `Formula/ai_lab.rb`. No repository push or release is automatic.
For a local Homebrew build, pass `--url file:///absolute/path/to/archive.tar.gz` to
the generator and use the resulting formula in a local tap. Rebuild and regenerate
if any release content changes.

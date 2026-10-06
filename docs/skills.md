# Install the AI Lab agent skill

Choose the agent and scope explicitly:

```sh
ai-lab skills install --agent codex --scope project --json
ai-lab skills install --agent claude --scope user --json
```

| Agent | Project scope (default: current directory) | User scope |
| --- | --- | --- |
| Codex | `.agents/skills/ai-lab/SKILL.md` | `~/.agents/skills/ai-lab/SKILL.md` |
| Claude Code | `.claude/skills/ai-lab/SKILL.md` | `~/.claude/skills/ai-lab/SKILL.md` |

Use `--project DIR` to choose the project directory. Use `--path DIR` for an exact
custom skill directory; the file is `DIR/SKILL.md`. The agent must load that
custom location. Both agent and scope are still required. `--project` applies
only to project scope. JSON and text output include the exact installed path.

The installer adds valid `name` and `description` YAML metadata to the shipped
`ai_lab.cli.SKILL` guide, which `ai-lab --skill` also prints. It reads that guide
lazily rather than maintaining a duplicate command template. JSON output names
the guide source and includes its SHA256 plus the installed document SHA256.
After an application update, rerun installation with `--force` to adopt a
changed guide. Identical content returns `unchanged`, preserving the file and
its permissions. Differing content is preserved unless `--force` is explicit.

New directories use mode 0700 and a published skill uses 0600. The installer
atomically publishes a complete file, leaves existing sibling references and
unrelated skills alone, and rejects symlinked path components, symlinked files,
nonregular destination files and parent traversal. These checks also apply to
`--force`. Installation requires a POSIX filesystem and no-follow directory
operations. It does not modify client configuration, install MCP, launch models,
download dependencies or message another agent.

The final central guide uses the thirteen canonical public surfaces. Conversation
uses `ai-lab chat --name "Exact saved name"`; optional `--self-mcp` enables AI
Lab's own offline tools without a config file. Allow/Deny remains required
unless an exact own tool is preauthorized through `--allow-tool`. Requiring a
tool call with `--tool-choice required` does not bypass approval. Start the
selected model API explicitly through `services` before chatting. Herdr's
current-pane reporting is automatic; `--herdr-tab` optionally opens a new tab.

Advanced examples from the CLI builder's canonical contract:

```sh
ai-lab completion --session-action create --name "Exact saved name" --scheme synthid --json
ai-lab completion --session SESSION --prompt "the quick brown" --no-wait --json
ai-lab completion --session-action wait --session SESSION --json
ai-lab completion --session-action get --session SESSION --json
ai-lab completion --view tournament --session SESSION
ai-lab completion --layout herdr --session SESSION --launch
ai-lab completion --session-action select --session SESSION --step 0 --token-id ID --revision REV --json
ai-lab completion --session-action append --session SESSION --revision REV --json
ai-lab chat --pane PANE --prompt "Continue the review" --wait --json
```

Session indices are zero based. Preserve raw prompt whitespace, native traces
and tournament evidence; do not invent missing probabilities. Existing session
model/scheme settings remain immutable. `mcp install` continues to manage the
established MCP integration separately.

Verification uses scratch home/project/custom destinations and synthetic
credentials only. The API/skills builder's starting commit contains the older
central guide. Its preliminary installed-package check proves wrapping and
installation provenance, not final canonical examples. Run
`packaging/check_api_skills.py --python INSTALLED_PYTHON --canonical` against the
accepted integrated CLI SHA to gate the canonical guide and public CLI wiring.

Paths and metadata follow the current [official OpenAI skills documentation](https://developers.openai.com/codex/skills)
and [Claude Code skills documentation](https://code.claude.com/docs/en/skills).

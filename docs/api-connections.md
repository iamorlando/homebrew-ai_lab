# API connections

`ai-lab apis` opens a settings inventory with Refresh and Exit. Use
`ai-lab apis --json` for the same information in scripts. Opening or refreshing
reads connection metadata and credential availability. It does not check health,
send provider requests, write configuration, start a process or download weights.
`configured` means the settings are usable; reachability remains `not_checked`.

| Connection | Default endpoint | URL setting | Authentication setting |
| --- | --- | --- | --- |
| DeepSeek R1 | `http://127.0.0.1:11435` | Fixed | None |
| Qwen3-8B | `http://127.0.0.1:11439` | Fixed | None |
| Native Contrastive CLM | `http://127.0.0.1:11436` | `AI_LAB_DECISIONS_URL` | `AI_LAB_DECISIONS_API_KEY` |
| Upstream Contrastive CLM | `http://127.0.0.1:8700` | `AI_LAB_CLM_UPSTREAM_URL` | `AI_LAB_CLM_UPSTREAM_API_KEY` |
| Laya | `http://127.0.0.1:8710` | `AI_LAB_LAYA_URL` | `AI_LAB_LAYA_API_KEY` |
| Hosted Jev / TypeSafe | `https://api.typesafe.ai/v1/systemone` | Fixed | `TYPESAFE_API_KEY` or `JEV_API_KEY` |

Local decision URL overrides must be loopback HTTP origins. Authentication is
optional for local connections; a separately configured server may require its
own bearer key. Native CLM also accepts `AI_LAB_DECISIONS_MODEL` to select a
decision model. URL and model overrides are optional. Jev requires either key
name, or the existing privately synced workspace credential. An environment
variable is `configured` only when nonblank. The Jev connection can therefore be
configured while both environment variables are unset, through its saved key.

The inventory reports variable names and booleans. Keys and model-selection
values are never exported. An invalid URL override is withheld entirely; auth,
path, query and fragment content cannot leak through endpoint output or errors.
Valid local endpoints contain only a loopback origin. Generation URLs come from
`generation_models.GENERATION_BACKENDS`; local decision defaults and URL
validation come from `decisions.DecisionRuntime`, and hosted key precedence
comes from `ai_lab.credentials.jev_key`. There is no OpenAI/Anthropic hosted chat
connection in this inventory because the application does not implement one.

Connections are shared backend/provider routes. Saved named generation profiles
belong to `ai-lab models`, with their own seed and watermark settings. Process
lifecycle belongs to `ai-lab services`. A configured connection does not mean its
model weights are installed or its API is running.

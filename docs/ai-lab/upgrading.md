# Upgrading AI Lab

1. Stop the old AI Lab website or an old foreground model launcher with Ctrl+C.
2. Upgrade the application:

   ```sh
   brew update
   brew upgrade iamorlando/ai_lab/ai_lab
   ai-lab --version
   ```

3. Open the app with `ai-lab web`. Select the model you want to use; its installed API starts on demand.

No data cleanup is required. Keep existing weights, model profiles, watermark
keys and sessions. Keep the same `AI_LAB_ROOT` or `--root` setting if you use one.
The default remains `~/.local/share/ai-lab`, outside the Homebrew Cellar.

If a required model has never been installed, install that family explicitly:

```sh
ai-lab setup install deepseek --yes
ai-lab setup install clm --yes
ai-lab setup install qwen38 --yes
```

Setup verifies and reuses compatible files. Do not delete gigabytes of weights
because a runtime needs repair. See `ai-lab setup --help` for repair options.

The public CLI now contains `web`, `mcp`, `setup`, and machine-oriented `services`. All interactive work is in
the website. Comparison and Watermarking are removed; Completion keeps its
existing view, Decisions offers CLM and Jev, and Decoder combines generation and
detection side by side. Existing profiles are not converted or deleted.

Refresh an installed MCP configuration with `ai-lab mcp install --codex --force`
or `--claude --force`, then restart that client.

AI Lab 0.1.17 retains the runtime pins from 0.1.16, which added TextGrain. After the
Homebrew upgrade, use `ai-lab setup repair-runtime --model deepseek --yes` when
setup reports that the runtime needs repair. This repairs the pinned runtime,
while reusing verified DeepSeek weights. CLM's runtime is unchanged.

The application advances only recognized shipped source manifests whose other
fields and official chat template remain unchanged. Custom sources/templates
remain user-owned. There is no profile or conversation schema migration. For a
rollback, restore the prior application and its shipped source manifest/runtime
pair in the same data root; retain the models, keys, profiles and sessions.

In 0.1.17, Qwen3.8-27B is a new independent generation choice. Adding it does not migrate
DeepSeek, CLM or legacy Qwen3-8B weights/profiles, and does not change existing
model selections. Install `qwen38` only if you want to use it. If CLM previously
failed for lack of memory, restart its owner with `AI_LAB_CLM_ISQ=q4k`; this
changes loading precision while retaining the original downloaded weight files.

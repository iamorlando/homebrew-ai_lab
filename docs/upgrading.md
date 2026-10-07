# Upgrade to AI Lab 0.1.15

1. Stop the old AI Lab website or an old foreground model launcher with Ctrl+C.
2. Upgrade the application:

   ```sh
   brew update
   brew upgrade iamorlando/ai_lab/ai_lab
   ai-lab --version
   ```

   The expected version is `AI Lab 0.1.15`.
3. Open the app with `ai-lab web`. It starts both DeepSeek and CLM APIs and keeps them running.

No data cleanup is required. Keep existing weights, model profiles, watermark
keys and sessions. Keep the same `AI_LAB_ROOT` or `--root` setting if you use one.
The default remains `~/.local/share/ai-lab`, outside the Homebrew Cellar.

If a required model has never been installed, install that family explicitly:

```sh
ai-lab setup install deepseek --yes
ai-lab setup install clm --yes
```

Setup verifies and reuses compatible files. Do not delete gigabytes of weights
because a runtime needs repair. See `ai-lab setup --help` for repair options.

The public CLI now contains `web`, `mcp` and `setup`. All interactive work is in
the website. Comparison and Watermarking are removed; Completion keeps its
existing view, Decisions offers CLM and Jev, and Decoder combines generation and
detection side by side. Existing profiles are not converted or deleted.

Refresh an installed MCP configuration with `ai-lab mcp install --codex --force`
or `--claude --force`, then restart that client.

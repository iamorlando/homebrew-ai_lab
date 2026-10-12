# Model files and setup

`ai-lab setup list --json` reports supported downloads and local availability.
Install a selected family with `ai-lab setup install deepseek --yes`,
`ai-lab setup install qwen38 --yes`, or `ai-lab setup install clm --yes`.
Multiple names and `--with-models` are supported; no selection installs all
supported local families.
Use `ai-lab setup doctor --model qwen38 --json` to inspect its prerequisites.
Existing verified files are reused; native runtime repair is separate:
`ai-lab setup repair-runtime --model deepseek --yes`.

DeepSeek and Qwen3.8-27B generate text. Select the underlying model in Completion
or a saved profile; generation, token inspection, and detection use that model’s
API, chat template, tokenizer, and vocabulary. Qwen3.8-27B (`qwen38`) is an
independent generation family, not CLM or the legacy Qwen3-8B model. Native CLM uses its CLM checkpoint and Qwen
encoder for typed decisions. Jev is hosted and has no local weights.
Create saved generation profiles in the website's **Models** page.


TextGrain profiles have their own context width, block/column counts,
entropy-loss budget, solver iteration limit/tolerance and generation policy.
Completion also supports temporary TextGrain settings. Its Watermarking view
shows vocabulary blocks, a coupling/cost heatmap, entropy calibration and
per-token detection signals. The block-then-token policy additionally shows
the actual sampling draws. Decoder uses TextGrain's native Gamma-tail evidence.

AI Lab 0.1.16 supplies a TextGrain-capable Mistral runtime from
`edc4950d31f1247ed641176e1cf0c9d8ce4d0274`. After upgrading, install the new
runtime with `ai-lab setup repair-runtime --model deepseek --yes` if setup
reports that it is required. Existing verified weights and saved profiles are
reused. SynthID retains its existing tournament behavior.

Changing a saved profile’s underlying model retains its ID, name, seed, key and
watermark settings. Derived vocabulary size follows the newly selected model.
Existing session snapshots retain their original model and settings. Legacy
Qwen3-8B profiles and files remain preserved and are not reinterpreted as Qwen3.8.

An application or runtime upgrade does not invalidate compatible verified model
weights. Setup verifies and reuses them; runtime-only repair never downloads
weights. Missing or corrupt files are reported separately from runtime readiness.

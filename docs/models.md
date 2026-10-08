# Model files and setup

`ai-lab setup list --json` reports supported downloads and local availability.
Install any selection with `ai-lab setup install deepseek clm --yes`.
Existing verified files are reused; native runtime repair is separate:
`ai-lab setup repair-runtime --model deepseek --yes`.

DeepSeek generates text. Native CLM uses its CLM checkpoint and Qwen
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

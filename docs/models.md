# Model files and setup

`ai-lab setup list --json` reports supported downloads and local availability.
Install any selection with `ai-lab setup install deepseek clm --yes`.
Existing verified files are reused; native runtime repair is separate:
`ai-lab setup repair-runtime --model deepseek --yes`.

DeepSeek generates text. Native CLM uses its CLM checkpoint and Qwen
encoder for typed decisions. Jev is hosted and has no local weights.
Create saved generation profiles in the website's **Models** page.

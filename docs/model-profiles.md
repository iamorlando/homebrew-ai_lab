# Saved models

Open `ai-lab web` and choose **Models**. Create a named profile with DeepSeek
as its underlying model, an optional seed, and optional watermark settings.
Profiles share an inference API for their underlying family. Selecting a profile
never requires starting a separate server for that profile.

Saved names, keys and settings persist in the workspace. Completion and Decoder
pickers use these profiles. Decoder inherits the writing model's configuration;
its run-only overrides do not modify a profile. Change and save settings in
Models when you want future generations to use them.

Existing profiles are preserved on upgrade. Keep the same `AI_LAB_ROOT` or
`--root` selection. Download missing families with `ai-lab setup install deepseek
--yes`; the website handles API startup.

Legacy standalone Qwen profiles remain stored but are omitted from active pickers.
They are never silently changed into DeepSeek profiles. New profiles use DeepSeek;
CLM is selected in Decisions and exposes its own persistent API.

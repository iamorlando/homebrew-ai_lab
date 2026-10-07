# Watermark decoder

Run `ai-lab web` and choose **Watermark decoder**.

The left pane generates text from a saved DeepSeek model. Select the
model, enter a prompt, and press Generate. The saved backend, seed, watermark key
and settings are inherited. Use Copy to decoder to transfer the exact output and
its generation configuration to the right pane.

The right pane also accepts pasted or edited text. Select the model that wrote
it to inherit its saved scheme, key and settings. You can choose another model,
change the scheme or fields, or enter a different key to compare the result.
Reset returns to the selected model's saved configuration. Overrides do not edit
profiles, and saved keys are not sent to the browser.

The evidence panel reports p-value, the configured detection threshold, scored
tokens and confidence. Below-threshold evidence is not a missing key. A 98%
value may not meet a 99% cutoff. Insufficient text is reported separately.
Confidence is `1 - p_value` for the known-key test, not a calibrated probability
of authorship. Changing inputs makes the old result stale until you decode again.

Web startup keeps the DeepSeek and CLM APIs running. Missing weights need an
explicit `ai-lab setup install deepseek clm --yes`; existing weights
are reused. There is no terminal decoder command in 0.1.15.

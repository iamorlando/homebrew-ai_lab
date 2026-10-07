# Deleting saved model profiles

Run `ai-lab models delete` in a terminal to choose a saved profile with the arrow
keys, then press Enter or choose the Delete button. Escape or Cancel closes the
picker without deleting anything. The picker contains saved profiles only.
Opening or cancelling this picker reads the saved catalog without starting the
session helper or creating files. A fresh workspace shows an empty picker. The
helper may start only after you choose a saved profile to delete.

Scripts can use an exact profile ID or a case-sensitive saved name:

```sh
ai-lab models list --json
ai-lab models delete PROFILE_ID --json
ai-lab models delete --name "Model name" --json
```

Use one selector. An unknown or ambiguous name is rejected. Bare deletion with
`--json` or without a terminal reports how to supply a target.

In `ai-lab models`, the Delete button or Ctrl+D removes the currently highlighted
table row. Enter still loads a profile's settings. Moving to another row before Delete changes
the deletion target, even when the form still displays the earlier profile.
The top status area reports successful deletion and API errors, including when
the settings form is scrolled out of view.
The Delete button fits an 80×24 terminal; Ctrl+D remains available at 50×18.

Deletion removes only the saved profile. Recorded sessions, downloaded weights,
and running inference servers are preserved. Existing recordings remain readable;
new completion requests using a deleted profile are rejected. Finish or stop an
active completion before deleting a profile. Website publication failures are
reported without a second local write.

# Updating AI Lab

The upgrade target is **AI Lab 0.1.14**. Once this release is published to the
Homebrew tap, update the formula metadata and upgrade AI Lab:

```sh
brew update
brew upgrade iamorlando/ai_lab/ai_lab
ai-lab --version
```

The last command should print `AI Lab 0.1.14` for this release. If it still shows
an older version, check `brew list --versions iamorlando/ai_lab/ai_lab` and
`command -v ai-lab` to confirm which installation your shell is running. If the
tap still provides the older version, keep your data and retry after publication.

Homebrew updates the application. The installed application's default data
folder is `~/.local/share/ai-lab`; `--root`, `AI_LAB_ROOT`, or `AI_LAB_HOME` can
select another folder. A source checkout uses that checkout by default. Keep
using the same data root to retain downloaded weights, saved profiles, watermark
keys, conversations and private settings. `ai-lab weights list --json` reports
the selected root and checks weight integrity separately from runtime readiness.

## Repair a runtime while keeping weights

Open `ai-lab weights`. A model can show **Downloaded** under **Weights**,
**Repair required** under **Runtime**, and **0** missing bytes. That means the
weight files verified successfully, while a runtime or dependency needs setup.
Opening or refreshing this screen does not install anything or start a model.

Choose **Download / repair**, or run `ai-lab weights offer`. Select only the
models you want to repair and press **Enter**. For a scripted repair of an
already-downloaded model, for example:

```sh
ai-lab weights list --json
ai-lab weights install clm --yes
# Or repair Qwen's generation runtime:
ai-lab weights install qwen --yes
```

The installer verifies and reuses existing weights unchanged. Runtime-only
repair downloads zero weight bytes, but it may download a runtime binary or
dependency packages. CLM setup includes its native server and upstream Python
dependencies. This setup step does not start either server. If a weight file is
missing, incomplete, or checksum-invalid, the same explicit install can download
its replacement; zero weight downloads are promised only for verified files.
Qwen generation also needs its own GGUF file, separate from CLM's Qwen encoder
weights. Having the encoder alone does not mean that GGUF is downloaded.

**Esc** skips the picker. **Ctrl+C** cancels setup; verified weights and partial
model downloads are kept. Rerun the same install command or `ai-lab weights offer`
to retry. Dependency failures identify the private log at
`ROOT/.state/ai-lab/model-install.log`. Leave saved settings and existing weights
in place while resolving the reported error.

If the inventory points to another data root with possible existing files,
inspect it with `ai-lab --root /path/to/previous-root weights list --json`.
The installed default can attach verified weights from one supported prior
root during explicit setup. It does not merge private settings, and explicit
root selections do not attach files from another root automatically. Keep the
source files in place when they are reused through links.

## CLM servers running during the upgrade

Open `ai-lab services` after updating. The manager can recognize a verified
healthy native CLM server started by an older AI Lab version, including a launch
from a supported prior data folder. Automatic adoption verifies the actual local
process, endpoint and runtime before enabling Stop, Restart and Interrupt.
Recognition reuses the existing server and weights. Exiting Services preserves
a server started by an earlier launcher.

If CLM is stopped, select **Native Contrastive CLM** and choose **Start**.
Start checks the existing weights and repairs the published runtime when needed.
Keep the Services window open while using a server started there.

For a scripted foreground start:

```sh
ai-lab services --action start --model contrastive
```

Keep that terminal open. Open `ai-lab services` in another terminal to inspect
or control the running server. Closing the owning Services window or pressing
**Ctrl+C** in the foreground launcher stops the servers it started. Opening a
second Services window does not transfer that foreground lifetime to it.

## If ownership still says external

Read the selected service's details. This means AI Lab could not verify that
the process at its configured endpoint belongs to a supported native CLM
launch. Stop that process through its original launcher: press **Ctrl+C** in
the terminal that started it, or use that launcher's Stop control. Then Refresh
Services and choose **Start**, or run the foreground start command above.

This is also the recovery procedure for AI Lab 0.1.13, which cannot recover
ownership records omitted by older CLM launchers. Keep the downloaded models and
settings; stopping the old launcher frees the endpoint for a managed start.

## Existing application API and website

Completion handles a supported older same-owner application API automatically.
You do not need to delete sockets, state or weights to make that compatibility
path work. This application API is separate from the native model server.
Restart an older website through its original launch terminal to load the new
website: **Ctrl+C**, then `ai-lab web`. Unknown external services remain under
their original launcher's control.

## Optional cleanup

No data-directory cleanup is required for an upgrade or runtime repair. Do not
delete `~/.local/share/ai-lab`, or the selected root's `.models`, `.state` or
`.runtime` directories as a troubleshooting step: they contain downloaded
weights, saved data and reusable dependencies.

To reclaim old Homebrew package versions after checking the upgrade, preview
the formula-specific cleanup, then run it if the listed files are appropriate:

```sh
brew cleanup --dry-run iamorlando/ai_lab/ai_lab
brew cleanup iamorlando/ai_lab/ai_lab
```

[Homebrew cleanup](https://docs.brew.sh/Manpage#cleanup-options-formulacask-)
removes old package versions and cached downloads; it does not reset AI Lab's
separate data folder. Keep backups of that folder before any deliberate data
removal, and preserve prior weight roots referenced by reused files.

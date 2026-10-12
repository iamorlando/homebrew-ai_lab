# Root-owned final release native lane

Authorized by the user requests to test Qwen and publish it. Root grants exactly one serialized run of the accepted check_qwen_native.py using installed AI Lab0.1.17 (source217b310fbb96fd4b89fb6ad5679c477a5c71293b; wheel962de95352a893e0c0afef603a5e670dffbad98d3ae56ec46057a9bdd579fb60).

- Installed interpreter: /private/tmp/ai-lab-qwen38-release-017/clean-env/bin/python.
- Owned endpoint: 127.0.0.1:11440; must be vacant and no other model process active.
- Approved owned data root: /Users/orlando/dev/deepseek/.worktrees/qwen38-integration. Only already verified Qwen3.8-27B Q4_K_M weights/assets and existing pinned Metal runtime may be used. No downloads, runtime rebuilds, CLM, DeepSeek or hosted requests.
- One native driver run, at most528 generated tokens, six generation calls plus one32-token MCP call, three detection calls; startup600s, eachcase180s, total20minutes. Existing audited arithmetic tool result is synthetic data, never execute arbitrary model tool requests.
- A no-download installedsetup reuse check may hash existing weights before/after and assert network/download spies remainzero.
- Preserve weights and existing profiles. Stop only receipt-identified newly owned Qwenprocess; verify receipt removed and reusable socket withSO_REUSEADDR plus listenerprobe. No other agent may start models during this lane.

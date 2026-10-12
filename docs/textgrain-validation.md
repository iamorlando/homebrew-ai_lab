# TextGrain feature validation (pre-release snapshot)

Scope: web/client integration against the Mistral TextGrain contract at
`edc4950d31f1247ed641176e1cf0c9d8ce4d0274` and the paper's Figure 1,
Section 3 and Algorithm A.1. Base app commit: `d1bcd6a`.

At the accepted feature commit `bf75a2f`, no native/runtime pins, locks, weights,
user profiles or tournament implementation
files changed. Runtime publication, Homebrew publication and live model execution
are **NOT_RUN**. The existing packaged runtime predates TextGrain, so native use
requires a separately validated runtime upgrade. This is not a release PASS.

## Passing checks

Run from this feature worktree using the repository's locked Python 3.13 venv.
All following completed with exit 0:

- `python -m unittest discover -s harness/tests -p test_textgrain.py -v`: 8 tests,
  configuration validation/defaults, both policies, skipped states, capture
  budget, dimensional/numeric/provenance rejection, configuration binding,
  private-field filtering, Gamma evidence and HTTP request/response routing.
- Run each `harness/tests` file with the same discovery command in its own
  process: `test_completion.py` (13), `test_generation_tournament.py` (5),
  `test_teaching_tournament.py` (4), `test_watermark_scoring.py` (6),
  `test_models.py` (12), `test_detection_lab.py` (10), `test_decoder.py` (17),
  `test_generation_models.py` (38).
- `WatermarkContractTests`, `DetectorHttpTests` from `test_watermarks`, plus
  `TraceProjectionTests`, `TraceHttpTests` from `test_sampling_trace`: 13 tests.
- Run each `tests/ai_lab` file with discovery in its own process:
  `test_mcp_detection.py` (12), `test_mcp_tools.py` (14),
  `test_decoder_service.py` (4), `test_service.py` (8).
- `node --test harness/tests/*.test.mjs`: 72 passed, 0 failed.
- `git diff --check`: exit 0.

The browser commands in `docs/tests.md` exercised real application routes over
owned loopback HTTP fixture servers, with a temporary data root and native
startup disabled. All three TextGrain browser scripts passed. Coverage includes
both generation policies, candidate inspection and keyboard focus, exact-text
append, 1440px/390px views, transport toggle, skip/limit/omission/missing-trace
states, error recovery, saved profile persistence, generation/copy/detection,
three verdicts, private-key filtering and settings reset. The SynthID switch
check retained depth 4 as its UI default, then exercised the existing depth-2
fixture's production bracket and emitted token 99.

Screenshots were visually inspected. A discovered mobile overflow from absolute
accessibility labels was fixed by positioning the heatmap's scroll container.
Early browser assertions were corrected to await asynchronous model loading and
read collapsed evidence using textContent. Early socket/browser sandbox failures
were rerun with the permissions needed for owned CPU fixtures.

Independent review also identified native f64 CDF endpoints that can round a
few ULPs above 1. Validation now permits a 1e-9 accumulation tolerance while
preserving the original values; uniforms must still be strictly less than 1.
The same tolerance handles one-block masses/couplings and tiny negative entropy
diagnostics from native marginal summation. A dedicated regression uses exact
f32 inputs and a 151,936-token accumulation from review and covers preserved rounding and rejected invalid draws.

## Existing broad-suite failures

Before the rounding-only review fix,
`python -m unittest discover -s harness/tests -p 'test_*.py' -q` exited 1:
172 tests, 2 failures, 8 errors, 2 skips. An extracted clean copy of the base
commit runs 165 tests with the same 2 failures, 8 errors and 2 skips. The cases
are obsolete comparison/watermark/Harbor route expectations, an obsolete
OpenCode profile assertion, and tests affected by globally bound workspace
modules. The new scheme-count assertions and detector evidence fixtures were
updated. No remaining broad-suite failure is introduced by TextGrain.

Native detection smoke tests remain opt-in and were not run. Fixture results
prove app configuration, transport, rendering and evidence handling; they do
not prove fresh native generation, solver behavior or native weight reuse.

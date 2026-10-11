# Runtime requirements and supported scope

## Run locally

- Python **3.10 or newer**.
- A writable output directory for evidence.
- A modern browser for the optional local workbench.
- A free loopback port, default **8767**.

The Python reference runtime has no third-party package dependencies. Python's SQLite support supplies the fixture databases. Running `python -m consentdiff` from this directory avoids an installation step. Optional package building uses the build system declared in `pyproject.toml`; that is separate from runtime requirements.

No AI or cloud account, Docker, or external database is needed. Real browser execution additionally needs Node.js 20+, the pinned Playwright dependency (`npm install`), and installed Chrome. Native mode requires actual WebMCP capability; the example testing flag applies only to the disposable browser profile.

## Implemented capability map

| Requirement | Delivered mechanism |
|---|---|
| Declare intent before actions | Fixed scenario-derived intent contract |
| Start from equivalent independent state | Two fresh SQLite stores and before-state digests |
| Exercise human/tool paths | Controller reference, or actual Chrome controls paired with HTTP/native tools |
| Bind approval to consequential arguments | Plan, version, recipient, role, resource, actor, operation |
| Observe persisted effects | Separate read-only connection and effect ledger |
| Detect both paths being wrong | Intent comparison independent of parity |
| Distinguish unknown from empty | Complete/unavailable/partial observer results |
| Preserve meaningful reduction preconditions | Trace validation before deletion candidates run |
| Retain reproducible evidence | A saved witness compared with repeated-run output |
| Verify export integrity | SHA-256 manifest and verified ZIP generation |
| Make behavior visible | Local workbench and manual controller demo |

## Supported inputs

Scenarios are CD-001 through CD-010. Modes are `seeded` and `repaired`. A saved run accepts 1–5 repeats. The reducer accepts an evaluation budget of 2–500 and requires two fresh pairs for each oracle decision.

The internal trace vocabulary is limited to inspect, stage, confirm, cancel, change_role, commit, and retry, with at most 30 actions. Valid ordered journey prerequisites must remain present. These internal interfaces do not imply a public arbitrary-workflow import feature.

The `browser-run` command loads the strict executable `examples/test-config.json` or `examples/native-config.json` format. It allows 1–3 browser repeats and 1–10 built-in scenarios. It accepts no arbitrary website URLs, databases, scripts or locators. The richer `examples/scenarios.json` remains design-only.

## CLI behavior

Commands are `serve`, `catalog`, `run`, `suite`, `minimize`, `verify`, `bundle`, and `browser-run`. Use `python -m consentdiff --help` or the individual subcommand's `--help` for current options.

Exit codes are 0 for PASS, 1 for FAIL, and 2 for INCONCLUSIVE or an input/operation error. An intentionally defective run is expected to return 1 while still saving a valid case.

## Limits

The contract, identity, time, approval token, and scheduling are synthetic. Controller and browser executions are labelled separately. Native WebMCP was exercised on the browser version recorded in VALIDATION.md; production authentication, cryptographic approval and arbitrary external websites are outside scope. The observer is logically separate but shares the same trusted machine.

The reference app is small; no measured minimum RAM, throughput, or performance guarantee is claimed. External-application adapters would have additional requirements.

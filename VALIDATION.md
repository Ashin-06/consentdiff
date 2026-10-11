# Recorded reference validation

Validated on 10 October 2026 with Python 3.12.3 on Windows and headless Chrome for the optional browser checks.

- **34 Python tests passed.** These include all scenario expectations, real SQLite mutations, exact resource/recipient/role/operation checks, duplicate grant and effect detection, confirmation checks independent of success flags, frozen identity mappings, incomplete baselines, expired approvals, bounded reduction, evidence tampering, CLI exit codes, HTTP guards, and interactive session isolation.
- **17 real browser checks passed.** Live configuration, seeded and repaired results, both-paths-wrong and missing-observer cases, six-to-three reduction, all three downloads, both ten-case suites, archive reopening, actual Stage/Confirm/Commit controls, cancellation, form validation, error recovery, keyboard tabs, and all four views at 390px were exercised. No uncaught JavaScript errors or page overflow were observed. Screenshots were visually reviewed.
- **Seeded scenario suite:** 10/10 expectations matched. The application outcomes are 2 PASS, 7 FAIL, and 1 INCONCLUSIVE.
- **Repaired scenario suite:** 10/10 expectations matched. Nine application outcomes PASS; the missing observer remains INCONCLUSIVE.
- **CD-002 reduction:** six actions reduce to `stage`, `confirm`, `commit`, preserving `overbroad_permission` on the tool path. Eight paired evaluations; 1-minimal under valid single-step deletions.
- **Sample evidence:** the retained paired replay matches the repeated oracle. All 11 content files verify against the manifest, including both real SQLite databases.

Actual generated results are in `examples/measured-validation.json`, `examples/browser-validation.json`, and `examples/sample-run/`.

Reproduce the Python checks with `python -m unittest discover -s tests -v`. For browser checks, start `python -m consentdiff serve`, provide Playwright and Chrome in your development environment, and run `node tests/browser_smoke.cjs`.

These original reference measurements cover deterministic controller adapters and separate workbench checks. The real browser/native results are recorded below. Neither set certifies arbitrary external applications, legal consent or production authentication. Hash manifests are unsigned.

## Real integrations validated on 11 October 2026

- **44 Python tests passed** in the final release run, including ten new configuration, session capability, receipt, capture and evidence-boundary checks.
- **HTTP browser suite: 20/20 expectations matched**, covering all ten scenarios in seeded and repaired modes, with two fresh paired trials per row.
- **Native WebMCP suite: 20/20 expectations matched**, with the same coverage and actual registration, discovery and invocation in Chrome 154.0.8037.99 using a disposable testing profile.
- **17 workbench checks passed again**, plus **3 new integration-control checks**: launch an HTTP job, launch a native job with six actual invocations, and fit the integration controls at 390px. No JavaScript errors; the native result screenshot was visually inspected.
- Default Chrome launch reports native capability unavailable. HTTP works independently; required native mode never silently falls back.

Both transport suites preserve seeded outcomes of 2 PASS, 7 FAIL and 1 INCONCLUSIVE, and repaired outcomes of 9 PASS and 1 INCONCLUSIVE. Forty expectation rows across both transports represent 80 fresh paired trials. Suite PASS means expected fixture behavior matched, including intentional defects.

Measured outputs: `examples/browser-http-validation.json`, `examples/browser-native-validation.json`, and `examples/browser-controls-validation.json`. Full per-repeat reports, SQLite states, screenshots, receipts and manifests are in the ignored local `.test-output/http-browser-runs/` and `.test-output/native-browser-runs/` directories. Rerun the documented browser commands to generate new evidence on another machine.

The earlier controller-only scope paragraph describes the original reference run. Native WebMCP is now validated within the precise local scope above. External websites, production authentication, cryptographic approvals, browser-driven reduction and remote attestation remain outside scope.

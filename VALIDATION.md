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

The paired scenario engine calls deterministic controller adapters; browser checks separately drive the visible local interface. These results do not certify external applications, native WebMCP, legal consent, arbitrary browser journeys, or production authentication. Hash manifests are unsigned.

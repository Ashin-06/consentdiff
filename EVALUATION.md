# Evaluation and reproducible checks

This document states what to run and how to interpret it. Record actual outputs before claiming measured test counts, performance, or a complete verification. Browser checks and controller-level experiment checks are separate evidence.

## Reproduce the core workflows

~~~powershell
python -m consentdiff suite --mode seeded
python -m consentdiff suite --mode repaired
python -m consentdiff run --scenario CD-002 --mode seeded --repeats 2 --output-dir runs
python -m consentdiff run --scenario CD-002 --mode repaired --repeats 2 --output-dir runs
python -m consentdiff minimize --scenario CD-002 --mode seeded --budget 100
python -m unittest discover -s tests -v
~~~

A seeded run can correctly return exit code 1 because it detected the expected defect. The suite itself returns 0 only when its expectation checks match. CD-008 should remain inconclusive in repaired mode.

## Catalogue expectations

| ID | Scenario | Seeded experiment expectation | Repaired experiment expectation |
|---|---|---|---|
| CD-001 | Correct viewer share | PASS | PASS |
| CD-002 | Tool widens role | FAIL: overbroad permission | PASS |
| CD-003 | Both paths agree on wrong role | FAIL: intent violation | PASS |
| CD-004 | Tool commits after cancellation | FAIL: cancellation violation | PASS |
| CD-005 | Old approval reused after role change | FAIL: stale confirmation | PASS |
| CD-006 | Same display name maps to wrong user | FAIL: wrong recipient | PASS |
| CD-007 | Success without persisted effect | FAIL: false success | PASS |
| CD-008 | Observer unavailable | INCONCLUSIVE | INCONCLUSIVE |
| CD-009 | Retry duplicates an effect | FAIL: duplicate effect | PASS |
| CD-010 | Both paths respect cancellation | PASS | PASS |

The suite checks these expectations and required finding kinds. Ten passing suite rows do not mean all ten seeded applications were safe.

## What automated tests should establish

- A role mismatch is found from actual persisted state.
- Identically wrong paths still fail against intent.
- Missing observation is not converted into an empty successful state.
- Same-label recipients remain distinguishable by logical identity.
- Pre-commit cancellation and stale approval prevent effects in the safe fixture.
- A retry cannot create duplicate effects in the safe fixture.
- Invalid trace reductions cannot manufacture a smaller failure.
- Limited budgets do not establish unsupported one-minimality.
- Saved witness state matches the repeated scenario result.
- Manifest verification rejects missing, changed, unsafe, or unexpected evidence.

Use the current test source and retained execution output to identify which checks ran on a particular checkout.

## Reduction interpretation

The default confirmation trace contains optional inspect steps plus mandatory stage, confirm, and commit steps. The reference reduction should be assessed by inspecting its returned signature, minimized steps, history, one_minimal flag, and budget use.

Each valid oracle decision uses two fresh pairs. A smaller trace must preserve the same kind and affected journey. This is a bounded reduction over an existing fixture trace, not discovery of an arbitrary website workflow.

## Evidence checks

Verify a generated run:

~~~powershell
python -m consentdiff verify runs/<actual-case-id>
~~~

Then copy that run to a disposable location, change one covered file, and confirm verification rejects the modified copy. Keep the original result intact.

Bundle export verifies before producing the archive. The manifest covers 11 content files; its unsigned hashes establish consistency with the manifest, not trusted origin.

## Browser validation

Separate browser checks can exercise the four workbench tabs, run and display a paired experiment, use the manual Stage/Confirm/Commit controls, inspect cancellation, reopen an archived case, and download evidence.

These checks do not turn the automated paired suite into a browser-driven suite. The runner still calls the same action controller directly. Native WebMCP and external websites remain untested.

## Metrics appropriate to publish

Publish expectation matches in each mode, repeated-outcome consistency, witness replay agreement, observed findings, reduction size/budget, and integrity verification. Report runtime or memory only when measured with environment details.

A small seeded catalogue does not establish population-wide detection accuracy. General recall or false-alarm claims would need independently designed cases, a declared denominator, and additional applications.

## External validity

The result is bounded to fictional file sharing, deterministic scheduling/time, fixture approvals, and a same-machine observer. It does not establish legal consent, real authentication, adversarial website truthfulness, broad browser compatibility, or correctness of arbitrary agent workflows.

# ConsentDiff — Human–Agent Consistency Tester

**Status: implemented local reference prototype.** ConsentDiff compares two paths through a fictional file-sharing application against a fixed user-intent contract and the effects actually stored in SQLite.

A person authorizes **viewer access** for one recipient. A deliberately defective tool path grants **editor access** instead. ConsentDiff shows the discrepancy, the approval record, and the saved permission that establishes it. It also catches cases where both paths agree but both violate the intent.

**Scope:** the paired runner drives the human action controller directly, using the same controller as the visible local demo. It is not a browser-driven end-to-end suite, native WebMCP adapter, or arbitrary-website tester.

## Start the local application

From this project directory, with Python 3.10 or newer:

~~~powershell
python -m consentdiff serve --port 8767 --runs-dir runs
~~~

Open [http://127.0.0.1:8767](http://127.0.0.1:8767). Keep the terminal open and press Ctrl+C there to stop the server. On Windows, `./Start-ConsentDiff.ps1` is the included launcher. If your system uses the Python launcher, substitute `py -3` for `python`.

The runtime uses Python's standard library. Running from this directory requires no third-party Python package, model API, browser-automation installation, cloud account, or database server.

## What is implemented

- Separate SQLite application states for the human and structured-tool paths.
- A frozen intent: share `file-42` with `user-7`, as viewer, with current approval.
- Confirmation, cancellation, changed-argument, and retry behavior.
- A read-only effect observer using a separate SQLite connection.
- Ten built-in scenarios in both **seeded** and **repaired** modes.
- Comparison against intent as well as cross-path agreement.
- Repeated fresh runs and an explicit inconclusive result when evidence is unavailable.
- Valid-step reduction that preserves a particular finding kind and affected path.
- An interactive local demo, saved case archive, HTML/JSON reports, verified ZIP bundles, and integrity checks.

The observer is logically separate from the application controller, but runs on the same machine. It is not remote attestation or a separate trust service.

## Explore the four tabs

1. **Paired experiment:** select a scenario and mode, run it, and inspect effects and approval traces side by side.
2. **Scenario checks:** compare the ten observed outcomes with their declared expectations.
3. **Try the controls:** manually stage, confirm or cancel, change role, commit, and retry in temporary fictional apps.
4. **Evidence archive:** reopen saved paired runs and download their records.

The temporary interactive demo is separate from saved experiment evidence. Starting it does not create an archived run.

## Command-line examples

~~~powershell
python -m consentdiff catalog
python -m consentdiff run --scenario CD-002 --mode seeded --repeats 2 --output-dir runs
python -m consentdiff run --scenario CD-002 --mode repaired --repeats 2 --output-dir runs
python -m consentdiff suite --mode seeded
python -m consentdiff suite --mode repaired
python -m consentdiff minimize --scenario CD-002 --mode seeded --budget 100
~~~

The run command prints its actual case ID. Use that directory for verification and export:

~~~powershell
python -m consentdiff verify runs/<printed-case-id>
python -m consentdiff bundle runs/<printed-case-id> --output consentdiff-evidence.zip
~~~

Replace the placeholder with the printed ID. Save the ZIP outside the run directory and choose a new filename; bundle export refuses to overwrite an existing file.

## Read results correctly

An experiment returns **PASS** when the observed paths satisfy the fixture contract, **FAIL** when a violation is established, and **INCONCLUSIVE** when the evidence cannot establish a result.

A suite PASS means all its expectations matched. Correctly detecting a seeded failure is a passing suite check. Repaired mode still leaves CD-008 inconclusive because repairing the application does not make an unavailable observer available.

CLI exit codes are **0 = PASS, 1 = FAIL, 2 = INCONCLUSIVE or error**. A seeded run can save its evidence successfully and return 1 because the intended defect was detected.

## Evidence you can inspect

A saved case contains the declared intent, separate before/after observations, ordered traces, two application databases, the result JSON, an HTML report, and a SHA-256 manifest. The saved witness is a fresh replay compared with the repeated-run result. It is not a capture of every discarded repeat.

Verification checks bytes against the unsigned manifest. It detects changes relative to that manifest; it does not prove authenticity or stop someone with access from rewriting both data and hashes.

## What is not implemented

No native WebMCP invocation, automatic website discovery, Playwright-driven paired suite, general contract loader, real authentication, production consent system, or external-application integration is included. The scenario and intent are fixed fictional fixtures.

`examples/test-config.json` and `examples/scenarios.json` are **design-only specifications**. The runtime uses its built-in catalogue and does not load those inputs. `examples/measured-validation.json` and `examples/sample-run/` contain actual generated results. The larger design is preserved in [INTEGRATION_ROADMAP.md](INTEGRATION_ROADMAP.md).

## Read the detailed documentation

| Document | Purpose |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Actual file tree, modules, and trust boundaries |
| [WORKFLOW.md](WORKFLOW.md) | Complete example from intent to saved evidence |
| [DATA_CONTRACTS.md](DATA_CONTRACTS.md) | Actual result fields and example-input limitations |
| [EVALUATION.md](EVALUATION.md) | Reproduction commands and scenario expectations |
| [VALIDATION.md](VALIDATION.md) | Recorded test results and curated sample evidence |
| [REQUIREMENTS.md](REQUIREMENTS.md) | Runtime needs and supported input limits |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | Delivered scope and remaining milestones |
| [SECURITY_SCOPE.md](SECURITY_SCOPE.md) | Local operation and evidence limitations |
| [INTEGRATION_ROADMAP.md](INTEGRATION_ROADMAP.md) | Future browser/native-tool integrations |

## Contribution and prior art

The contribution is this concrete reference harness: paired physical state, explicit intent, observed effects, bounded reproduction reduction, and reviewable evidence. UI/tool parity is an established idea.

- [isWebMCP's UI/tool parity guidance](https://iswebmcp.com/learn/shared-services-ui-webmcp-parity) describes equivalent journeys and shared postconditions.
- [WindTunnel](https://webmcp.com/blog/windtunnel-webmcp-browser-agent-benchmark) compares WebMCP and browser-agent interfaces.
- [WebMCP data-rights workbench](https://github.com/webmaxru/webmcp-data-rights-workbench) demonstrates confirmation-bound staging and cancellation.
- [GoogleChromeLabs example WebMCP extension](https://github.com/GoogleChromeLabs/webmcp-extension/) provides a native-tool experimentation reference; it is not a dependency or implemented adapter here.

This project makes no “first ever” claim. It does not require or use AI to decide whether a permission changed.

# ConsentDiff — Human–Agent Consistency Tester

**Status: implemented local reference prototype.** ConsentDiff compares two paths through a fictional file-sharing application against a fixed user-intent contract and the effects actually stored in SQLite.

A person authorizes **viewer access** for one recipient. A deliberately defective tool path grants **editor access** instead. ConsentDiff shows the discrepancy, the approval record, and the saved permission that establishes it. It also catches cases where both paths agree but both violate the intent.

**Scope:** two accurately labelled runners are included. The fast reference drives deterministic controllers. The browser integration clicks real Chrome controls and pairs them with structured HTTP tools or actual native WebMCP registration, discovery and invocation. Both target only this owned disposable application.

## Start the local application

From this project directory, with Python 3.12 or newer:

~~~powershell
python -m consentdiff serve --port 8767 --runs-dir runs
~~~

Open [http://127.0.0.1:8767](http://127.0.0.1:8767). Keep the terminal open and press Ctrl+C there to stop the server. On Windows, `./Start-ConsentDiff.ps1` is the included launcher. If your system uses the Python launcher, substitute `py -3` for `python`.

The controller runtime uses Python's standard library. The optional browser runner additionally needs Node.js 20+, Playwright and installed Google Chrome. It needs no model API, cloud account or database server.

Install the pinned browser dependency locally with `npm install`, then run:

~~~powershell
python -m consentdiff browser-run --config examples/test-config.json --output-dir runs
python -m consentdiff browser-run --config examples/native-config.json --output-dir runs
~~~

Both commands start their own temporary loopback server and test all ten scenarios in seeded and repaired modes with two independent repeats. The native config enables Chrome's WebMCP testing feature only in a disposable profile and requires actual native support. It fails explicitly if unavailable. The workbench also has **Run in Chrome** and **Run all 10 in Chrome** controls. See [BROWSER_INTEGRATION.md](BROWSER_INTEGRATION.md) for setup, evidence and capability details.

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
- Actual browser journeys, server-correlated action receipts, visible plan/approval captures, screenshots and separate read-only database observations for every repeat.
- Strict executable configuration with bounded built-in scenarios and validated action sequences; optional native WebMCP and explicit HTTP fallback.

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

A saved case contains the declared intent, separate before/after observations, ordered traces, application databases, result JSON, HTML report and a SHA-256 manifest. Controller cases keep a fresh replay compared with the repeated-run result. Browser cases keep the actual databases, browser action captures, receipts, screenshots and runtime capability record from every executed repeat; they are not reconstructed by controller replay.

Verification checks bytes against the unsigned manifest. It detects changes relative to that manifest; it does not prove authenticity or stop someone with access from rewriting both data and hashes.

## What is not implemented

Automatic website discovery, arbitrary contracts, production authentication, external applications and AI workflow discovery are not included. The scenario and intent remain fixed fictional fixtures. Browser-case minimization is not implemented; the workbench clearly restricts the existing reducer to controller cases.

`examples/test-config.json` and `examples/native-config.json` are executable browser configurations. `examples/scenarios.json` retains a richer **design-only** language; it is not accepted by the loader. `examples/browser-http-validation.json` and `examples/browser-native-validation.json` contain actual measured integration results. Earlier controller measurements and sample evidence remain available. [INTEGRATION_ROADMAP.md](INTEGRATION_ROADMAP.md) distinguishes delivered integrations from broader future work.

## Running as a service

The container image runs the same workbench in production mode, still with no third-party packages:

```bash
docker build -t consentdiff .
python -m consentdiff.ops keygen            # one API key per person: analyst, viewer or monitor
docker run -d --name consentdiff -p 8767:8767 -v consentdiff-data:/data \
  -e CONSENTDIFF_KEYS_FILE=/run/secrets/consentdiff-keys.json -e CONSENTDIFF_ALLOWED_HOSTS=lab.example.org \
  consentdiff
```

With API keys configured, every `/api` route needs a key (`X-API-Key` or `Authorization: Bearer`): `analyst` runs experiments, `viewer` opens saved cases and downloads, `monitor` reads `/metrics`. The page asks for the key once per browser session. `/healthz` and `/readyz` are open for probes; requests are rate-limited per client and logged as JSON lines with request IDs, without submitted content. See [docs/runbook.md](docs/runbook.md) and [docs/threat-model.md](docs/threat-model.md).

| Variable | Purpose |
|---|---|
| `CONSENTDIFF_ENV=production` | refuse to start without hashed API keys |
| `CONSENTDIFF_API_KEYS` / `CONSENTDIFF_KEYS_FILE` | hashed API keys with roles |
| `CONSENTDIFF_HOST`, `CONSENTDIFF_PORT` | default `127.0.0.1:8767`; any other address needs API keys |
| `CONSENTDIFF_ALLOWED_HOSTS` | host names clients use, besides loopback (DNS-rebinding protection) |
| `CONSENTDIFF_DATA_DIR` | where cases are kept (default `./runs`, `/data` in the image) |
| `CONSENTDIFF_RATE_LIMIT` | requests per minute per client (default 120) |

Browser automation (real Chrome driving the workbench) stays a workstation feature: run `consentdiff browser-run` locally. With API keys configured, the `/api/browser/*` routes are switched off, and a key-less loopback workbench is not rate-limited so its browser runs aren't throttled.

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
| [INTEGRATION_ROADMAP.md](INTEGRATION_ROADMAP.md) | Delivered integrations and future extensions |

## Contribution and prior art

The contribution is this concrete reference harness: paired physical state, explicit intent, observed effects, bounded reproduction reduction, and reviewable evidence. UI/tool parity is an established idea.

- [isWebMCP's UI/tool parity guidance](https://iswebmcp.com/learn/shared-services-ui-webmcp-parity) describes equivalent journeys and shared postconditions.
- [WindTunnel](https://webmcp.com/blog/windtunnel-webmcp-browser-agent-benchmark) compares WebMCP and browser-agent interfaces.
- [WebMCP data-rights workbench](https://github.com/webmaxru/webmcp-data-rights-workbench) demonstrates confirmation-bound staging and cancellation.
- [Chrome's imperative WebMCP API](https://developer.chrome.com/docs/ai/webmcp/imperative-api) documents the native API used by the adapter. No extension or polyfill is required.

This project makes no “first ever” claim. It does not require or use AI to decide whether a permission changed.

## License

MIT. See [LICENSE](LICENSE).

# Real browser integration

ConsentDiff executes the owned disposable file-sharing app in headless Chrome. The human runner uses Playwright `locator.click()` on rendered controls for every action, including inspection, staging, approval, cancellation, changed arguments, commit and retry. It does not call a Python controller or page action function for the human path. The tool runner either invokes a registered native WebMCP tool or uses the explicitly labelled structured local HTTP adapter.

## Setup and run

Requires Python 3.10+, Node.js 20+, installed Google Chrome and Playwright. From this directory, `npm install` installs the pinned Playwright 1.62.1 dependency in local `node_modules`. The runner uses the installed Chrome channel; no Playwright browser download is required. If Chrome is absent, install Google Chrome through its official installer.

```powershell
npm install
python -m consentdiff browser-run --config examples/test-config.json --output-dir runs --summary .test-output/http-summary.json
python -m consentdiff browser-run --config examples/native-config.json --output-dir runs --summary .test-output/native-summary.json
```

Each command owns a temporary loopback server, isolated browser profile and fresh SQLite pair per trial. It closes the server and browser after completion. Forty paired trials run per command: ten scenarios × two application modes × two repeats. A suite PASS means expected outcomes matched; intentionally unsafe seeded cases must report FAIL, and CD-008 must stay INCONCLUSIVE.

For the workbench, start `python -m consentdiff serve`, then use **Run in Chrome** or **Run all 10 in Chrome** in the experiment sidebar. Select HTTP, automatic detection or required native WebMCP. The testing checkbox changes only the disposable browser launch. Saved cases reopen through the existing archive, HTML report and ZIP download controls.

## Native capability, precisely

The page feature-detects `document.modelContext.registerTool`, `getTools` and `executeTool`. It registers `consentdiff_action`, discovers that tool and invokes it through the browser API. No `modelContext` mock or polyfill is created. The report records the browser version, secure-context status, registration, discovery, invocation count, selected transport and testing flag.

Measured Chrome 154.0.8037.99 has no `document.modelContext` in a normal fresh launch. Automatic selection therefore uses `structured-http` and records the unavailable native API. A disposable launch with `--enable-features=WebMCPTesting` exposes the actual native API and passed all scenarios. Requiring native support without an available API is an error, never a simulated native pass. Chrome ≤154 uses JSON-string execution arguments; Chrome ≥155 uses object arguments, matching the documented transition.

Primary references checked 11 October 2026: [Chrome WebMCP and local testing flag](https://developer.chrome.com/docs/ai/webmcp), [imperative registration, discovery and execution](https://developer.chrome.com/docs/ai/webmcp/imperative-api), and [WebMCP community draft](https://webmachinelearning.github.io/webmcp/). The API remains experimental; support is detected at runtime.

## Executable configuration

Schema `1.0` accepts exactly `schema_version`, `fixture`, `scenarios`, `modes`, `repeats`, `tool_adapter`, and `webmcp_testing`. The fixture must be `consentdiff-owned-local-app`. Choose 1–10 unique built-in scenario IDs, seeded/repaired modes, 1–3 repeats, and `auto`, `http` or `native` tools. Unknown fields, invalid types, duplicate JSON keys and unsafe action orders are rejected. An optional `steps` array on a scenario may omit inspections or the optional retry only when the consent prerequisites remain valid. No URL, script, executable path, arbitrary locator or external application can be supplied.

The older `examples/scenarios.json` is a design record, not an accepted configuration. The executable examples use the current loader and validated catalogue.

## Saved evidence and boundary

Driver capabilities are different for each path. The private evidence capability cannot be obtained from a driver view. Driver responses expose application plan/approval/message state, not the independent observer. The backend enforces the declared action order and issues a receipt for each action.

The finalization boundary rejects missing captures, mismatched receipts, altered consent records, repeated-session reuse and unsupported native claims. It ignores no client verdict because no verdict field is accepted. It independently reopens the backend-owned SQLite databases read-only using frozen setup mappings and recomputes the comparison. Every repeat includes before/after observations, the actual databases, action/approval records, receipts, visible DOM captures and before/after PNG screenshots. All files enter the existing unsigned SHA-256 manifest. The second and third trials are stored under `evidence/repeats/`.

This is one local trust domain: a hostile administrator or modified runner can fabricate captures and hashes. Receipts establish internal correlation, not remote attestation. Actions are selected by a deterministic test plan, not a human or an autonomous model. Screenshots contain only fictional data. External website testing, production authentication and browser-driven trace minimization remain outside scope.

## Validation

`python -m unittest discover -s tests -v` covers the controller and browser boundaries. The two browser-run commands perform the actual browser integration. `node tests/browser_smoke.cjs` tests the workbench UI against a running server. Generated evidence, logs, `node_modules` and runtime outputs stay in ignored directories; compact measured suite summaries are retained in `examples/`.

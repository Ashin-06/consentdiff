# Architecture — reference and real browser runners

ConsentDiff checks three things: the declared action, the records of its approval and execution, and the state actually stored by two fictional application paths. Both paths must satisfy the contract; matching each other is insufficient.

## Actual file structure

~~~text
consentdiff/
  __init__.py              # package version
  __main__.py              # module entry point
  cli.py                   # reference commands and browser-run
  config.py                # strict executable scenario configuration
  browser.py               # Node worker invocation and bounded UI jobs
  browser_runner.cjs       # actual Playwright human/tool journeys
  browser_sessions.py      # capabilities, receipts, independent final observation
  core.py                  # application fixture, observer, comparison, reducer
  evidence.py              # atomic saved cases, manifests, verified ZIP export
  reports.py               # standalone readable report
  server.py                # loopback API and static-file server
  sandbox.py               # bounded temporary interactive demo sessions
  static/
    index.html             # four-tab local workbench
    styles.css             # presentation
    app.js                 # interface, browser jobs and local API calls
    driver.html            # isolated rendered journey controls
    driver.js              # HTTP/native WebMCP tool surface
tests/
  test_core.py             # fixture, oracle, and reduction checks
  test_integration.py      # evidence and server checks
  test_browser_integration.py # config, receipt and evidence boundary checks
  browser_smoke.cjs        # optional Playwright/Chrome checks of the real interface
examples/
  test-config.json         # executable HTTP browser configuration
  native-config.json       # executable native WebMCP configuration
  scenarios.json          # future specification, not loaded by runtime
  measured-validation.json # actual suite and reduction results
  sample-run/              # generated paired SQLite witness and verified report
Start-ConsentDiff.ps1      # Windows launcher
pyproject.toml            # package metadata; runtime dependencies are empty
runs/                     # generated cases, not source
~~~

The source tree implements both the controller reference and owned local browser integration. [BROWSER_INTEGRATION.md](BROWSER_INTEGRATION.md) documents the actual browser lifecycle; [INTEGRATION_ROADMAP.md](INTEGRATION_ROADMAP.md) distinguishes further external-application work.

## Human and tool paths

`Application` in `core.py` provides the same action controller used by the visible demo. The paired runner invokes this controller directly with a human or tool driver label.

The fast reference runner invokes controllers directly. The separate `browser-run` runner clicks actual rendered controls for the human path and invokes structured HTTP or native WebMCP for the tool path. Native mode registers, discovers and executes the real `document.modelContext` tool, with feature detection and invocation records. Both paths use fresh independent databases for every repeat.

The browser session backend validates ordered actions and capture receipts, then recomputes the result from its own databases and frozen identity maps. Client-submitted verdicts are not accepted. Saved browser cases retain actual databases, receipts, visible captures and screenshots from each repeat; controller cases retain their independently checked replay.

## Two independent fixture databases

Each paired run creates `human/application.sqlite` and `tool/application.sqlite`. They contain users, grants, and a committed-effect ledger. Physical user IDs differ between the two databases; setup supplies explicit logical mappings.

Both `user-7` and `user-8` are displayed as Maya, making it possible to demonstrate why a display name is insufficient for identifying a recipient. Comparisons use logical identities rather than labels.

Before-state observations must be complete, empty, and equivalent to establish a clean pair. Missing or mismatched baseline evidence prevents PASS. An independently established violation can still produce FAIL.

## Data flow

~~~text
built-in scenario -> fixed intent + valid ordered trace
                           |
                 fresh independent apps
                    /            \
          human controller     tool controller
                    |            |
            actual SQLite mutations
                    |            |
              read-only observers
                    \            /
                 intent + parity checks
                           |
               repeat consistency / reduction
                           |
             saved witness + report + manifest
~~~

The observer opens a separate read-only SQLite connection. It reads actual grants and effects and normalizes physical recipient IDs using the frozen setup mapping. It checks the mutable users table against that mapping. Missing mapping, identity drift, and orphaned records produce incomplete evidence; a database row cannot redefine the intended recipient.

The observer and application remain within one machine/process trust environment. This is logical separation suitable for a controlled fixture, not independent trusted infrastructure.

## Actions and approval binding

The supported actions are `inspect`, `stage`, `confirm`, `cancel`, `change_role`, `commit`, and `retry`.

A staged plan identifies actor, operation, resource, recipient, role, and version. Confirmation copies that plan and adds a fixed fixture expiry and token. The safe controller requires approval to match the current plan. A role change increments the version; an old confirmation cannot authorize the changed plan.

These are deterministic fixture values. There is no real identity authentication, token signature, clock synchronization, or production approval service.

## What comparison checks

The comparator requires both persisted grant and effect records to match the exact expected recipient, role, resource, operation, and count. It finds role widening, wrong recipient/resource/operation, cancellation violation, stale approval, duplicate records, missing successful effects, confirmation mismatch, and cross-path divergence. Every observed record must correspond to an uncancelled commit plan with matching approval and unexpired validity at the recorded clock, regardless of the response's claimed commit status.

If both paths produce the same incorrect effect, the intent violation still fails. If the observer is unavailable, an empty-looking result is not treated as proof of no effect.

The scope is the fixed file-sharing contract. Do not infer support for arbitrary business rules or resources from this limited comparator.

## Repaired mode

Repaired mode selects the safe application behavior while retaining the scenario's journey. A cancelled or stale-confirmation journey must have no effect. An observer-unavailable scenario remains unavailable in both modes.

This separation prevents the repair from silently redefining the evidence problem as a successful application outcome.

## Reduction

The reducer starts with the scenario's built-in trace and uses its first finding's kind and affected journey as a signature. It attempts individual step deletions while retaining ordered journey preconditions.

Every oracle decision repeats two fresh paired runs. Invalid traces are rejected without being mistaken for smaller bugs. A one-minimal result means no further valid single-step deletion preserves the selected violation within the completed search. It is not a globally shortest trace or automatic workflow discovery.

## Saved witness

The evidence layer repeats the selected scenario, then runs another pair into the evidence directory. It compares that retained witness with the repeated-run result. Disagreement makes the case inconclusive.

This distinction matters: the exported databases belong to the retained witness, not all earlier temporary repeats. The manifest covers the result, report, intent, observations, traces, and databases; the manifest itself is unsigned.

## Local server

`server.py` binds to 127.0.0.1, restricts accepted Host values, rejects cross-origin writes when an Origin is supplied, accepts JSON requests, limits body size, and serializes experiments. These are local-service boundaries, not a multi-user authorization system.

The interactive sandbox retains at most eight temporary sessions and bounds action counts. It is separate from archived experiments and is cleaned up when the server closes.

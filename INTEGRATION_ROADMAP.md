# Integration status and remaining architecture

The owned local browser integration is now delivered. `browser_runner.cjs` clicks actual Chrome controls, `driver.js` registers and invokes native WebMCP when available, and `browser_sessions.py` validates captures and independently observes SQLite. The strict loader accepts the executable HTTP/native configurations. See [BROWSER_INTEGRATION.md](BROWSER_INTEGRATION.md) for commands and measured capabilities. Arbitrary applications and AI workflow discovery remain future work.

## Browser-driven human journeys

Delivered: the Playwright adapter drives actual visible controls, records displayed plans and confirmations, follows cancellation/change/retry scenarios, and retains authoritative observations plus screenshots for every repeat.

The earlier controller adapter remains available for fast reference testing and reduction. Reports distinguish it from browser execution. Browser cases cannot invoke the controller reducer while claiming a browser-minimized result.

## Native WebMCP tool journeys

Delivered: real `document.modelContext` registration, discovery and invocation with feature detection and recorded invocation counts. Chrome 154.0.8037.99 passes with the WebMCP testing feature enabled in a disposable profile; default launch records unsupported capability and can use HTTP fallback.

The structured HTTP path is separately labelled. It is never relabelled native WebMCP. Current primary documentation is linked in the integration guide; later API revisions require new runtime validation.

## Proposed future structure

~~~text
Future modules, not implemented files:
  adapters/browser.py           # actual visible-control journeys
  adapters/webmcp.py            # native page-tool discovery/invocation
  adapters/application.py       # external owned-application contract
  contract_loader.py           # strict scenario/intent validation
  workflow_mapping.py          # reviewed mapping between action surfaces
  observers/application_api.py # authoritative external effect observation
  tests/browser/               # browser-driven paired suites
  tests/adapters/              # independently reset integration fixtures
~~~

The delivered controller uses dependency-free Python. The delivered browser runner uses JavaScript, Playwright and installed Chrome. The modules listed above describe possible external-application extensions, not missing requirements for the delivered owned local integration.

## Declarative inputs

`examples/test-config.json` and `examples/native-config.json` are executable schema 1.0 inputs. `examples/scenarios.json` alone retains the richer design language and is not executable.

The loader rejects unknown fields, duplicate JSON keys, invalid types and invalid action orders; it limits scenarios and repeats and accepts no arbitrary scripts, URLs or locators. Broader contracts would need their own reviewed schema and adapters.

## Cross-application equivalence

For a second application, define what constitutes the same action and the same permitted result. Compare stable identities, consequential fields, confirmation binding, and authoritative effects. Different physical IDs or irrelevant timestamps may be normalized only through documented rules.

Money, if added, requires integer minor units and currency. Permission sets may require set comparison, while ordered business events may not be safely sorted. Do not erase differences with a vague similarity score.

## Trust and privacy

An external observer must establish what it can actually prove. An application's own success message is not independent effect evidence. A database read may be adequate in an owned staging environment but does not attest to a malicious third-party service.

Future screenshot, accessibility-tree, network, and tool traces need field-level redaction, restricted storage, retention controls, and fictional or explicitly authorized accounts. The current loopback fixture does not supply these deployment controls for a customer environment.

## Automated pairing and optional AI

Automatic discovery could suggest that a visible share control corresponds to a particular tool call. Treat that mapping as a proposal until validated. Ambiguous mappings should produce an unresolved result rather than a guessed equivalence.

AI may propose mappings or explain a verified finding. It must not decide whether the server committed an effect, manufacture approval, or change the intent after seeing the result. The current prototype uses no model API.

## Evidence needed for broader claims

A browser-integration claim requires recorded browser actions and backend effects. A native-WebMCP claim requires actual native tool invocation. A cross-application claim requires evaluation beyond the single included fixture.

Retain exact versions, mappings, reset procedures, safe controls, seeded defects, and observed limitations. The existing local reduction is one-minimal under valid action deletion, not proof of the shortest possible real-world workflow.


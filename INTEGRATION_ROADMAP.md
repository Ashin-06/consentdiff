# Future integration architecture

The local reference is implemented. This document preserves the larger product design without implying that browser-driven suites, native WebMCP, arbitrary application adapters, or AI workflow discovery already exist.

## Browser-driven human journeys

A future adapter should drive actual visible controls using a supported browser automation tool. It must record the meaningful confirmation values, errors, cancellations, and resulting authoritative state.

The current human adapter calls the shared application controller directly. Keep both adapters available and identify them accurately in reports. Passing controller tests is not evidence that a browser locator, accessibility label, rendered dialog, or focus behavior is correct.

## Native WebMCP tool journeys

Add actual discovery and invocation against a pinned browser and API version. Feature-detect support, record the tool registration and invocation, and make unsupported runs explicit.

The existing structured tool controller is local Python application behavior. It cannot be relabeled as native WebMCP. Native API changes and browser support must be checked against primary documentation during implementation.

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

The original design considered TypeScript and Playwright for browser-heavy work. The delivered reference instead uses dependency-free Python. Future integrations may use either approach, but their dependencies and interoperability require real implementation and testing.

## Declarative inputs

The JSON files under `examples/` retain the proposed richer scenario/configuration format. They are not executable inputs to the reference runner.

A real loader needs versioned schemas, rejected unknown fields, typed actions, reviewed locators and adapters, limits on resources, safe reset behavior, and no arbitrary script execution. Input validation must distinguish absent values, null, false, and empty values where the application semantics differ.

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


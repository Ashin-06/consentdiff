# Delivered reference and future milestones

ConsentDiff now includes a working local reference application, paired-controller runner, effect oracle, reducer, evidence workflow, and browser workbench. The larger automatic website-testing product remains future work.

## Delivered components

- Two independent physical SQLite fixture stores and explicit logical identity mappings.
- Fixed intent and ordered traces for ten known scenarios.
- Human and structured-tool controller adapters.
- Current-plan confirmation, pre-commit cancellation, stale approval, and retry examples.
- Seeded and repaired modes with an unavailable-observer case preserved in both.
- Read-only observation of persisted grants and committed effects.
- Intent checks in addition to cross-path comparison.
- Repeated fresh runs, a retained witness replay, and consistency checks.
- Valid-step reduction with bounded one-minimality claims.
- Local server, interactive demo, run archive, report generation, manifest verification, and ZIP export.

The paired runner does not use browser automation. The visible demo shares its action controller with the human adapter, allowing focused browser checks without claiming that the full automated suite clicked through the interface.

## Validation gate

Use [EVALUATION.md](EVALUATION.md) to reproduce the delivered behavior. Retain actual outputs before claiming test counts, reduction counts, or performance. A suite expectation match is different from a secure experiment outcome.

The gate includes seeded and repaired suites, a saved defective case, a repaired case, unavailable evidence, reduction, bundle verification, and integrity rejection after deliberate modification of a disposable copy.

## Next milestone — browser-driven journeys

Implement an actual browser adapter that interacts with visible controls and captures confirmation values. Keep it separate from the controller adapter and report which one ran.

Completion requires evidence that browser interactions reached the authoritative backend state, with reset checks and stable identity mappings. A screenshot alone does not establish the resulting permission.

## Next milestone — native WebMCP

Implement discovery and invocation against a pinned browser/API version. Record feature detection and actual invocations. Unsupported configurations should be explicitly skipped or inconclusive.

Do not rename the current local tool controller as a native WebMCP adapter. It is a distinct implementation and evidence boundary.

## Next milestone — general contracts and applications

Add strict schemas and a real loader for reviewed intent contracts, application adapters, locators, and journey definitions. The JSON examples currently document future inputs and are not parsed by the runtime.

Test a second owned application before making cross-application claims. Its domain semantics may require different rules for ordering, retries, money, object identity, and cancellation.

## Next milestone — automatic workflow pairing

A later system could propose mappings between visible actions and tool operations. Ambiguous mappings should remain unresolved until validated. AI may help suggest a mapping or explain a confirmed finding, but should not be the authority on whether an effect occurred.

## Product readiness beyond a portfolio prototype

An external-facing product would require reliable adapter maintenance, customer-specific fixture isolation, authentication, access controls, privacy handling, configurable retention, and clear operator permissions. The current loopback development server is not such a hosted service.

The extended architecture, proposed modules, and integration evidence requirements are preserved in [INTEGRATION_ROADMAP.md](INTEGRATION_ROADMAP.md).

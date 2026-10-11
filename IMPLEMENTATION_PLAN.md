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

The fast paired runner remains controller-based. A separate real browser runner is also delivered: visible human clicks, HTTP/native WebMCP tools, strict configuration, bounded jobs, receipt correlation, independent backend observations and per-repeat evidence.

## Validation gate

Use [EVALUATION.md](EVALUATION.md) to reproduce the delivered behavior. Retain actual outputs before claiming test counts, reduction counts, or performance. A suite expectation match is different from a secure experiment outcome.

The gate includes seeded and repaired suites, a saved defective case, a repaired case, unavailable evidence, reduction, bundle verification, and integrity rejection after deliberate modification of a disposable copy.

## Delivered — browser-driven journeys

`browser_runner.cjs` drives actual rendered controls and captures displayed confirmations. The backend validates receipts and observes committed state with frozen mappings. Both modes and all ten scenarios were executed with two fresh repeats; see VALIDATION.md. Browser-case minimization remains a separate future feature.

## Delivered — native WebMCP

The adapter registers, discovers and executes the actual browser API, recording capabilities and invocation counts. Chrome 154 was validated with the native testing feature enabled in a disposable profile. HTTP execution is separately labelled; requiring unavailable native support fails explicitly. See BROWSER_INTEGRATION.md.

## Next milestone — general contracts and applications

A strict loader for bounded built-in browser scenarios is delivered in `config.py`, with executable HTTP/native examples. General intent contracts, external application adapters and arbitrary locators remain future work; the richer `examples/scenarios.json` is still design-only.

Test a second owned application before making cross-application claims. Its domain semantics may require different rules for ordering, retries, money, object identity, and cancellation.

## Next milestone — automatic workflow pairing

A later system could propose mappings between visible actions and tool operations. Ambiguous mappings should remain unresolved until validated. AI may help suggest a mapping or explain a confirmed finding, but should not be the authority on whether an effect occurred.

## Product readiness beyond a portfolio prototype

An external-facing product would require reliable adapter maintenance, customer-specific fixture isolation, authentication, access controls, privacy handling, configurable retention, and clear operator permissions. The current loopback development server is not such a hosted service.

The extended architecture, proposed modules, and integration evidence requirements are preserved in [INTEGRATION_ROADMAP.md](INTEGRATION_ROADMAP.md).

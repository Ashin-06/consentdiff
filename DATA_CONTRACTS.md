# Implemented data contracts

The runtime returns JSON-compatible dictionaries defined in `consentdiff/core.py`. `examples/test-config.json` and `examples/scenarios.json` are retained `0.1-design` inputs and are not loaded by this implementation. Other curated examples contain generated validation results and evidence.

## Scenario catalogue

Each catalogue entry has `id`, `title`, `variant`, `journey`, `expected_status`, and `expected_kind`. Scenario IDs CD-001 through CD-010 are the supported catalogue.

A repaired suite changes application behavior to safe, but retains the chosen journey. Its expected result is PASS except for CD-008, whose evidence remains unavailable.

## Intent

The actual runtime intent contains:

- `actor`, `action`, `resource`, `recipient`, `role`, and the allowed `operation`.
- `confirmation_required`.
- `required_effect_count`: one for confirmed/retry journeys and zero for cancel/stale-confirmation journeys.
- `cancellation_semantics`.
- `changed_arguments_require_new_approval`.

The fixture intent is fixed to a file share. This is not a general-purpose schema interpreter for arbitrary business policies.

## Plan and approval

A staged plan records actor, action, recipient, role, resource, version, and operation. An approval copies those fields and adds `decision`, `expires_at`, and a synthetic token.

The safe controller compares the critical fields with the current plan before committing. Changing the role changes the plan version. The token and expiry are deterministic fixture values, not signed authorization credentials.

## Trace record

Each trace entry contains `step`, `action`, `plan`, `approval`, `cancelled`, the deterministic `clock`, and `response`. Responses include an action/message and whether the controller reports a commit.

The oracle checks approval against actual observed records independently of the reported commit flag. A success message without a persisted grant is not accepted as success; a false commit flag cannot hide an unapproved persisted effect.

## Observer result

The observer returns `status`, `effects`, `grants`, and `state_digest`.

- `complete`: effects and grants are authoritative observations within the fixture.
- `unavailable`: lists and digest are null, not empty.
- `partial`: the frozen setup mapping is absent/invalid, application identities drifted, or a recipient cannot be resolved against the frozen map.

Each observed effect/grant contains logical recipient, role, resource, and operation. Physical SQLite IDs are translated only through the independently frozen setup mapping; the mutable users table must still match it. Display labels are ignored. Every record and its count must match the exact intent in both persisted representations.

## Paired result

`run_pair` includes `scenario`, `mode`, `intent`, `steps`, `journeys`, `baseline_equal`, `baseline_clean`, `status`, `findings`, `parity`, `observer_complete`, `intent_satisfied`, `ignored_fields`, `required_effect_count`, `scope`, and `limitations`.

Each journey contains its driver/adapter label, identity mapping, before/after observations, trace, and responses.

Each finding includes `kind`, `journey`, `expected`, `actual`, and `evidence_ref`. Kinds include overbroad_permission, wrong_recipient, cancellation_violation, stale_confirmation, duplicate_effect, false_success, confirmation_violation, intent_violation, and path_divergence.

`parity` may be null when evidence is incomplete. Agreement alone is not a passing result. An established violation produces FAIL; otherwise incomplete evidence produces INCONCLUSIVE.

## Repeated and saved results

`run_scenario` adds `repeats` and `repeat_consistent`. The evidence layer runs a separate retained witness and adds `witness_matches`. Disagreement makes the case inconclusive.

A saved case wraps the result with `case_id`, `created_at`, `tool_version`, `config`, and artifact links. The exported databases belong to that retained witness rather than every earlier temporary repeat.

## Suite results

A suite returns `status`, `mode`, `summary`, `results`, and `interpretation`. Each row has expected_status, observed_status, expectation-match status, and finding_kinds.

The summary counts expectation matches. It does not count secure systems. A row can have status PASS while observed_status is FAIL or INCONCLUSIVE.

## Reduction results

The reducer returns original/minimized action lists and counts, a finding `signature` of kind plus journey, `one_minimal`, `evaluations`, `budget_exhausted`, candidate `history`, status, and limitations.

Evaluations count individual paired runs. A normal oracle decision uses two. Invalid deletion candidates are recorded as INVALID and do not become reproductions. One-minimality is limited to valid single-step deletions preserving the selected signature.

## Evidence files and integrity

A case stores `case.json`, `report.html`, `manifest.json`, `evidence/intent.json`, and per-path application.sqlite, before.json, after.json, and trace.json.

The manifest covers 11 content files and is not self-hashed. Verification checks required files, safe paths, file digests, and unexpected content. It is unsigned and provides integrity relative to the manifest, not authenticity.

## Design-only examples

The original example files preserve richer future contracts, named journey recipes, and proposed browser adapter configuration. Their field names and variant labels are not guaranteed to match the implemented fixed catalogue. Do not pass them to the runtime as if a scenario loader exists. Future loader work is described in [INTEGRATION_ROADMAP.md](INTEGRATION_ROADMAP.md).

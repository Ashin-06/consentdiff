# Changelog

All notable changes to this project. Versions follow [semantic versioning](https://semver.org/).

## 1.1.0 — 2026-11-03

### Added
- The workbench can run as a service: settings from `CONSENTDIFF_*` environment variables, checked
  at startup; production refuses to start without hashed API keys, and the server never binds a
  non-loopback address without keys. Keys carry roles (`analyst`, `viewer`, `monitor`, `admin`).
  The page asks for a key once per browser session and sends it with every API call and download.
- Per-client rate limit for keyed or remote clients, request IDs, JSON access logs without case
  content, `/healthz`, `/readyz` and Prometheus `/metrics` (`python -m consentdiff.ops keygen`
  makes keys). Still no third-party runtime dependencies.
- `CONSENTDIFF_ALLOWED_HOSTS` for names other than loopback; loopback is accepted on any port, so
  Docker port mapping works.
- With API keys configured, the browser automation routes are switched off: real Chrome runs stay a
  workstation feature. `browser-run` always uses its own disposable loopback server without keys,
  whatever is set in the environment.
- A container image (slim, non-root, health check), pinned development tools in
  `requirements-dev.lock`, and a CI job with ruff, bandit, pip-audit and coverage next to the
  existing Ubuntu/Windows matrix, now on Python 3.12 and 3.13.
- `SECURITY.md`, `docs/threat-model.md`, `docs/runbook.md`, MIT licence.
- The CI workflow, installation check, process cleanup (`processes.py`), browser runner and
  evidence fixes from the 11 October work, first published here.

### Changed
- Python 3.12 or newer is required (was 3.10).

### Unchanged
- Scenarios, findings, minimization and bundles; the 44 earlier tests pass (two unused test imports
  removed), and both real Chrome suites (`examples/test-config.json` and `examples/native-config.json`)
  pass 20 of 20 journeys on this version.

## 1.0.0 — 2026-10-10

First release: the reference lab, structured-tool and browser paths, workbench and CLI.

# Runbook

How to deploy and operate the workbench as a service. Commands assume the repository root.

## Deploy

```bash
docker build -t consentdiff:1.1.0 .
python -m consentdiff.ops keygen           # one key per person; repeat for each
docker run -d --name consentdiff -p 8767:8767 -v consentdiff-data:/data \
  -e CONSENTDIFF_KEYS_FILE=/run/secrets/consentdiff-keys.json \
  -e CONSENTDIFF_ALLOWED_HOSTS=lab.example.org \
  consentdiff:1.1.0
curl -fsS http://127.0.0.1:8767/readyz
```

The image has no third-party packages, runs as a non-root user and keeps cases in `/data`. It
refuses to start, and says why, without hashed API keys. Put it behind a TLS-terminating proxy and
list the proxy's public name in `CONSENTDIFF_ALLOWED_HOSTS`. The image has no Node or Chrome: real
browser runs stay on a workstation (`npm ci`, then `python -m consentdiff browser-run`).

## Configure

| Variable | Required in production | Meaning |
|---|---|---|
| `CONSENTDIFF_ENV` | — | `development` (default) or `production` |
| `CONSENTDIFF_API_KEYS` / `CONSENTDIFF_KEYS_FILE` | yes | JSON `{"sha256:<hex>": {"user": "...", "role": "..."}}`. Roles: `analyst` (run, read), `viewer` (read), `monitor` (metrics), `admin` |
| `CONSENTDIFF_HOST`, `CONSENTDIFF_PORT` | — | default `127.0.0.1:8767`; the image uses `0.0.0.0` |
| `CONSENTDIFF_ALLOWED_HOSTS` | when reached by name | comma-separated host names clients use (with or without a port) |
| `CONSENTDIFF_DATA_DIR` | — | case storage; `/data` in the image |
| `CONSENTDIFF_RATE_LIMIT` | — | requests per minute per keyed or remote client, default 120 |
| `CONSENTDIFF_LOG_LEVEL` | — | default `INFO` |

## Watch

- `GET /healthz` (process up), `GET /readyz` (data directory usable), `GET /metrics` (role
  `monitor`): `http_requests_total`, `http_request_duration_seconds`,
  `consentdiff_decisions_total{decision="case_run_seeded|case_run_repaired|suite_*|minimized"}`.
- Logs are JSON lines on stdout with a request ID; they hold no case content.

## Rotate keys

Add the new key's hash, restart, hand over the key, remove the old hash, restart.

## Back up and restore

Cases are plain folders with a SHA-256 manifest. Back up the volume; after a restore, run
`python -m consentdiff verify <case folder>` on any case you rely on.

## Incidents

1. **Leaked key.** Remove its hash and restart; review the access log for that user.
2. **A case fails `verify`.** Treat it as altered; re-run the scenario.

# entitlement-service

Deterministic capability entitlement resolution. Answers which capabilities are enabled for a tenant context based on segment, plan, country, and add-ons.

## Design

See `docs/designs/entitlement-service-design.md` (B2P02).

## Responsibilities

- Deterministic capability grant/denial from commercial policy inputs
- Add-on-aware enablement — add-ons processed in sorted lexical order, deny wins over grant
- Dependency enforcement using capability registry metadata
- Traceable output with per-capability decision reasons

## Out of scope

- Config key/value resolution (owned by `config-service`)
- Capability registry schema ownership (owned by `capability-registry`)
- Runtime feature execution (owned by domain services)

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/entitlement/resolve` | Resolve full capability map for context |
| POST | `/api/v1/entitlement/is-enabled` | Check single capability for context |
| GET | `/health` | Health check |
| GET | `/metrics` | Service metrics |

## Gateway registration

Route: `/api/v1/entitlement` → `entitlement-service`
Rate limit: `internal-control-plane`

## Running tests

```
pytest tests/
```

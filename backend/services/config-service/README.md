# config-service

Runtime configuration resolution service. Resolves effective configuration across a five-level hierarchy: `global → country → segment → plan → tenant`.

## Design

See `docs/designs/config-service-design.md` (B2P01).

## Responsibilities

- Hierarchical config resolution with deterministic override precedence
- Storage-agnostic layer provider abstraction
- Capability-aware config projection (filter resolved map by capability key)
- Runtime ephemeral override support with TTL
- Provenance metadata per resolved key

## Out of scope

- Entitlement decisions (owned by `entitlement-service`)
- Capability lifecycle management (owned by `capability-registry`)
- Business-rule computation or inline branching — see MS-CONFIG-01

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/config/resolve` | Resolve a single key |
| POST | `/api/v1/config/resolve-keys` | Resolve multiple keys |
| POST | `/api/v1/config/resolve-namespace` | Resolve all keys under a namespace prefix |
| GET | `/health` | Health check |
| GET | `/metrics` | Service metrics |

## Gateway registration

Route: `/api/v1/config` → `config-service`
Rate limit: `internal-control-plane`

## Running tests

```
pytest tests/
```

# capability-registry

Single source of truth for capability metadata and dependency relationships. Stores capability definitions, dependency graph, and versioned snapshots for deterministic downstream consumption.

## Design

See `docs/designs/capability-registry-service-design.md` (B2P05) and `docs/specs/capability-registry-service-spec.md`.

## Responsibilities

- Authoritative storage of capability records (MS-CAP-01: 6 required fields enforced)
- Dependency graph index with cycle detection and reverse-edge queries
- Pre-publish validation (schema, identity, dependency integrity, MS-CAP-01, MS-CAP-02)
- Immutable versioned snapshots with integrity digest
- Read-only integration contract for entitlement-service (`EntitlementRegistryReaderPort` — B15-022)
- Runtime capability plug-in lifecycle interface (`CapabilityModuleInterface` — B15-034)

## Out of scope

- Entitlement resolution or allow/deny decisions (owned by `entitlement-service`)
- Config value retrieval or hierarchy merging (owned by `config-service`)
- Commercial packaging or pricing authoring

## B15 fixes (2026-06-02)

- **B15-021**: `billing_type` enum corrected to spec values: `metered | included | add_on | non_monetizable`
- **B15-022**: `app/ports.py` — `EntitlementRegistryReaderPort` ABC + `InProcessEntitlementRegistryReader` concrete adapter
- **B15-034**: `app/ports.py` — `CapabilityModuleInterface` ABC with `enable()`, `disable()`, `validate_dependencies()`, `on_usage()`, `inject_config()` lifecycle methods

## API

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/capability-registry` | List all capabilities |
| GET | `/api/v1/capability-registry/{key}` | Get single capability |
| GET | `/api/v1/capability-registry/graph` | Get full dependency graph |
| GET | `/api/v1/capability-registry/snapshot/{version}` | Get snapshot metadata |
| POST | `/api/v1/capability-registry/draft` | Submit draft changes for validation |
| POST | `/api/v1/capability-registry/draft/{draftId}/publish` | Publish a validated draft |
| GET | `/health` | Health check |
| GET | `/metrics` | Service metrics |

## Gateway

Route: `/api/v1/capability-registry` → `capability-registry` | Rate limit: `internal-control-plane`

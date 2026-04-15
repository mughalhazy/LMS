# Learning Path Service Rules

## Creation workflow

1. Validate tenant context (`X-Tenant-Id` and token claim).
2. Validate owner belongs to tenant.
3. Create path with `status=draft` and `version=1`.
4. Emit `learning.path.created` event.

## Course sequencing workflow

1. Replace node/edge payload in a single transaction.
2. Validate all referenced node IDs exist in path payload.
3. Validate no cycles in directed graph.
4. Validate each non-entry required node has inbound dependency.
5. Validate elective group constraints (`min_select <= max_select`).
6. Persist and emit `learning.path.updated`.

## Publishing workflow

1. Lock path row for update.
2. Run publish validator:
   - at least one required node
   - all references active and publishable
   - DAG check passes
   - completion mode and elective requirements consistent
3. Set `status=published`, increment `version`, stamp `published_at/published_by`.
4. Write immutable record in `learning_path_audit_log` with `change_reason`.
5. Emit `learning.path.published`.

## Tenant data access policy

All repository methods require tenant-scoped keys and deny operations where:

- `tenant_id` is missing from request context
- path `tenant_id` does not match auth tenant claim
- referenced nodes/edges originate from another tenant

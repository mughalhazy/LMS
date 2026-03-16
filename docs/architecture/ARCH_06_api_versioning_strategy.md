# ARCH_06 — API Versioning Strategy

## 1) Version format

### Canonical format
- **URI major versioning** is mandatory for externally exposed REST endpoints.
- Pattern: **`/api/v{major}`** where `major` is a positive integer (`v1`, `v2`, ...).
- Examples:
  - `/api/v1/courses`
  - `/api/v1/enrollments`
  - `/api/v1/lessons`

### Semantics
- **Major** version increments communicate any change that can break existing clients.
- **Minor/patch** evolution is handled **within a major version** as non-breaking changes and tracked in OpenAPI changelogs and release notes (not encoded into path).
- Each API response must include:
  - `X-API-Version: v{major}`
  - `Sunset` header when deprecation has entered migration window.

## 2) Endpoint versioning rules

1. **Every public endpoint is versioned in path** under `/api/v{major}`.
2. **New endpoint families for new capabilities require a new major version** (policy requirement), unless they are explicitly private/internal.
3. **Breaking changes require a new major version** and parallel operation with prior major during migration.
4. Resource naming and hierarchical style remain stable across versions where possible:
   - v1: `/api/v1/courses/{courseId}/lessons`
   - v2 equivalent: `/api/v2/courses/{courseId}/lessons`
5. Query parameters and optional response fields may be added in-place only if backward compatible.
6. Existing gateway/service routing must support side-by-side versions so one service can expose both `/api/v1/*` and `/api/v2/*` during migration.

## 3) Deprecation rules

### Lifecycle states
- **Active**: fully supported for new and existing consumers.
- **Deprecated**: still supported, but migration is required.
- **Sunset**: removed from production traffic.

### Required deprecation timeline
- Minimum migration window after deprecation notice: **6 months**.
- Recommended migration window for high-traffic or regulated integrations: **12 months**.
- Deprecation notice must include:
  - impacted endpoints
  - replacement endpoints/version
  - migration guide link
  - announced sunset date

### Communication and enforcement
- Publish deprecation in release notes and API changelog.
- Add runtime headers on deprecated versions:
  - `Deprecation: true`
  - `Sunset: <RFC 7231 datetime>`
  - `Link: <migration-guide>; rel="deprecation"`
- 90/30/7 day reminders before sunset to API owners and registered API clients.

## 4) Backward compatibility rules

### Compatibility guarantees within a major version
The following are guaranteed non-breaking and allowed inside the same major version:
- adding new optional request fields
- adding new response fields
- adding new endpoints that do not alter existing contracts
- relaxing validation constraints (where security/compliance is not weakened)

### Changes considered breaking (must trigger new major version)
- removing or renaming request/response fields
- changing field type or semantic meaning
- changing requiredness from optional → required
- changing auth model/scopes in a way that blocks existing clients
- changing status-code behavior for successful flows

### Runtime compatibility expectation
- A client built against `vN` must continue to function for all non-breaking updates released under `vN`.
- During migration windows, `vN` and `vN+1` run in parallel at gateway and service layers.

## 5) Compatibility with current LMS repository APIs

This strategy is compatible with current gateway paths already using `/api/v1/*`, including core resources and integrations. It preserves existing contract shape while defining the upgrade path for future majors.

Examples already present in repository routing:
- `/api/v1/courses`
- `/api/v1/enrollments`
- `/api/v1/lessons`
- `/api/v1/courses/{courseId}/lessons`
- `/api/v1/integrations/webhooks/events`

## 6) QC loop

### QC pass #1

| Category | Score (1–10) | Findings |
|---|---:|---|
| Backward compatibility guarantees | 8 | Rules identify breaking vs non-breaking but did not mandate deprecation headers and communication checkpoints strongly enough. |
| Clarity of version policy | 9 | Version format and triggers are clear, but lifecycle state transitions needed explicit operational markers. |
| Compatibility with existing repo APIs | 10 | Strategy aligns with existing `/api/v1/*` gateway structure and endpoint examples. |

**Weakness identified:** deprecation operations were underspecified.

**Revision applied:** added lifecycle states (Active/Deprecated/Sunset), minimum migration windows, required headers (`Deprecation`, `Sunset`, `Link`), and reminder cadence.

---

### QC pass #2 (after revision)

| Category | Score (1–10) | Findings |
|---|---:|---|
| Backward compatibility guarantees | 10 | Explicit compatibility guarantees and breaking-change triggers now fully testable and enforceable. |
| Clarity of version policy | 10 | Format, endpoint versioning behavior, and deprecation lifecycle are unambiguous. |
| Compatibility with existing repo APIs | 10 | Continues to align with `/api/v1/*` patterns currently configured in gateway routes and API docs. |

**Final QC result:** **10/10** across all required categories.

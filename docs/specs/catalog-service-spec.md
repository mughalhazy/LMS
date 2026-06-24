# Catalog Service Specification

**Location:** `Repo/docs/specs/catalog-service-spec.md` | **Type:** Canonical Spec | **Created:** U7 delta remediation 2026-06-20  
**Service:** `backend/services/catalog-service` | **Port (code default):** 8094 | **Manifest port:** 8146

---

## Service Purpose

The catalog service is the platform's commerce product catalog authority. It manages the lifecycle of purchasable products (courses, bundles, plans) and their associated offers, and resolves catalog snapshots for checkout flows.

**In scope:**
- Product definition and lifecycle (draft → published → retired)
- Offer creation and retrieval per product
- Tenant-specific catalog configuration overrides
- Catalog snapshot resolution for downstream checkout/entitlement flows

**Out of scope:**
- Payment processing (payment-service)
- Invoice and billing logic (invoice-billing-service)
- Subscription lifecycle (subscription-service)
- Entitlement enforcement (entitlement-service)

---

## Auth Exception

**Auth mechanism: HS256 shared-secret** (uses `JWT_SHARED_SECRET` env var). This service deviates from the platform-wide RS256 JWT standard (FA-004a). Routes `/health` and `/metrics` are exempt from auth entirely.

**Impact:** External-facing catalog routes must route through an RS256-validating gateway layer. Tracked for remediation to RS256 in line with FA-004a.

---

## Runtime

- **Implementation:** Python `http.server.BaseHTTPRequestHandler` (not FastAPI)
- **Port:** 8094 (code default); 8146 (manifest assignment)
- **Header:** `X-Tenant-Id` required on all authenticated routes; `X-API-Version: v1` returned in all responses (CAT-004)

---

## API Endpoints

Base path: `/api/v1/catalog`

### Product endpoints

| Method | Path | Response | Description |
|---|---|---|---|
| `GET` | `/api/v1/catalog/products` | 200 | List products. Query params: `status`, `segment`. Scoped to `X-Tenant-Id`. |
| `GET` | `/api/v1/catalog/products/{product_id}` | 200 | Get product by ID. Tenant-scoped. |
| `POST` | `/api/v1/catalog/products` | 201 | Create product. Body: product definition with `tenant_id`. |
| `PATCH` | `/api/v1/catalog/products/{product_id}` | 200 | Update product metadata. Tenant-scoped. |
| `POST` | `/api/v1/catalog/products/{product_id}/publish` | 200 | Publish product (draft → published). |
| `POST` | `/api/v1/catalog/products/{product_id}/retire` | 200 | Retire published product (published → retired). |

### Offer endpoints

| Method | Path | Response | Description |
|---|---|---|---|
| `GET` | `/api/v1/catalog/offers/{offer_id}` | 200 | Get offer by ID. |
| `POST` | `/api/v1/catalog/products/{product_id}/offers` | 201 | Create offer for a product. Body: offer definition with pricing details. |

### Utility endpoints

| Method | Path | Response | Description |
|---|---|---|---|
| `POST` | `/api/v1/catalog/resolve-snapshot` | 200 | Resolve catalog snapshot for a list of `product_ids`. Returns point-in-time product/offer state for checkout flows. |
| `POST` | `/api/v1/catalog/tenants/{tenant_id}/config` | 200 | Update tenant-specific catalog configuration (pricing overrides, visibility rules). |

### Infrastructure endpoints (auth-exempt)

| Method | Path | Response | Description |
|---|---|---|---|
| `GET` | `/health` | 200 | Liveness check: `{"status": "ok", "service": "catalog-service"}` |
| `GET` | `/metrics` | 200 | Observability: `{"service": "catalog-service", "service_up": 1}` |

---

## Error Responses

| Code | Meaning |
|---|---|
| 401 | Missing or invalid JWT (HS256 validation failed) |
| 400 | Malformed JSON body or missing required fields |
| 404 | Product, offer, or tenant config not found |
| 500 | Unexpected service error |

---

## See also

- `docs/designs/checkout-service-design.md` — checkout flow consuming catalog snapshots
- `docs/designs/payment-service-design.md` — payment flows
- `docs/governance/doc-catalogue.md` — full doc index

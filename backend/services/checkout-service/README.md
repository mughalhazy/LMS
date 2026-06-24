# checkout-service

Converts purchase intent into committed orders and initiates payment. Stateless, idempotency-keyed. Design: `docs/designs/checkout-service-design.md` (B3P03).

## Gateway
Route: `/api/v1/checkout` | Rate limit: `public-api-standard`

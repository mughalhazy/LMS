# Payment Service

Pakistan payment orchestration service — routes payments through local payment providers.

## Design reference

`Repo/docs/designs/checkout-service-design.md` | `Repo/docs/designs/invoice-billing-service-design.md`

## Providers

- **JazzCash** — primary mobile money provider
- **Easypaisa** — secondary mobile money provider

Routing is handled by `build_pakistan_payment_router()` in `service.py`. Provider selection is based on tenant country code and payment method preference.

## Key classes

- `PaymentOrchestrationService` — top-level coordinator
- `PaymentCallbackRequest` / `PaymentCallbackResponse` — API models in `api.py`

## Status

Service exists on disk with full implementation. Not yet registered in the API gateway (pending).

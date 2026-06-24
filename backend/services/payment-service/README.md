# Payment Service

Pakistan payment orchestration service — routes payments through local payment providers.

## Design reference

`Repo/docs/designs/checkout-service-design.md` | `Repo/docs/designs/invoice-billing-service-design.md`

## Providers

- **JazzCash** — primary mobile money provider
- **Easypaisa** — secondary mobile money provider

Routing is handled by `build_pakistan_payment_router()` in `service.py`. Provider selection is based on tenant country code and payment method preference.

## API

- `POST /api/v1/payments/initiate` — initiate a payment; body: `{order_id, user_id, amount, currency, payment_method, tenant_id}`; returns `{payment_id, provider, redirect_url, status}`
- `POST /api/v1/payments/callback/{provider}` — inbound payment callback from JazzCash / Easypaisa

## Key classes

- `PaymentOrchestrationService` — top-level coordinator (`integrations/payments.py`)
- `PakistanPaymentRouter` — resolves `payment_method` to `jazzcash` | `easypaisa`
- `PaymentCallbackRequest` / `PaymentCallbackResponse` — callback API models
- `PaymentInitiateRequest` / `PaymentInitiateResponse` — initiation API models

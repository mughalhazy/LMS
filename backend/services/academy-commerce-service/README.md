# academy-commerce-service

Academy commerce extensions — enrollment offer composition, student payment orchestration, regional pricing context, and promotion scenario management. Implements `docs/designs/academy-commerce-extensions.md`. Created B15-010 (2026-06-02).

## Components

| Class | Purpose |
|---|---|
| `EnrollmentOfferComposer` | Composes enrollment offers: pricing context + promotions + installment plans |
| `StudentPaymentOrchestrationExtension` | Orchestrates payment reference submission → enrollment activation |
| `EnrollmentBasedPricingContextAdapter` | Resolves regional policy packs (PKR/USD/GBP, tax, installment rules) per country code |
| `PromotionScenarioRegistry` | Manages promotion scenarios: early_bird, group, scholarship, referral |

## API

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/academy-commerce/offers` | Compose enrollment offer (pricing + promo + installments) |
| GET | `/api/v1/academy-commerce/offers/{offer_id}` | Get composed offer |
| POST | `/api/v1/academy-commerce/promotions/{scenario_id}` | Register promotion scenario |
| GET | `/api/v1/academy-commerce/promotions` | List active promotions |
| POST | `/api/v1/academy-commerce/payment-references` | Submit student payment reference |
| POST | `/api/v1/academy-commerce/payment-references/{id}/verify` | Verify reference and emit enrollment activation event |
| GET | `/health` | Health check |
| GET | `/metrics` | Service metrics |

## Events emitted

- `academy.payment.reference.submitted` — on payment reference submission
- `academy.offer.composed` — on payment verification; signals enrollment-service to activate enrollment

## Regional policy packs

| Country | Currency | Tax | Installments |
|---|---|---|---|
| PK | PKR | 0% | up to 3 |
| US | USD | 8.5% | no |
| GB | GBP | 20% | up to 2 |

## Design reference

`docs/designs/academy-commerce-extensions.md`

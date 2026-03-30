# B3P02 — Catalog Service Design

## 1) Purpose

The Catalog Service defines and publishes **sellable products** for commerce without owning checkout, billing, or payment execution concerns. It provides a tenant-configurable product model that can be reused across B2C, B2B, enterprise, and partner segments.

This service answers:

- What can be sold? (`course product`, `bundle`, `subscription product`)
- Under which offer/pricing models can it be sold?
- Which discounts/coupons can be applied at product/offer scope?
- Which tenant-specific rules control visibility and availability?

---

## 2) Scope and non-scope

## 2.1 In scope (product-focused only)

- Sellable product definitions for:
  - course products
  - bundles
  - subscriptions
- Commercial packaging metadata (SKU, offer, sellability windows, target segments)
- Product-to-pricing linkage via references to pricing models
- Product-level discount and coupon applicability policies
- Tenant-level catalog configuration and publishing controls
- Catalog read APIs for commerce domain consumers

## 2.2 Out of scope (strict boundary)

- Checkout sessions, carts, order creation, order state
- Payment authorization, capture, refunds, payment-provider integrations
- Invoice generation, tax calculation execution, recurring billing cycles
- Course authoring, course structure/content duplication, or learner progress

The service stores only `course_ref` pointers to course domain entities and never copies course syllabus/content records.

---

## 3) Position in commerce domain

```text
Course Service (source of course truth)
          |
          | course_ref validation only
          v
+-----------------------+          +-----------------------+
|    Catalog Service    |<-------->|   Pricing Service     |
| (products and offers) | price    | (pricing logic engine)|
+-----------+-----------+ model    +-----------+-----------+
            |                                    |
            | publish catalog + offer snapshot   | quote/rate
            v                                    v
      Commerce APIs (checkout/order/subscription/invoice consumers)
```

Boundary rule:

- Catalog Service owns **product identity and offer composition**.
- Pricing Service owns **price calculation logic**.
- Checkout/Billing services consume published artifacts and do not mutate catalog definitions.

---

## 4) Service capabilities

1. **Product lifecycle**
   - Draft → Review → Published → Retired
   - Versioned publishing with immutable snapshots for downstream commercial flows

2. **Offer management**
   - Attach one or more pricing models to a product
   - Define default offer and channel/segment-specific offers

3. **Discount and coupon policy linking**
   - Mark product/offer eligibility constraints
   - Reference discount policies and coupon campaigns managed by pricing/promotion subsystem

4. **Tenant configurability**
   - Tenant-specific catalog overlays (visibility, purchasability, localization labels, segment gating)
   - Per-tenant activation windows and policy toggles

5. **Catalog discovery for commerce**
   - Query sellable products by tenant/segment/channel/region
   - Resolve active product + offer bundle into a stable snapshot for commercial transactions

---

## 5) Product model (canonical)

## 5.1 Core entities

### `Product`

Represents a sellable commercial entity.

- `product_id` (UUID)
- `tenant_id` (UUID)
- `product_type` (`COURSE`, `BUNDLE`, `SUBSCRIPTION`)
- `sku` (unique per tenant)
- `status` (`DRAFT`, `PUBLISHED`, `RETIRED`)
- `display_name` / `description` (localized)
- `sellable_from` / `sellable_until`
- `channel_targets` (web, mobile, partner, sales-assisted)
- `segment_targets` (consumer, team, enterprise)
- `offer_ids[]`
- `version`

### `CourseProductDetails`

Type extension for `COURSE` products.

- `course_ref` (foreign reference to Course Service)
- `access_mode` (`LIFETIME`, `TERM_LIMITED`, `COHORT_WINDOW`)
- `access_duration_days` (nullable)

### `BundleProductDetails`

Type extension for `BUNDLE` products.

- `bundle_strategy` (`FIXED_SET`, `CHOICE_SET`)
- `bundle_items[]`
  - `item_type` (`COURSE_REF`, `PRODUCT_REF`)
  - `item_ref`
  - `quantity`
  - `selection_rules` (for choice bundles)

### `SubscriptionProductDetails`

Type extension for `SUBSCRIPTION` products.

- `entitlement_scope` (`CATALOG_SET`, `TAG_SET`, `NAMED_PRODUCTS`)
- `included_refs[]`
- `renewal_behavior` (`AUTO_RENEW`, `EXPIRE`)
- `plan_group` (for upgrade/downgrade compatibility)

### `Offer`

Represents commercial sell option attached to a product.

- `offer_id` (UUID)
- `product_id`
- `offer_code`
- `pricing_model_refs[]` (one or many)
- `default_pricing_model_ref`
- `discount_policy_refs[]`
- `coupon_policy_ref`
- `constraints`
  - `region_allowlist`
  - `currency_allowlist`
  - `min_seats` / `max_seats`
  - `new_customer_only`
- `effective_from` / `effective_until`

### `PricingModelRef`

Catalog-owned pointer to pricing logic definition (not calculation logic).

- `pricing_model_id`
- `pricing_type` (`ONE_TIME`, `RECURRING`, `USAGE_BASED`, `TIERED`, `SEAT_BASED`, `HYBRID`)
- `price_book_id`
- `billing_period_hint` (nullable)

### `TenantCatalogConfig`

Tenant-level switches for catalog behavior.

- `tenant_id`
- `default_currency`
- `supported_currencies[]`
- `segment_policy`
- `channel_policy`
- `coupon_stackability_mode` (`NONE`, `LIMITED`, `CONFIGURED`)
- `publish_approval_required` (bool)
- `regional_compliance_tags[]`

---

## 5.2 Relationship rules

- A `Product` has one `product_type` and one corresponding details extension.
- A `Product` has one-to-many `Offer` records.
- An `Offer` has one-to-many `PricingModelRef` records to support multiple pricing types per product.
- Discounts and coupons are linked at `Offer` scope to preserve separation between product identity and pricing logic.
- `CourseProductDetails.course_ref` must reference an existing course in Course Service and remains a pointer only.

---

## 6) Pricing separation contract

To keep pricing logic cleanly separated:

- Catalog stores **pricing references and eligibility metadata only**.
- Pricing service executes all arithmetic, discount evaluation, coupon validation, rounding, and tax-rating decisions.
- Catalog never calculates totals or proration.
- Any quote returned to checkout/order flows is generated by pricing service using catalog snapshot IDs.

Contract interface (logical):

- Catalog → Pricing input: `catalog_snapshot_id`, `offer_id`, `pricing_model_id`, eligibility metadata
- Pricing → Catalog feedback: model validity status and compatibility diagnostics (non-financial)

---

## 7) APIs (logical)

## 7.1 Write APIs (internal/admin)

- `POST /catalog/products`
- `PATCH /catalog/products/{productId}`
- `POST /catalog/products/{productId}/offers`
- `PATCH /catalog/offers/{offerId}`
- `POST /catalog/products/{productId}/publish`
- `PATCH /catalog/tenants/{tenantId}/config`

## 7.2 Read APIs (commerce consumers)

- `GET /catalog/products/{productId}`
- `GET /catalog/products?tenantId=&segment=&channel=&status=PUBLISHED`
- `GET /catalog/offers/{offerId}`
- `POST /catalog/resolve-snapshot` (returns immutable product+offer snapshot reference)

---

## 8) Events

Published by Catalog Service:

- `catalog.product.created`
- `catalog.product.published`
- `catalog.product.retired`
- `catalog.offer.updated`
- `catalog.snapshot.created`
- `catalog.tenant_config.updated`

Consumed by Catalog Service:

- `course.published` / `course.retired` (to validate/flag `course_ref` availability)
- `pricing.model.retired` (to invalidate stale pricing references)

No checkout, order, invoice, or payment events are owned by this service.

---

## 9) Multi-tenant configurability model

Tenant override precedence:

1. Global default catalog policy
2. Segment-level tenant policy
3. Tenant explicit override
4. Time-bound campaign override (if enabled)

Configurable dimensions per tenant:

- Supported product types
- Allowed pricing types per segment/channel
- Coupon policy profile
- Publish workflow strictness
- Regional sellability policies

This allows the same service to be reused across segments without forked implementations.

---

## 10) QC compliance mapping

- **No overlap with checkout or billing**: checkout/order/payment/invoice flows are explicitly out of scope; catalog provides product and offer definitions only.
- **No duplication of course data**: only `course_ref` pointers are stored; course content remains in Course Service.
- **Product-focused only**: entities center on products, offers, bundle composition, and tenant catalog controls.
- **Clean separation of pricing logic**: pricing computations remain in Pricing Service; catalog keeps references and eligibility metadata.
- **Reusable across segments**: segment/channel targeting and tenant override model support consumer, enterprise, and partner motions.


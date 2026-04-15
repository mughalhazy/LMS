# Free Tier Operational Definition

**Type:** Specification | **Date:** 2026-04-14 | **MS§:** §5.5 (Commerce), §2 (Entitlement)
**Gap:** MO-016 | **Contract:** BC-FREE-01
**Source authority:** `LMS_Pakistan_Market_Research_MASTER.md` §9 (pricing), `LMS_Platform_Master_Behavioral_Spec.md` §7.5
**Status:** SPEC COMPLETE — implementation in `DOC_07_billing_and_usage_model.md` and `entitlement-service`

---

## Purpose

This document formally defines what the free tier **must include** and what it must **not restrict**. It implements the behavioral contract BC-FREE-01 (Free Entry Delivers a Complete Operational Flow) as a concrete spec that the entitlement service, commerce service, and onboarding service can reference.

---

## The Problem with Typical Free Tiers

Most SaaS free tiers are designed as restricted demos — limited to 3 students, no payment collection, no automations — forcing users to upgrade before they can run a real institution. In the Pakistan market, this approach fails because:

1. Operators have **low willingness to pay upfront** — they upgrade only after clear value
2. The **first-use experience must deliver meaningful operational value** before any upgrade prompt
3. **Payment collection is a core need, not a premium feature** — any tier that blocks it is unusable for the primary use case

---

## Free Tier Definition

### What the Free Tier MUST Enable

| Capability | Free Tier Limit | Why Included |
|---|---|---|
| Student enrollment and attendance tracking | Up to 50 students | Core daily operation |
| Course content delivery (video, docs) | Up to 10 content items | Core learning delivery |
| Basic fee reminders (manual trigger) | Up to 50 reminders/month | Core revenue operation |
| Payment collection (JazzCash, EasyPaisa) | Unlimited transactions | Market requirement — blocking this makes the product unusable |
| Daily Action List (basic) | Full access | Core operational visibility |
| WhatsApp-based interaction (basic) | Up to 100 messages/month | Market requirement — WhatsApp is the primary channel |
| Single branch / single batch | 1 branch, 3 batches | Sufficient for solo operators |
| Basic progress tracking (per student) | Full access | Core learner management |

### What Requires an Upgrade

Free tier limits are defined by **capability scope depth** — not by disabling core operations.

| Capability | Free Limit | Upgrade Unlocks |
|---|---|---|
| Students | 50 | 500 / 5,000 / unlimited per plan |
| Batches | 3 | 20 / unlimited |
| WhatsApp messages | 100/month | 1,000 / unlimited |
| Auto-reminders (scheduled, rule-based) | Manual trigger only | Automated rule-based reminders |
| Multi-branch management | Single branch | 5 branches / unlimited |
| Analytics (advanced cohort, trend, risk) | Basic daily summary | Full analytics dashboard |
| AI assist capabilities | Disabled | Enabled on paid plans |
| Certificate generation | Disabled | Enabled on paid plans |
| Compliance reporting | Disabled | Enabled on paid plans |
| LTI / HRIS / SSO integrations | Disabled | Enabled on enterprise plan |

---

## What the Free Tier MUST NOT Restrict

Per BC-FREE-01:

| Action | Restriction Status |
|---|---|
| Payment collection via local methods | NEVER restricted |
| Enrollment of students within limit | NEVER restricted |
| Sending fee reminders (manual) | NEVER restricted |
| Viewing attendance | NEVER restricted |
| Basic Daily Action List | NEVER restricted |
| WhatsApp interaction (within monthly limit) | NEVER restricted |
| Content delivery to enrolled students | NEVER restricted |

---

## Free-to-Paid Upgrade Path

**Upgrade trigger:** The system must prompt an upgrade **contextually** when a usage limit is approached — not when the user first logs in, and not via an intrusive banner.

**Upgrade prompt rule (BC-SIMPLE-01 + contextual upsell from BOS §8.2):**
- "You've enrolled 48 of 50 students. Upgrade to grow your student base." — shown at enrollment #48
- "You've used 90 of 100 monthly WhatsApp messages. Upgrade to remove the limit." — shown at 90 messages
- "Auto-reminders can recover overdue fees automatically. Upgrade to enable." — shown when operator manually sends 3+ reminders

**What this prohibits:**
- Upgrade prompts on login or landing page (intrusive)
- Upgrade prompts with no connection to the current action (irrelevant)
- Upgrade prompts that use technical capability key names (BC-LANG-01 violation)

---

## Entitlement Service Implementation

The entitlement service enforces free tier limits through:

1. **Plan type:** `plan_type = "free"` activates this bundle
2. **Capability registry:** Each capability has `plan_availability: ["free", "starter", "pro", "enterprise"]` — free capabilities are available in all plans
3. **Usage quotas:** `usage_quota` fields on Capability model enforce student count, batch count, message counts
4. **Quota events:** When a quota is approached (≥80% used), the entitlement service emits an `entitlement.quota_warning` event — the commerce service converts this to a contextual upsell notification

---

## Onboarding Integration

**BC-SIMPLE-01** and **BC-FREE-01** require that a new free-tier operator completes a meaningful workflow **within their first session without setup friction.**

The first session must deliver at minimum:
1. One batch created (pre-filled name, start date inferred)
2. One student enrolled
3. One Daily Action List rendered (may be empty but must be visible)
4. One automated action experienced (welcome message sent to student)

The onboarding service (`services/onboarding/`) manages this first-session flow and must respect the free tier capability bundle throughout.

---

## References

- `docs/specs/platform_behavioral_contract.md` — BC-FREE-01
- `docs/specs/DOC_07_billing_and_usage_model.md` — billing model and tier definitions
- `services/entitlement-service/` — quota enforcement
- `services/commerce/` — plan management
- `services/onboarding/` — first-session flow
- `LMS_Pakistan_Market_Research_MASTER.md` §9 (pricing expectations), §7 (customer behavior)

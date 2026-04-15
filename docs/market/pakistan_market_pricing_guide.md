# Pakistan Market Pricing Guide

**Type:** Market Reference | **Date:** 2026-04-14
**Gap:** MO-018 | **Folder:** `docs/market/` (new)
**Source authority:** `LMS_Pakistan_Market_Research_MASTER.md` §9, §6, §3 (segment analysis)
**Rule:** This document informs pricing model design and plan tier definitions. It is a reference — actual plan pricing is defined in `DOC_07_billing_and_usage_model.md`.

---

## Purpose

This document captures Pakistan-specific pricing intelligence for the LMS platform. It informs:
- Free tier limits (how much value to deliver before asking for payment)
- Plan tier pricing bands (PKR values per segment)
- Payment method preferences (which adapters must be supported per tier)
- Psychological pricing thresholds (where resistance begins)
- Monetization model preferences (freemium vs transaction cut vs flat fee)

---

## Core Market Reality on Pricing

| Insight | Implication |
|---|---|
| Low willingness to pay upfront | Free tier must deliver real operational value |
| Upgrade only after clear demonstrated value | Upsell must be contextual (BC-FREE-01, BOS §8.2) |
| Value is measured in ROI, not features | Business impact language required (BC-LANG-01) |
| PKR pricing, not USD pricing | All plan prices must be displayed in PKR |
| JazzCash / EasyPaisa preferred | Local payment methods are non-negotiable for sub-enterprise |

---

## Segment-Wise Pricing Expectations

### Tuition Centers & Small Academies

| Model | Range | Notes |
|---|---|---|
| Per-student SaaS fee | 500–1,500 PKR per student per year | Acceptable for up to ~50 students |
| Transaction cut | 10–20% of course fee collected | Preferred for variable revenue operators |
| Monthly flat fee | 2,000–5,000 PKR/month | Acceptable if ROI is clearly demonstrated |

**Psychological threshold:** Any model requiring upfront payment >2,000 PKR/month without demonstrated ROI sees high resistance.

**Preferred model:** Freemium → pay per student or pay per transaction. Never flat fee without a free period.

### Large Academies & Coaching Networks

| Model | Range | Notes |
|---|---|---|
| Annual flat fee per branch | 50,000–200,000 PKR/branch/year | Depending on student count tier |
| Per-student annual fee | 200–500 PKR/student | Scaled model, preferred for 1,000+ students |
| Enterprise negotiated | Custom | For 50,000+ student networks; custom contracts |

**Notes:** Large academies have experienced custom software costs in the millions. 50,000–200,000 PKR/year is a significant reduction they will respond to.

### Private Schools (Low-Cost)

| Model | Range | Notes |
|---|---|---|
| Annual per-branch fee | 30,000–80,000 PKR/year | Flat fee preferred |
| Per-student annual | 300–600 PKR/student/year | Alternative |

**Notes:** Low-cost schools are price-sensitive. Parent communication and attendance are the key selling points, not learning features.

### Private Schools (Premium)

| Model | Range | Notes |
|---|---|---|
| Annual per-branch fee | 200,000–500,000 PKR/year | Includes ERP integration, advanced reporting |
| Enterprise custom | Custom | For Beaconhouse/City School scale |

### Universities

| Model | Range | Notes |
|---|---|---|
| Annual per-institution | 1,000,000–5,000,000 PKR/year | Replaces Moodle hosting + maintenance |
| Per-department modules | Custom | For partial adoption starting with one faculty |

**Notes:** Moodle replacement is a major opportunity. Positioning as "lower TCO than Moodle" resonates — Moodle requires server maintenance, upgrades, IT staff.

### SMEs / Corporates

| Model | Range | Notes |
|---|---|---|
| Per-user per-month | Equivalent of 2–5 USD/user/month, billed in PKR | Benchmarked against global tools |
| Annual flat per company | Negotiated | Preferred for predictable budgets |

**Notes:** Corporate buyers benchmark against TalentLMS (USD pricing). A local PKR alternative at equivalent USD value wins on currency stability alone.

---

## Psychological Pricing Thresholds

| Threshold | Observation |
|---|---|
| Above 2,000 PKR/month for individual courses | High resistance unless high-stakes (MDCAT, CSS, CSS exam prep) |
| Above 5,000 PKR/month for small academy operators | Requires clear ROI demonstration before commitment |
| Above 50,000 PKR/year for school operators | Requires management-level decision, longer sales cycle |
| Free tier with any payment collection restriction | Immediate disqualification — operators will not use a "demo" |

---

## Payment Method Requirements by Segment

| Segment | Required Methods | Notes |
|---|---|---|
| Tuition Centers / Small Academies | JazzCash, EasyPaisa, Raast | Cash/bank transfer screenshots still common — platform must offer these as alternatives too |
| Large Academies | JazzCash, EasyPaisa, Bank Transfer, Credit Card | Corporate accounts may prefer bank transfer |
| Schools | Bank Transfer, Cheque, JazzCash | School fee collection often involves parent-paid bank transfers |
| SMEs / Corporates | Bank Transfer, Credit Card | Corporate procurement processes require invoicing |
| Universities | Bank Transfer, Procurement Order | Government universities require purchase order flows |

**Note:** BC-PAY-01 requires that payment confirmation → instant access for all digital payment methods. Bank transfer / cheque flows may still require manual confirmation but must have a clear operator flow.

---

## Monetization Model Comparison

| Model | Market Fit | Risk |
|---|---|---|
| Freemium + capability upgrade | High — matches low upfront willingness | Risk: over-generous free tier leaves no upgrade incentive |
| Per-student SaaS | High for small operators | Risk: complex billing for operators with fluctuating student counts |
| Transaction cut | High for course sellers | Risk: operator friction on high-volume fee collection |
| Flat annual fee | Medium — predictable for both sides | Risk: requires value demonstration before commitment |
| Usage-based (API/storage) | Low for core ops — acceptable for enterprise add-ons | Risk: unpredictable bills create anxiety |

**Recommended:** Freemium → flat monthly/annual per capability tier + transaction fee on payment collection (optional, operator can disable by upgrading to higher tier).

---

## References

- `LMS_Pakistan_Market_Research_MASTER.md` §9 (pricing expectations), §6 (pricing analysis), §3 (segment analysis)
- `docs/specs/DOC_07_billing_and_usage_model.md` — actual plan definitions
- `docs/specs/free_tier_operational_definition.md` — free tier spec
- `docs/specs/platform_behavioral_contract.md` — BC-PAY-01, BC-FREE-01, BC-LANG-01

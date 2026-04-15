# Domain Capability Extension Model

**Type:** Architecture design | **Date:** 2026-04-04 | **MS§:** §5.19

---

## Purpose

Define how use-case-specific capability domains (B5P* batch docs) fit within the global capability platform model without becoming segment-forked products.

---

## The Pattern

The platform supports **domain capability extensions** — pre-designed groups of capabilities optimised for a specific market use-case profile. These extensions:

- Add new capabilities on top of the core platform
- Do NOT fork the core platform
- Are accessed via the standard entitlement system
- Are selected using `segment_type` + `plan_type` as entitlement inputs
- Can be enabled/disabled per tenant without code changes

---

## Defined Domain Extensions

| Extension | Batch doc | Use-case profile | Key capabilities added |
|---|---|---|---|
| Academy Operations | `B5P01` | `segment_type: academy` | Batch/class ops, attendance, fee tracking, branch management |
| School Engagement | `B5P02` | `segment_type: school` | Grading publication, parent portal, teacher-parent comms |
| Workforce Training | `B5P03` | `segment_type: corporate` or `sme` | Compliance training, onboarding flows, manager oversight |
| University Operations | `B5P04` | `segment_type: university` | Faculty workflows, advanced assessment, research tracking |

---

## How Extension Capabilities Are Enabled

```
Tenant registers with segment_type = "academy"
           ↓
Entitlement resolver reads segment_type from tenant context
           ↓
Policy store returns capability grants for academy profile
           ↓
Academy operations capabilities are enabled (e.g. CAP-BATCH-OPS, CAP-ATTENDANCE)
           ↓
Core platform capabilities remain available to all tenants unchanged
```

---

## Rules

1. Domain extensions NEVER modify core service logic
2. Domain extensions add new service modules that integrate via the event bus and stable APIs
3. All extension capabilities must have a capability_key in the registry
4. Extension capabilities must be independently disableable
5. No extension may duplicate data ownership from a core domain

---

## What This Is NOT

- NOT a segment-specific product fork
- NOT a separate codebase branch
- NOT a hardcoded `if segment == 'school'` condition in any service
- NOT a separate deployment

---

## References

- Master Spec §5.19
- `docs/architecture/B2P05_capability_registry_service_design.md`
- `docs/architecture/B2P02_entitlement_service_design.md`
- `docs/architecture/B5P01`–`B5P04` (the extension domain designs)

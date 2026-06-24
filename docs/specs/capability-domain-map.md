# B0P09 — Full Capability Domain Map

**Type:** Specification | **Date:** 2026-04-04 | **MS§:** §5 (all 18 domains)

---

## Purpose

Authoritative cross-reference mapping all 18 Master Spec §5 capability domains to their service owners, spec/design docs, and current implementation status.

**Status codes:** `BUILT` = service + spec exist | `PARTIAL` = code exists, spec incomplete | `SPEC-ONLY` = spec exists, no service | `PLANNED` = neither service nor spec built

---

## Capability Domain Status Map

| # | MS§ | Domain | Status | Owner service(s) | Design doc(s) | Spec doc(s) |
|---|---|---|---|---|---|---|
| 1 | §5.1 | Learning Capabilities | BUILT | `course-service`, `lesson-service`, `services/exam-engine/` | `ARCH_01`, `B0P04` | `SPEC_09`, `lesson-service-spec.md`, `content-service-spec.md`, `scorm-runtime-spec.md`, `exam-engine-spec.md` |
| 2 | §5.2 | Student Lifecycle Capabilities | BUILT | `enrollment-service`, `progress-service`, `services/system-of-record/` | `ARCH_01`, `SOR_01` | `SPEC_11`, `SPEC_12`, `progress-tracking-spec.md` |
| 3 | §5.3 | Financial Capabilities | PARTIAL | `services/system-of-record/`, `services/commerce/billing.py` | `SOR_01`, `B3P04` | `financial-ledger-spec.md` |
| 4 | §5.4 | Commerce Capabilities | BUILT | `services/commerce/`, `services/subscription-service/` | `B3P01`–`B3P07` | `DOC_07` |
| 5 | §5.5 | Monetization Capabilities | BUILT | `services/commerce/monetization.py`, `services/capability-registry/` | `B2P04`, `B2P05` | `DOC_07`, `capability-registry-service-spec.md` |
| 6 | §5.6 | Operations Capabilities | BUILT | `services/academy-ops/` | `B5P01`–`B5P04` | `SPEC_07`, `org-hierarchy-spec.md` |
| 7 | §5.7 | Communication Capabilities | PARTIAL | `services/notification-service/` | `B2P08` | `notification-service-spec.md` |
| 8 | §5.8 | Workflow Capabilities | PARTIAL | `services/workflow-engine/` | `ARCH_05`, `event-bus-design.md` | `workflow-engine-spec.md` |
| 9 | §5.9 | Interaction Layer Capabilities | PLANNED | None built | None | `interaction-layer-spec.md` (placeholder) |
| 10 | §5.10 | Admin Operations Capabilities | PARTIAL | `services/operations-os/` | `B5P01` | `operations-os-spec.md` |
| 11 | §5.11 | Content Protection Capabilities | PARTIAL→BUILT | `services/media-security/`, `services/file-storage/` (NEW), `services/media-pipeline/` (NEW) | `media-security-interface-contract.md`, `content-storage-model.md`, `storage-adapter-interface-contract.md` | `media-security-spec.md`, `media-pipeline-spec.md` |
| 12 | §5.12 | Offline Capabilities | PARTIAL | `services/offline-sync/` | `offline-sync-interface-contract.md` | `offline-sync-spec.md` |
| 13 | §5.13 | Performance Capabilities | PARTIAL | Cross-cutting (gateway, event-bus, tenant isolation) | `scalability-strategy.md`, `ARCH_07` | `performance-capabilities-spec.md` |
| 14 | §5.14 | Economic Capabilities (User Level) | PARTIAL | `services/commerce/owner_economics.py` | `owner-economics-service-design.md` | `economic-capabilities-user-spec.md` |
| 15 | §5.15 | Economic Capabilities (System Level) | PARTIAL | `services/analytics-service/`, `services/commerce/` | `B3P06` | `system-economics-spec.md` |
| 16 | §5.16 | Data & Analytics Capabilities | BUILT | `services/analytics-service/` | `B6P01`–`B6P05` | `AI_01`–`AI_05`, `learning-analytics-spec.md`, `reporting-spec.md`, `analytics-service-spec.md` |
| 17 | §5.17 | Onboarding Capabilities | PARTIAL | `services/onboarding/` | — | `onboarding-spec.md` |
| 18 | §5.18 | Enterprise Capabilities | BUILT | `services/enterprise-control/` | `B2P07`, `security-architecture.md` | `SPEC_01`, `SPEC_03`, `sso-spec.md`, `compliance-reporting-spec.md`, `enterprise-control-spec.md` |

---

## Summary

| Status | Count | Domains |
|---|---|---|
| BUILT | 5 | §5.1, §5.2, §5.4, §5.5, §5.18 |
| PARTIAL (code + spec now added) | 12 | §5.3, §5.6, §5.7, §5.8, §5.10, §5.11, §5.12, §5.13, §5.14, §5.15, §5.16, §5.17 |
| PLANNED (no code or service) | 1 | §5.9 Interaction Layer |

---

## Gap Action (Post-Normalisation)

- §5.9: Requires a new service build — see `docs/specs/interaction-layer-spec.md` and Drift Flag DF-03
- §5.6 partial domains (B5P02, B5P03, B5P04): Services for school engagement, workforce, and university are partially built — need dedicated service layer beyond `academy-ops`

---

## References

- Master Spec §5 (all capability domains)
- `docs/governance/doc-catalogue.md` (full doc index with service mapping)
- `docs/specs/B0P04_core_capabilities.json` (core 7 capabilities — superseded in scope by this doc)

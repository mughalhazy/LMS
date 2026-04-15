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
| 1 | §5.1 | Learning Capabilities | BUILT | `course-service`, `lesson-service`, `services/exam-engine/` | `ARCH_01`, `B0P04` | `SPEC_09`, `lesson_service_spec.md`, `content_service_spec.md`, `scorm_runtime_spec.md`, `exam_engine_spec.md` |
| 2 | §5.2 | Student Lifecycle Capabilities | BUILT | `enrollment-service`, `progress-service`, `services/system-of-record/` | `ARCH_01`, `SOR_01` | `SPEC_11`, `SPEC_12`, `progress_tracking_spec.md` |
| 3 | §5.3 | Financial Capabilities | PARTIAL | `services/system-of-record/`, `services/commerce/billing.py` | `SOR_01`, `B3P04` | `financial_ledger_spec.md` |
| 4 | §5.4 | Commerce Capabilities | BUILT | `services/commerce/`, `services/subscription-service/` | `B3P01`–`B3P07` | `DOC_07` |
| 5 | §5.5 | Monetization Capabilities | BUILT | `services/commerce/monetization.py`, `services/capability-registry/` | `B2P04`, `B2P05` | `DOC_07`, `capability_registry_service_spec.md` |
| 6 | §5.6 | Operations Capabilities | BUILT | `services/academy-ops/` | `B5P01`–`B5P04` | `SPEC_07`, `org_hierarchy_spec.md` |
| 7 | §5.7 | Communication Capabilities | PARTIAL | `services/notification-service/` | `B2P08` | `notification_service_spec.md` |
| 8 | §5.8 | Workflow Capabilities | PARTIAL | `services/workflow-engine/` | `ARCH_05`, `event_bus_design.md` | `workflow_engine_spec.md` |
| 9 | §5.9 | Interaction Layer Capabilities | PLANNED | None built | None | `interaction_layer_spec.md` (placeholder) |
| 10 | §5.10 | Admin Operations Capabilities | PARTIAL | `services/operations-os/` | `B5P01` | `operations_os_spec.md` |
| 11 | §5.11 | Content Protection Capabilities | PARTIAL→BUILT | `services/media-security/`, `services/file-storage/` (NEW), `services/media-pipeline/` (NEW) | `media_security_interface_contract.md`, `content_storage_model.md`, `storage_adapter_interface_contract.md` | `media_security_spec.md`, `media_pipeline_spec.md` |
| 12 | §5.12 | Offline Capabilities | PARTIAL | `services/offline-sync/` | `offline_sync_interface_contract.md` | `offline_sync_spec.md` |
| 13 | §5.13 | Performance Capabilities | PARTIAL | Cross-cutting (gateway, event-bus, tenant isolation) | `scalability_strategy.md`, `ARCH_07` | `performance_capabilities_spec.md` |
| 14 | §5.14 | Economic Capabilities (User Level) | PARTIAL | `services/commerce/owner_economics.py` | `B3P08_owner_economics_service_design.md` | `economic_capabilities_user_spec.md` |
| 15 | §5.15 | Economic Capabilities (System Level) | PARTIAL | `services/analytics-service/`, `services/commerce/` | `B3P06` | `system_economics_spec.md` |
| 16 | §5.16 | Data & Analytics Capabilities | BUILT | `services/analytics-service/` | `B6P01`–`B6P05` | `AI_01`–`AI_05`, `learning_analytics_spec.md`, `reporting_spec.md`, `analytics_service_spec.md` |
| 17 | §5.17 | Onboarding Capabilities | PARTIAL | `services/onboarding/` | — | `onboarding_spec.md` |
| 18 | §5.18 | Enterprise Capabilities | BUILT | `services/enterprise-control/` | `B2P07`, `define_lms_security_architecture.md` | `SPEC_01`, `SPEC_03`, `sso_spec.md`, `compliance_reporting_spec.md`, `enterprise_control_spec.md` |

---

## Summary

| Status | Count | Domains |
|---|---|---|
| BUILT | 5 | §5.1, §5.2, §5.4, §5.5, §5.18 |
| PARTIAL (code + spec now added) | 12 | §5.3, §5.6, §5.7, §5.8, §5.10, §5.11, §5.12, §5.13, §5.14, §5.15, §5.16, §5.17 |
| PLANNED (no code or service) | 1 | §5.9 Interaction Layer |

---

## Gap Action (Post-Normalisation)

- §5.9: Requires a new service build — see `docs/specs/interaction_layer_spec.md` and Drift Flag DF-03
- §5.6 partial domains (B5P02, B5P03, B5P04): Services for school engagement, workforce, and university are partially built — need dedicated service layer beyond `academy-ops`

---

## References

- Master Spec §5 (all capability domains)
- `doc_catalogue.md` (full doc index with service mapping)
- `docs/specs/B0P04_core_capabilities.json` (core 7 capabilities — superseded in scope by this doc)

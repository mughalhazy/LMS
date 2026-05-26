# Enterprise Control Spec

**Type:** Specification | **Date:** 2026-04-04 | **MS§:** §5.18 | **Service:** `services/enterprise-control/`

---

## Capability Domain: §5.18 Enterprise Capabilities

Covers: RBAC | audit logs | compliance | integrations

---

## Service Boundary

The enterprise control service provides platform-wide enterprise governance capabilities. It orchestrates RBAC enforcement, audit policy, compliance controls, and enterprise integration management. It does not own identity (auth-service does) but enforces access policy across all services.

---

## Capabilities Defined

### CAP-RBAC
- Role-based and attribute-based access control across all platform operations
- Integrates with: `rbac-service-spec.md`
- Delegation, temporary grants, role hierarchy templates
- Owner: `services/enterprise-control/api.py`

### CAP-AUDIT-LOGS
- Immutable audit trail for all administrative, security, and compliance-relevant actions
- Audit events include: who, what, when, from where, outcome
- Retention policies are config-driven
- Integrates with: `audit-policy-layer-design.md`
- QC: `docs/qc/audit-logging-verification-report.md`

### CAP-COMPLIANCE
- Compliance controls: SOC2-friendly data minimisation, encryption, retention, export
- Configurable compliance levels: baseline / enhanced / strict (from segment_configuration)
- Spec ref: `docs/specs/features/compliance-reporting-spec.md`

### CAP-ENTERPRISE-INTEGRATIONS
- HRIS/directory sync, SSO federation, webhook delivery, LTI interoperability
- Owner: `services/integration-service/` (routes through enterprise-control policy layer)

---

## Service Files

- `services/enterprise-control/api.py`
- `services/enterprise-control/models.py`
- `services/enterprise-control/qc.py`
- `services/enterprise-control/service.py`
- `services/enterprise-control/test_enterprise_control_service.py`

---

## References

- Master Spec §5.18
- `docs/designs/audit-policy-layer-design.md`
- `docs/specs/features/compliance-reporting-spec.md`
- `docs/specs/features/rbac-service-spec-v0.md`
- `docs/specs/sso-spec.md`

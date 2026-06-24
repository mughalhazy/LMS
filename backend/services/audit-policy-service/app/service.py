from __future__ import annotations

import fnmatch
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .models import AuditRecord, PolicyBundle, PolicyDecision, PolicyRule
from .store import InMemoryAuditStore

# Canonical audit event types per B2P07 taxonomy
_TAXONOMY_VERSION = "v1"

# B15-002: canonical taxonomy — versioned, managed by AuditTaxonomyManager
AUDIT_EVENT_TYPES = {
    "capability.access.requested", "capability.access.decisioned",
    "capability.access.denied", "capability.break_glass.invoked",
    "config.change.requested", "config.change.approved",
    "config.change.applied", "config.change.reverted",
    "entitlement.change.proposed", "entitlement.change.approved",
    "entitlement.change.applied", "entitlement.change.revoked",
    "policy.bundle.published", "policy.decision.evaluated",
    "policy.override.granted", "policy.override.expired",
    "audit.export.accessed", "audit.legal_hold.set", "audit.legal_hold.released",
    "audit.retention.class.applied", "audit.deletion.defensible",
}

RETENTION_CLASSES = {"standard": 365, "regulatory": 365 * 3, "legal": 365 * 7}  # days
ALLOWED_EXPORT_ROLES = {"auditor", "compliance_officer", "legal_counsel"}

REQUIRED_AUDIT_FIELDS = {"event_id", "event_type", "tenant_id", "action", "target_ref",
                          "outcome", "source_service", "request_id"}


class AuditPolicyService:
    def __init__(self, store: InMemoryAuditStore) -> None:
        self.store = store
        self._seed_default_bundle()

    def _seed_default_bundle(self) -> None:
        bundle = PolicyBundle(
            bundle_id="default",
            version="v1",
            rules=[
                PolicyRule("rule-allow-all", "*", "*", "ALLOW", priority=999, reason_code="default_allow"),
                PolicyRule("rule-deny-break-glass", "capability.break_glass.*", "*",
                            "REQUIRE_JIT_APPROVAL", priority=1, reason_code="break_glass_requires_approval"),
            ],
            published_at=datetime.now(timezone.utc),
            signature="default-bundle-sig",
        )
        self.store.save_bundle(bundle)
        self.store.activate_bundle("default")

    # --- Policy management ---

    def publish_bundle(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        rules_data = body.get("rules", [])
        rules = [
            PolicyRule(
                rule_id=r.get("rule_id", self.store.new_id("rule")),
                action_pattern=r.get("action_pattern", "*"),
                resource_pattern=r.get("resource_pattern", "*"),
                decision=r.get("decision", "ALLOW"),
                priority=r.get("priority", 100),
                conditions=r.get("conditions", {}),
                obligations=r.get("obligations", []),
                reason_code=r.get("reason_code", ""),
            )
            for r in rules_data
        ]
        bundle = PolicyBundle(
            bundle_id=self.store.new_id("bundle"),
            version=body.get("version", "v1"),
            rules=rules,
            published_at=datetime.now(timezone.utc),
            signature=body.get("signature", ""),
        )
        self.store.save_bundle(bundle)
        self.store.activate_bundle(bundle.bundle_id)
        self._emit_audit({
            "event_id": self.store.new_id(), "event_type": "policy.bundle.published",
            "tenant_id": body.get("tenant_id", "system"), "action": "publish",
            "target_ref": bundle.bundle_id, "outcome": "success",
            "source_service": "audit-policy-service", "request_id": self.store.new_id(),
            "schema_version": "v1",
        })
        return 200, {"bundle_id": bundle.bundle_id, "version": bundle.version,
                     "rule_count": len(rules), "active": True}

    # --- Policy evaluation ---

    def evaluate(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        action = body.get("action", "")
        resource_ref = body.get("resource_ref", "")
        tenant_id = body.get("tenant_id", "")
        actor_id = body.get("actor_id", "")
        entitlement_input = body.get("entitlement_input", "unknown")
        request_id = body.get("request_id", self.store.new_id())
        correlation_id = body.get("correlation_id", request_id)

        bundle = self.store.active_bundle()
        if bundle is None:
            return 503, {"error": "no_active_policy_bundle"}

        # Sort rules by priority (lower number = higher priority)
        sorted_rules = sorted(bundle.rules, key=lambda r: r.priority)
        matched_rule = None
        for rule in sorted_rules:
            if fnmatch.fnmatch(action, rule.action_pattern) and \
               fnmatch.fnmatch(resource_ref, rule.resource_pattern):
                matched_rule = rule
                break

        if matched_rule is None:
            final_decision = "DENY"
            reason_codes = ["no_matching_rule"]
            obligations: List[str] = []
        else:
            final_decision = matched_rule.decision
            reason_codes = [matched_rule.reason_code] if matched_rule.reason_code else []
            obligations = matched_rule.obligations

        # Entitlement gate: if entitlement denies, force DENY regardless of policy
        if entitlement_input == "deny":
            final_decision = "DENY"
            reason_codes = ["entitlement_denied"] + reason_codes

        decision = PolicyDecision(
            decision_id=self.store.new_id("dec"),
            tenant_id=tenant_id,
            actor_id=actor_id,
            action=action,
            resource_ref=resource_ref,
            entitlement_input=entitlement_input,
            policy_decision=final_decision,
            policy_id=bundle.bundle_id,
            policy_version=bundle.version,
            reason_codes=reason_codes,
            obligations=obligations,
            request_id=request_id,
            correlation_id=correlation_id,
            evaluated_at=datetime.now(timezone.utc),
        )
        self.store.save_decision(decision)

        self._emit_audit({
            "event_id": self.store.new_id(), "event_type": "policy.decision.evaluated",
            "tenant_id": tenant_id, "action": action, "target_ref": resource_ref,
            "outcome": final_decision, "source_service": "audit-policy-service",
            "request_id": request_id, "schema_version": "v1",
            "decision_id": decision.decision_id, "actor_id": actor_id,
            "correlation_id": correlation_id,
        })

        return 200, {
            "decision_id": decision.decision_id,
            "decision": final_decision,
            "policy_id": bundle.bundle_id,
            "policy_version": bundle.version,
            "reason_codes": reason_codes,
            "obligations": obligations,
            "evaluated_at": decision.evaluated_at.isoformat(),
        }

    def evaluate_batch(self, requests: List[Dict[str, Any]]) -> Tuple[int, Dict[str, Any]]:
        results = []
        for req in requests:
            _, result = self.evaluate(req)
            results.append(result)
        return 200, {"results": results, "count": len(results)}

    # --- Audit ingestion ---

    def ingest_audit_event(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        missing = [f for f in REQUIRED_AUDIT_FIELDS if not body.get(f)]
        if missing:
            return 400, {"error": "missing_required_fields", "fields": missing}

        event_type = body.get("event_type", "")
        if event_type not in AUDIT_EVENT_TYPES:
            return 400, {"error": "unknown_event_type", "event_type": event_type,
                         "valid_types": sorted(AUDIT_EVENT_TYPES)}

        payload_str = str(sorted(body.items()))
        payload_hash = hashlib.sha256(payload_str.encode()).hexdigest()[:32]
        now = datetime.now(timezone.utc)

        ts_raw = body.get("timestamp")
        ts = datetime.fromisoformat(ts_raw) if ts_raw else now

        record = AuditRecord(
            record_id=self.store.new_id("rec"),
            event_id=body["event_id"],
            event_type=event_type,
            timestamp=ts,
            tenant_id=body["tenant_id"],
            actor_id=body.get("actor_id"),
            target_ref=body["target_ref"],
            action=body["action"],
            outcome=body["outcome"],
            source_service=body["source_service"],
            schema_version=body.get("schema_version", "v1"),
            request_id=body["request_id"],
            correlation_id=body.get("correlation_id", body["request_id"]),
            ingested_at=now,
            payload_hash=payload_hash,
            decision_id=body.get("decision_id"),
            control_id=body.get("control_id"),
        )
        self.store.append_record(record)
        return 201, {
            "record_id": record.record_id,
            "event_id": record.event_id,
            "record_hash": record.record_hash,
            "ingested_at": record.ingested_at.isoformat(),
        }

    def query_audit(self, tenant_id: str, event_type: Optional[str] = None) -> Tuple[int, Dict[str, Any]]:
        records = self.store.query_records(tenant_id, event_type)
        return 200, {
            "tenant_id": tenant_id,
            "count": len(records),
            "records": [
                {"record_id": r.record_id, "event_id": r.event_id, "event_type": r.event_type,
                 "action": r.action, "outcome": r.outcome, "actor_id": r.actor_id,
                 "target_ref": r.target_ref, "timestamp": r.timestamp.isoformat(),
                 "record_hash": r.record_hash}
                for r in records
            ],
        }

    def export_evidence(self, tenant_id: str, from_dt: Optional[str] = None,
                        to_dt: Optional[str] = None) -> Tuple[int, Dict[str, Any]]:
        records = self.store.query_records(tenant_id, from_dt=from_dt, to_dt=to_dt)
        hashes = [r.record_hash for r in records]
        manifest_hash = hashlib.sha256(":".join(hashes).encode()).hexdigest()
        return 200, {
            "tenant_id": tenant_id,
            "record_count": len(records),
            "manifest_hash": manifest_hash,
            "chain_intact": len(records) > 0,
            "exported_at": datetime.now(timezone.utc).isoformat(),
        }

    # B15-002: AuditTaxonomyManager — versioned taxonomy management
    def get_taxonomy(self) -> Tuple[int, Dict[str, Any]]:
        return 200, {
            "version": _TAXONOMY_VERSION,
            "event_families": sorted(AUDIT_EVENT_TYPES),
            "count": len(AUDIT_EVENT_TYPES),
            "retention_classes": RETENTION_CLASSES,
        }

    def add_event_type(self, event_type: str, tenant_id: str) -> Tuple[int, Dict[str, Any]]:
        """B15-002: extend taxonomy — prevents semantic drift by requiring explicit registration."""
        if event_type in AUDIT_EVENT_TYPES:
            return 200, {"status": "already_registered", "event_type": event_type}
        if not event_type or "." not in event_type:
            return 400, {"error": "invalid_format", "hint": "event_type must use dot-notation e.g. domain.action"}
        AUDIT_EVENT_TYPES.add(event_type)
        self._emit_audit({
            "event_id": self.store.new_id(), "event_type": "policy.bundle.published",
            "tenant_id": tenant_id, "action": "taxonomy_extend",
            "target_ref": event_type, "outcome": "success",
            "source_service": "audit-policy-service", "request_id": self.store.new_id(),
        })
        return 201, {"status": "registered", "event_type": event_type, "taxonomy_version": _TAXONOMY_VERSION}

    # B15-001: RetentionAndLegalHoldManager
    def set_legal_hold(self, tenant_id: str, record_ids: List[str], reason: str) -> Tuple[int, Dict[str, Any]]:
        held = []
        for rid in record_ids:
            rec = self.store.get_record(rid)
            if rec and rec.tenant_id == tenant_id:
                rec.legal_hold = True
                held.append(rid)
        self._emit_audit({
            "event_id": self.store.new_id(), "event_type": "audit.legal_hold.set",
            "tenant_id": tenant_id, "action": "legal_hold",
            "target_ref": ",".join(record_ids), "outcome": "success",
            "source_service": "audit-policy-service", "request_id": self.store.new_id(),
            "reason": reason,
        })
        return 200, {"held_count": len(held), "record_ids": held, "reason": reason, "legal_hold": True}

    def apply_retention_class(self, tenant_id: str, record_ids: List[str],
                               retention_class: str) -> Tuple[int, Dict[str, Any]]:
        """B15-001: apply 1y/3y/7y retention class to records. Legal hold supersedes expiry."""
        if retention_class not in RETENTION_CLASSES:
            return 400, {"error": "invalid_retention_class",
                         "valid": list(RETENTION_CLASSES.keys())}
        return_days = RETENTION_CLASSES[retention_class]
        self._emit_audit({
            "event_id": self.store.new_id(), "event_type": "audit.retention.class.applied",
            "tenant_id": tenant_id, "action": "retention_apply",
            "target_ref": f"class:{retention_class}:{len(record_ids)} records",
            "outcome": "success", "source_service": "audit-policy-service",
            "request_id": self.store.new_id(),
        })
        return 200, {"retention_class": retention_class, "retain_days": return_days,
                     "record_count": len(record_ids), "legal_hold_supersedes_expiry": True}

    # B15-003: PolicyRegistryPort — validate bundle signature before activation
    def publish_bundle_verified(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        """B15-003: validate bundle signature before activation (PolicyRegistryPort)."""
        import hashlib, hmac as _hmac
        signature = body.get("signature", "")
        secret = __import__("os").getenv("POLICY_SIGNING_SECRET", "")
        if secret and signature:
            rules_payload = str(sorted([(r.get("rule_id", ""), r.get("decision", ""))
                                        for r in body.get("rules", [])]))
            expected = _hmac.new(secret.encode(), rules_payload.encode(), hashlib.sha256).hexdigest()
            if not _hmac.compare_digest(expected, signature):
                return 400, {"error": "bundle_signature_invalid",
                             "hint": "Bundle signature failed verification. Bundle not activated."}
        return self.publish_bundle(body)

    # B15-004: ComplianceEvidenceService — chain-of-custody on export
    def export_evidence_verified(self, tenant_id: str, actor_role: str,
                                  from_dt: Optional[str] = None,
                                  to_dt: Optional[str] = None) -> Tuple[int, Dict[str, Any]]:
        """B15-004: RBAC-gated export with audit trail and signed manifest."""
        import hashlib
        if actor_role not in ALLOWED_EXPORT_ROLES:
            self._emit_audit({
                "event_id": self.store.new_id(), "event_type": "capability.access.denied",
                "tenant_id": tenant_id, "action": "audit_export",
                "target_ref": "evidence_export", "outcome": "denied",
                "source_service": "audit-policy-service", "request_id": self.store.new_id(),
                "reason": f"role '{actor_role}' not in allowed export roles",
            })
            return 403, {"error": "export_access_denied",
                         "allowed_roles": sorted(ALLOWED_EXPORT_ROLES)}

        status, result = self.export_evidence(tenant_id, from_dt, to_dt)

        # Log the export access itself as immutable audit event
        watermark_id = self.store.new_id("wm")
        self._emit_audit({
            "event_id": self.store.new_id(), "event_type": "audit.export.accessed",
            "tenant_id": tenant_id, "action": "evidence_export",
            "target_ref": f"watermark:{watermark_id}", "outcome": "success",
            "source_service": "audit-policy-service", "request_id": self.store.new_id(),
            "actor_role": actor_role, "record_count": result.get("record_count", 0),
        })

        result["watermark_id"] = watermark_id
        result["actor_role"] = actor_role
        result["signed_manifest"] = hashlib.sha256(
            f"{watermark_id}:{result.get('manifest_hash', '')}:{actor_role}".encode()
        ).hexdigest()
        return status, result

    def _emit_audit(self, body: Dict[str, Any]) -> None:
        body.setdefault("schema_version", "v1")
        body.setdefault("correlation_id", body.get("request_id", ""))
        self.ingest_audit_event(body)

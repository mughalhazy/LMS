from __future__ import annotations
import pytest
from app.service import AuditPolicyService
from app.store import InMemoryAuditStore


def _svc() -> AuditPolicyService:
    return AuditPolicyService(InMemoryAuditStore())


def _ctx(**kwargs) -> dict:
    return {"tenant_id": "t1", "actor_id": "admin-1", "entitlement_input": "allow",
            "request_id": "req-1", "correlation_id": "cor-1", **kwargs}


def _audit_event(**kwargs) -> dict:
    return {
        "event_id": "evt-1", "event_type": "config.change.applied",
        "tenant_id": "t1", "action": "config.change.applied",
        "target_ref": "config/feature-x", "outcome": "success",
        "source_service": "config-service", "request_id": "req-1",
        "schema_version": "v1", **kwargs,
    }


def test_default_allow():
    svc = _svc()
    status, body = svc.evaluate({**_ctx(), "action": "read", "resource_ref": "course/123"})
    assert status == 200
    assert body["decision"] == "ALLOW"


def test_break_glass_requires_jit():
    svc = _svc()
    status, body = svc.evaluate({**_ctx(), "action": "capability.break_glass.invoke", "resource_ref": "*"})
    assert status == 200
    assert body["decision"] == "REQUIRE_JIT_APPROVAL"


def test_entitlement_denied_forces_deny():
    svc = _svc()
    status, body = svc.evaluate({**_ctx(entitlement_input="deny"), "action": "read", "resource_ref": "quiz/1"})
    assert status == 200
    assert body["decision"] == "DENY"
    assert "entitlement_denied" in body["reason_codes"]


def test_custom_bundle_deny_rule():
    svc = _svc()
    svc.publish_bundle({
        "version": "v2", "tenant_id": "system",
        "rules": [
            {"rule_id": "deny-all", "action_pattern": "*", "resource_pattern": "*",
             "decision": "DENY", "priority": 100, "reason_code": "blanket_deny"},
        ],
    })
    status, body = svc.evaluate({**_ctx(), "action": "read", "resource_ref": "anything"})
    assert body["decision"] == "DENY"
    assert "blanket_deny" in body["reason_codes"]


def test_evaluate_batch():
    svc = _svc()
    reqs = [
        {**_ctx(), "action": "read", "resource_ref": "r1"},
        {**_ctx(), "action": "write", "resource_ref": "r2"},
    ]
    status, body = svc.evaluate_batch(reqs)
    assert status == 200
    assert body["count"] == 2
    assert all(r["decision"] == "ALLOW" for r in body["results"])


def test_ingest_audit_event():
    svc = _svc()
    status, body = svc.ingest_audit_event(_audit_event())
    assert status == 201
    assert "record_hash" in body


def test_ingest_rejects_unknown_event_type():
    svc = _svc()
    status, body = svc.ingest_audit_event(_audit_event(event_type="billing.invoice.paid"))
    assert status == 400
    assert "unknown_event_type" in body["error"]


def test_ingest_rejects_missing_fields():
    svc = _svc()
    status, body = svc.ingest_audit_event({"event_id": "x"})
    assert status == 400


def test_hash_chain_integrity():
    svc = _svc()
    svc.ingest_audit_event(_audit_event(event_id="e1"))
    svc.ingest_audit_event(_audit_event(event_id="e2", event_type="policy.bundle.published",
                                         action="policy.bundle.published"))
    records = svc.store._records
    # Each record's prev_hash should match the prior record's record_hash
    for i in range(1, len(records)):
        assert records[i].prev_hash == records[i - 1].record_hash


def test_query_audit():
    svc = _svc()
    svc.ingest_audit_event(_audit_event())
    status, body = svc.query_audit("t1")
    assert status == 200
    assert body["count"] >= 1


def test_export_evidence():
    svc = _svc()
    svc.ingest_audit_event(_audit_event())
    status, body = svc.export_evidence("t1")
    assert status == 200
    assert "manifest_hash" in body
    assert body["record_count"] >= 1

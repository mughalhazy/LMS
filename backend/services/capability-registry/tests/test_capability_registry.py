from __future__ import annotations

import pytest

from app.service import CapabilityRegistryService
from app.store import InMemoryCapabilityStore


def _svc() -> CapabilityRegistryService:
    return CapabilityRegistryService(InMemoryCapabilityStore())


def _valid_change(key: str, deps: list = None) -> dict:
    return {
        "key": key,
        "domain": "learning",
        "description": f"{key} capability",
        "dependencies": deps or [],
        "usage_metrics": ["activations"],
        "billing_type": "per_tenant",
        "required_adapters": [],
        "owner": "platform-team",
        "lifecycle_status": "active",
    }


def test_submit_and_publish_draft():
    svc = _svc()
    status, body = svc.submit_draft("admin", [_valid_change("quiz")])
    assert status == 201
    assert body["status"] == "validated"
    draft_id = body["draft_id"]

    status, body = svc.publish_draft(draft_id)
    assert status == 200
    assert "snapshot_version" in body
    assert body["capability_count"] == 1


def test_get_capability_after_publish():
    svc = _svc()
    _, draft = svc.submit_draft("admin", [_valid_change("video")])
    svc.publish_draft(draft["draft_id"])

    status, body = svc.get_capability("video")
    assert status == 200
    assert body["key"] == "video"


def test_get_nonexistent_capability():
    svc = _svc()
    status, body = svc.get_capability("nonexistent")
    assert status == 404


def test_list_capabilities():
    svc = _svc()
    _, d = svc.submit_draft("admin", [_valid_change("quiz"), _valid_change("video")])
    svc.publish_draft(d["draft_id"])

    status, body = svc.list_capabilities()
    assert status == 200
    assert body["count"] == 2


def test_dependency_graph():
    svc = _svc()
    changes = [_valid_change("quiz"), _valid_change("scorm", deps=["quiz"])]
    _, d = svc.submit_draft("admin", changes)
    svc.publish_draft(d["draft_id"])

    status, body = svc.get_dependency_graph()
    assert status == 200
    assert "quiz" in body["graph"]["scorm"]


def test_validation_rejects_missing_required_fields():
    svc = _svc()
    bad_change = {"key": "bad", "domain": "x"}  # missing 4 required fields
    status, body = svc.submit_draft("admin", [bad_change])
    assert status == 422
    assert body["status"] == "rejected"
    assert len(body["validation_errors"]) > 0


def test_validation_rejects_self_dependency():
    svc = _svc()
    change = _valid_change("quiz", deps=["quiz"])
    status, body = svc.submit_draft("admin", [change])
    assert status == 422
    assert any("self-dependency" in e for e in body["validation_errors"])


def test_validation_rejects_cycle():
    svc = _svc()
    changes = [_valid_change("a", deps=["b"]), _valid_change("b", deps=["a"])]
    status, body = svc.submit_draft("admin", changes)
    assert status == 422
    assert any("cycle" in e for e in body["validation_errors"])


def test_snapshot_by_version():
    svc = _svc()
    _, d = svc.submit_draft("admin", [_valid_change("quiz")])
    _, pub = svc.publish_draft(d["draft_id"])
    version = pub["snapshot_version"]

    status, body = svc.get_snapshot(version)
    assert status == 200
    assert body["version"] == version


def test_publish_nonexistent_draft():
    svc = _svc()
    status, body = svc.publish_draft("draft-does-not-exist")
    assert status == 404

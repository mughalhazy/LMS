from __future__ import annotations
import pytest
from app.service import FeatureFlagService, _deterministic_bucket
from app.store import InMemoryFlagStore


def _svc() -> FeatureFlagService:
    return FeatureFlagService(InMemoryFlagStore())


def _flag(svc: FeatureFlagService, **kwargs) -> dict:
    body = {"feature_key": "quiz.new-ui", "default_state": True, **kwargs}
    _, f = svc.upsert_flag(body)
    return f


def _ctx(**kwargs) -> dict:
    return {"tenant_id": "t1", "segment": "corp", "user_id": "u1", **kwargs}


def test_default_enabled():
    svc = _svc()
    _flag(svc, default_state=True)
    _, body = svc.is_enabled({"feature_key": "quiz.new-ui", **_ctx()})
    assert body["enabled"] is True
    assert body["reason"] == "default"


def test_kill_switch_overrides_all():
    svc = _svc()
    _flag(svc, default_state=True, kill_switch=True, tenant_overrides={"t1": True})
    _, body = svc.is_enabled({"feature_key": "quiz.new-ui", **_ctx()})
    assert body["enabled"] is False
    assert body["reason"] == "kill_switch"


def test_entitlement_denied():
    svc = _svc()
    _flag(svc, default_state=True)
    _, body = svc.is_enabled({"feature_key": "quiz.new-ui", "entitlement_denied": True, **_ctx()})
    assert body["enabled"] is False
    assert body["reason"] == "entitlement_denied"


def test_segment_rule():
    svc = _svc()
    _flag(svc, default_state=False, segment_rules={"corp": True})
    _, body = svc.is_enabled({"feature_key": "quiz.new-ui", **_ctx(segment="corp")})
    assert body["enabled"] is True
    assert body["reason"] == "segment_rule"


def test_tenant_override_wins_over_segment():
    svc = _svc()
    _flag(svc, default_state=True, segment_rules={"corp": True}, tenant_overrides={"t1": False})
    _, body = svc.is_enabled({"feature_key": "quiz.new-ui", **_ctx()})
    assert body["enabled"] is False
    assert body["reason"] == "tenant_override"


def test_experiment_deterministic():
    svc = _svc()
    _flag(svc, default_state=False, experiment={
        "experiment_id": "exp-1",
        "variants": [
            {"name": "control", "weight": 50, "state": False},
            {"name": "treatment", "weight": 50, "state": True},
        ],
        "allocation_version": "v1",
    })
    # Same subject key must always get same result
    _, r1 = svc.is_enabled({"feature_key": "quiz.new-ui", **_ctx()})
    _, r2 = svc.is_enabled({"feature_key": "quiz.new-ui", **_ctx()})
    assert r1["enabled"] == r2["enabled"]
    assert r1["experiment_variant"] == r2["experiment_variant"]
    assert r1["reason"] == "experiment"


def test_resolve_many():
    svc = _svc()
    _flag(svc, feature_key="flag-a", default_state=True)
    _flag(svc, feature_key="flag-b", default_state=False)
    _, body = svc.resolve_many({"feature_keys": ["flag-a", "flag-b"], **_ctx()})
    assert body["decisions"]["flag-a"]["enabled"] is True
    assert body["decisions"]["flag-b"]["enabled"] is False


def test_unknown_flag_disabled():
    svc = _svc()
    _, body = svc.is_enabled({"feature_key": "unknown", **_ctx()})
    assert body["enabled"] is False
    assert body["reason"] == "flag_not_found"


def test_bucket_determinism():
    b1 = _deterministic_bucket("exp-1", "t1:u1")
    b2 = _deterministic_bucket("exp-1", "t1:u1")
    assert b1 == b2
    assert 0 <= b1 < 100

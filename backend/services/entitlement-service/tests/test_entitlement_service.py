from __future__ import annotations

import pytest

from app.models import CapabilityMeta, EntitlementContext, PolicyEntry
from app.service import EntitlementService
from app.store import InMemoryPolicyStore, InMemoryRegistryReader


def _build_service() -> EntitlementService:
    policy_store = InMemoryPolicyStore()
    policy_store.seed([
        # universal grants — no plan restriction
        PolicyEntry(capability_key="quiz", granted=True, source="base_plan"),
        PolicyEntry(capability_key="video", granted=True, source="base_plan"),
        # plan-gated
        PolicyEntry(capability_key="scorm", granted=False, source="base_plan", plan="basic"),
        PolicyEntry(capability_key="scorm", granted=True, source="base_plan", plan="enterprise"),
        PolicyEntry(capability_key="analytics", granted=True, source="base_plan", plan="enterprise"),
        # add-on
        PolicyEntry(capability_key="offline", granted=True, source="addon:offline-pack", add_on="offline-pack"),
        # deny via add-on
        PolicyEntry(capability_key="video", granted=False, source="addon:restricted", add_on="restricted-mode"),
    ])

    registry = InMemoryRegistryReader()
    registry.seed([
        CapabilityMeta(key="quiz", dependencies=[]),
        CapabilityMeta(key="video", dependencies=[]),
        CapabilityMeta(key="scorm", dependencies=["video"]),
        CapabilityMeta(key="analytics", dependencies=["quiz"]),
        CapabilityMeta(key="offline", dependencies=["scorm"]),
    ])

    return EntitlementService(policy_store, registry)


def _ctx(**kwargs) -> EntitlementContext:
    defaults = dict(tenant_id="t1", segment="corp", plan="basic", country="PK", add_ons=[])
    defaults.update(kwargs)
    return EntitlementContext(**defaults)


def test_base_plan_grants():
    svc = _build_service()
    _, body = svc.resolve(_ctx())
    assert body["decisions"]["quiz"]["enabled"] is True
    assert body["decisions"]["video"]["enabled"] is True


def test_base_plan_denial():
    svc = _build_service()
    _, body = svc.resolve(_ctx())
    assert body["decisions"]["scorm"]["enabled"] is False
    assert "denied_by_policy" in body["decisions"]["scorm"]["reasons"]


def test_enterprise_plan_enables_scorm():
    svc = _build_service()
    _, body = svc.resolve(_ctx(plan="enterprise"))
    assert body["decisions"]["scorm"]["enabled"] is True


def test_dependency_blocks_scorm_when_video_denied():
    svc = _build_service()
    _, body = svc.resolve(_ctx(plan="enterprise", add_ons=["restricted-mode"]))
    assert body["decisions"]["video"]["enabled"] is False
    assert body["decisions"]["scorm"]["enabled"] is False
    assert any("missing_dependency:video" in r for r in body["decisions"]["scorm"]["reasons"])


def test_addon_grants_capability():
    svc = _build_service()
    _, body = svc.resolve(_ctx(plan="enterprise", add_ons=["offline-pack"]))
    assert body["decisions"]["offline"]["enabled"] is True


def test_deny_wins_over_grant():
    svc = _build_service()
    _, body = svc.resolve(_ctx(add_ons=["restricted-mode"]))
    assert body["decisions"]["video"]["enabled"] is False


def test_is_enabled_single_capability():
    svc = _build_service()
    _, body = svc.is_enabled(_ctx(), "quiz")
    assert body["enabled"] is True
    assert body["capability_key"] == "quiz"


def test_addons_sorted_lexically():
    svc = _build_service()
    _, body = svc.resolve(_ctx(add_ons=["restricted-mode", "offline-pack"]))
    order = body["evaluation_order"]
    addon_steps = [s for s in order if s.startswith("addon:")]
    assert addon_steps == sorted(addon_steps)

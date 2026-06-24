from __future__ import annotations

import pytest
from datetime import datetime, timezone

from app.models import ConfigEntry
from app.schemas import ResolutionContext
from app.service import ConfigService
from app.store import InMemoryLayerStore


def _store_with_entries() -> InMemoryLayerStore:
    store = InMemoryLayerStore()
    store.seed([
        ConfigEntry(key="feature.max_users", value=100, level="global", revision="rev-1"),
        ConfigEntry(key="feature.max_users", value=200, level="country", revision="rev-1", country_code="PK"),
        ConfigEntry(key="feature.max_users", value=500, level="plan", revision="rev-1", plan_key="enterprise"),
        ConfigEntry(key="ui.theme", value="light", level="global", revision="rev-1"),
        ConfigEntry(key="ui.theme", value="dark", level="tenant", revision="rev-1", tenant_id="tenant-abc"),
        ConfigEntry(key="payments.gateway", value="stripe", level="segment", revision="rev-1", segment_key="corp"),
        ConfigEntry(key="cap.quiz.max_attempts", value=3, level="global", revision="rev-1", capability_key="quiz"),
    ])
    return store


def _ctx(**kwargs) -> ResolutionContext:
    defaults = dict(
        tenant_id="tenant-abc",
        country_code="PK",
        segment_key="corp",
        plan_key="enterprise",
    )
    defaults.update(kwargs)
    return ResolutionContext(**defaults)


def test_resolve_key_global_fallback():
    svc = ConfigService(_store_with_entries())
    status, body = svc.resolve_key(_ctx(tenant_id="other"), "ui.theme")
    assert status == 200
    assert body["value"] == "light"
    assert body["provenance"] == "global"


def test_resolve_key_tenant_wins():
    svc = ConfigService(_store_with_entries())
    status, body = svc.resolve_key(_ctx(), "ui.theme")
    assert status == 200
    assert body["value"] == "dark"
    assert body["provenance"] == "tenant"


def test_resolve_key_plan_wins_over_country():
    svc = ConfigService(_store_with_entries())
    status, body = svc.resolve_key(_ctx(), "feature.max_users")
    assert status == 200
    assert body["value"] == 500
    assert body["provenance"] == "plan"


def test_resolve_key_not_found():
    svc = ConfigService(_store_with_entries())
    status, body = svc.resolve_key(_ctx(), "nonexistent.key")
    assert status == 404


def test_resolve_keys_multiple():
    svc = ConfigService(_store_with_entries())
    status, body = svc.resolve_keys(_ctx(), ["ui.theme", "feature.max_users"])
    assert status == 200
    assert body["values"]["ui.theme"] == "dark"
    assert body["values"]["feature.max_users"] == 500


def test_resolve_namespace():
    svc = ConfigService(_store_with_entries())
    status, body = svc.resolve_namespace(_ctx(), "ui")
    assert status == 200
    assert "ui.theme" in body["values"]
    assert "feature.max_users" not in body["values"]


def test_capability_projection():
    svc = ConfigService(_store_with_entries())
    ctx = _ctx(capability_key="quiz")
    status, body = svc.resolve_keys(ctx, None)
    assert status == 200
    assert "cap.quiz.max_attempts" in body["values"]
    assert "ui.theme" not in body["values"]

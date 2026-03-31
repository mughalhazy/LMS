import json

from app.main import service


def test_plan_type_capabilities_resolve_from_runtime_mapping(monkeypatch) -> None:
    monkeypatch.setenv(
        "SUBSCRIPTION_PLAN_CAPABILITIES_JSON",
        json.dumps(
            {
                "free": ["course.read"],
                "pro": ["course.read", "assessment.attempt"],
                "enterprise": ["course.read", "analytics.read"],
            }
        ),
    )

    tenant, _ = service.create_tenant(
        name="Dynamic Entitlements",
        country_code="US",
        segment_type="enterprise",
        plan_type="enterprise",
        addon_flags=["ai_tutor"],
        admin_user="admin-ent",
    )

    assert service.get_tenant_capabilities(tenant.tenant_id) == {"course.read", "analytics.read"}


def test_plan_capability_mapping_updates_without_tenant_mutation(monkeypatch) -> None:
    monkeypatch.setenv("SUBSCRIPTION_PLAN_CAPABILITIES_JSON", json.dumps({"pro": ["course.read"]}))

    tenant, _ = service.create_tenant(
        name="Runtime Update Tenant",
        country_code="US",
        segment_type="enterprise",
        plan_type="pro",
        addon_flags=[],
        admin_user="admin-runtime",
    )

    assert service.get_tenant_capabilities(tenant.tenant_id) == {"course.read"}

    monkeypatch.setenv(
        "SUBSCRIPTION_PLAN_CAPABILITIES_JSON",
        json.dumps({"pro": ["course.read", "recommendation.basic", "assessment.attempt"]}),
    )

    assert service.get_tenant_capabilities(tenant.tenant_id) == {
        "course.read",
        "recommendation.basic",
        "assessment.attempt",
    }

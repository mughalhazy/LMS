from app.main import service
from app.models import TenantConfiguration


def test_admin_actions_are_audited_with_required_fields() -> None:
    tenant, _ = service.create_tenant(
        name="Acme",
        country_code="US",
        segment_type="enterprise",
        plan_type="enterprise",
        addon_flags=["ai_tutor"],
        admin_user="admin-1",
    )

    service.patch_configuration(tenant.tenant_id, {"timezone": "UTC"}, actor_id="admin-1", reason="ops")
    service.initialize_configuration(tenant.tenant_id, TenantConfiguration(), actor_id="admin-1")

    event = service.audit_logger.list_events()[-1]
    assert event.event_type == "admin.tenant.configuration.initialized"
    assert event.tenant_id == tenant.tenant_id
    assert event.actor_id == "admin-1"
    assert event.timestamp is not None
    assert event.destination == "loki"

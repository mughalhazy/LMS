from app.main import TenantAPI
from app.schemas import CreateTenantRequest, UpdateTenantConfigurationRequest


def test_admin_actions_are_audited_with_required_fields() -> None:
    api = TenantAPI()
    created = api.create_tenant(
        CreateTenantRequest(
            tenant_name="Acme",
            tenant_code="acme-audit",
            primary_domain="acme-audit.example.com",
            admin_user="admin-1",
            data_residency_region="us-east",
            subscription_plan="enterprise",
        )
    )

    api.update_tenant_configuration(
        created.tenant_id,
        UpdateTenantConfigurationRequest(config_patch={"timezone": "UTC"}, actor_id="admin-1", change_reason="ops"),
    )

    event = api.service.audit_logger.list_events()[-1]
    assert event.event_type == "admin.tenant.configuration.updated"
    assert event.tenant_id == created.tenant_id
    assert event.actor_id == "admin-1"
    assert event.timestamp is not None
    assert event.destination == "loki"

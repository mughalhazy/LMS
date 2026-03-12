import unittest

from app.main import TenantAPI
from app.schemas import (
    CreateTenantRequest,
    InitializeTenantConfigurationRequest,
    IsolationContext,
    SuspendTenantRequest,
    UpdateTenantConfigurationRequest,
    ValidateTenantCreationRequest,
)


class TenantServiceTests(unittest.TestCase):
    def test_tenant_lifecycle_configuration_and_isolation(self) -> None:
        api = TenantAPI()

        validate = api.validate_tenant_creation(
            ValidateTenantCreationRequest(
                tenant_code="acme",
                primary_domain="acme.example.com",
                admin_email="admin@acme.example.com",
                requested_region="us-east",
            )
        )
        self.assertTrue(validate.validation_passed)

        created = api.create_tenant(
            CreateTenantRequest(
                tenant_name="Acme Inc",
                tenant_code="acme",
                primary_domain="acme.example.com",
                admin_user="admin_1",
                data_residency_region="us-east",
                subscription_plan="enterprise",
            )
        )
        tenant_id = created.tenant_id
        self.assertEqual(created.isolation_mode, "database_per_tenant")

        init_config = api.initialize_tenant_configuration(
            tenant_id,
            InitializeTenantConfigurationRequest(
                default_locale="en-US",
                timezone="UTC",
                branding={"theme": "dark"},
                enabled_modules=["courses", "certifications"],
                security_baseline={"security.require_mfa": True},
            ),
        )
        self.assertEqual(init_config.configuration.version, 1)

        patched = api.update_tenant_configuration(
            tenant_id,
            UpdateTenantConfigurationRequest(
                config_patch={"timezone": "America/New_York"}, actor_id="admin_1", change_reason="regional"
            ),
        )
        self.assertEqual(patched.configuration.version, 2)

        api.suspend_tenant(tenant_id, SuspendTenantRequest(suspension_reason="billing_hold", suspended_by="system"))

        denied = api.evaluate_isolation(
            IsolationContext(tenant_id=tenant_id, actor_tenant_id=tenant_id, actor_id="admin_1", action="write")
        )
        self.assertFalse(denied.allowed)

        cross_tenant = api.evaluate_isolation(
            IsolationContext(tenant_id=tenant_id, actor_tenant_id="another_tenant", actor_id="admin_1", action="read")
        )
        self.assertFalse(cross_tenant.allowed)


if __name__ == "__main__":
    unittest.main()

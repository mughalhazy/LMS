from __future__ import annotations

from datetime import datetime, timezone

from app.errors import TenantServiceError
from app.models import LifecycleState, TenantConfiguration
from app.repository import TenantRepository
from app.schemas import (
    ArchiveTenantRequest,
    CreateTenantRequest,
    CreateTenantResponse,
    DecommissionTenantRequest,
    InitializeTenantConfigurationRequest,
    IsolationContext,
    IsolationDecision,
    LifecycleStatusResponse,
    ManageFeatureFlagsRequest,
    ReactivateTenantRequest,
    SuspendTenantRequest,
    TenantConfigurationResponse,
    UpdateTenantConfigurationRequest,
    ValidateTenantCreationRequest,
    ValidationResponse,
)
from app.service import TenantService


class TenantAPI:
    def __init__(self) -> None:
        self.service = TenantService(TenantRepository())

    def validate_tenant_creation(self, request: ValidateTenantCreationRequest) -> ValidationResponse:
        errors = self.service.validate_creation(request.tenant_code, request.primary_domain, request.requested_region)
        return ValidationResponse(validation_passed=not errors, errors=errors)

    def create_tenant(self, request: CreateTenantRequest) -> CreateTenantResponse:
        tenant, namespace = self.service.create_tenant(**request.__dict__)
        return CreateTenantResponse(
            tenant_id=tenant.tenant_id,
            bootstrap_status="complete",
            isolation_mode=tenant.isolation_mode.value,
            namespace_resource=namespace.resource_locator,
        )

    def initialize_tenant_configuration(
        self, tenant_id: str, request: InitializeTenantConfigurationRequest
    ) -> TenantConfigurationResponse:
        config = self.service.initialize_configuration(tenant_id, TenantConfiguration(**request.__dict__))
        tenant = self.service.get_tenant(tenant_id)
        return TenantConfigurationResponse(
            tenant_id=tenant_id,
            configuration=config,
            effective_settings=self.service.effective_settings(tenant, include_defaults=True),
        )

    def update_tenant_configuration(self, tenant_id: str, request: UpdateTenantConfigurationRequest) -> TenantConfigurationResponse:
        config = self.service.patch_configuration(tenant_id, request.config_patch, request.actor_id, request.change_reason)
        tenant = self.service.get_tenant(tenant_id)
        return TenantConfigurationResponse(
            tenant_id=tenant_id,
            configuration=config,
            effective_settings=self.service.effective_settings(tenant, include_defaults=True),
        )

    def get_tenant_configuration(self, tenant_id: str, include_effective_defaults: bool = True) -> TenantConfigurationResponse:
        tenant = self.service.get_tenant(tenant_id)
        return TenantConfigurationResponse(
            tenant_id=tenant_id,
            configuration=tenant.configuration,
            effective_settings=self.service.effective_settings(tenant, include_defaults=include_effective_defaults),
        )

    def manage_tenant_feature_flags(self, tenant_id: str, request: ManageFeatureFlagsRequest) -> TenantConfigurationResponse:
        config = self.service.manage_feature_flags(tenant_id, request.feature_flag_changes, request.actor_id)
        tenant = self.service.get_tenant(tenant_id)
        return TenantConfigurationResponse(
            tenant_id=tenant_id,
            configuration=config,
            effective_settings=self.service.effective_settings(tenant, include_defaults=True),
        )

    def suspend_tenant(self, tenant_id: str, request: SuspendTenantRequest) -> dict:
        tenant = self.service.transition_lifecycle(
            tenant_id, LifecycleState.SUSPENDED, request.suspension_reason, request.suspended_by, request.effective_at
        )
        return {"suspension_receipt": {"tenant_id": tenant.tenant_id, "state": tenant.lifecycle_state}}

    def reactivate_tenant(self, tenant_id: str, request: ReactivateTenantRequest) -> dict:
        tenant = self.service.transition_lifecycle(
            tenant_id, LifecycleState.ACTIVE, request.reactivation_reason, request.approved_by, request.effective_at
        )
        return {"reactivation_receipt": {"tenant_id": tenant.tenant_id, "state": tenant.lifecycle_state}}

    def archive_tenant(self, tenant_id: str, request: ArchiveTenantRequest) -> dict:
        tenant = self.service.transition_lifecycle(
            tenant_id,
            LifecycleState.ARCHIVED,
            f"archive_policy:{request.archive_policy};retention:{request.retention_period}",
            request.requested_by,
            datetime.now(timezone.utc),
        )
        return {"archive_status": {"tenant_id": tenant.tenant_id, "state": tenant.lifecycle_state}}

    def decommission_tenant(self, tenant_id: str, request: DecommissionTenantRequest) -> dict:
        reason = f"legal_hold={request.legal_hold_status};purge_after={request.purge_after_date.isoformat()}"
        tenant = self.service.transition_lifecycle(
            tenant_id, LifecycleState.DECOMMISSIONED, reason, request.approved_by, request.purge_after_date
        )
        return {"decommission_status": {"tenant_id": tenant.tenant_id, "state": tenant.lifecycle_state}}

    def get_tenant_lifecycle_status(self, tenant_id: str) -> LifecycleStatusResponse:
        tenant = self.service.get_tenant(tenant_id)
        pending = {
            LifecycleState.ACTIVE: ["suspend", "archive"],
            LifecycleState.SUSPENDED: ["reactivate", "archive"],
            LifecycleState.ARCHIVED: ["decommission"],
            LifecycleState.DECOMMISSIONED: [],
            LifecycleState.PROVISIONING: ["activate"],
        }
        constraints = [
            "cross-tenant writes are denied",
            "suspended tenants cannot create sessions or write data",
            "archived/decommissioned tenants are immutable",
        ]
        return LifecycleStatusResponse(
            tenant_id=tenant_id,
            lifecycle_state=tenant.lifecycle_state,
            state_history=tenant.state_history,
            pending_transitions=pending[tenant.lifecycle_state],
            policy_constraints=constraints,
            next_allowed_actions=pending[tenant.lifecycle_state],
        )

    def evaluate_isolation(self, context: IsolationContext) -> IsolationDecision:
        return self.service.enforce_isolation(context)


__all__ = ["TenantAPI", "TenantServiceError"]


HEALTH_ENDPOINT = "/health"
METRICS_ENDPOINT = "/metrics"


def health() -> dict[str, str]:
    return {"status": "ok", "service": "tenant-service"}


def metrics() -> dict[str, int | str]:
    return {"service": "tenant-service", "service_up": 1}

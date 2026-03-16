from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.errors import TenantServiceError
from app.events import InMemoryEventPublisher
from app.middleware import TenantContextMiddleware
from app.models import LifecycleState, TenantConfiguration
from app.observability import MetricsRegistry
from app.repository import InMemoryTenantStore
from app.schemas import (
    ArchiveTenantRequest,
    CreateTenantRequest,
    CreateTenantResponse,
    DecommissionTenantRequest,
    InitializeTenantConfigurationRequest,
    IsolationContext,
    IsolationDecision,
    LifecycleEventResponse,
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

store = InMemoryTenantStore()
metrics_registry = MetricsRegistry()
event_publisher = InMemoryEventPublisher()
service = TenantService(store=store, publisher=event_publisher, metrics=metrics_registry)

app = FastAPI(title="Tenant Service", version="2.0.0")
app.middleware("http")(TenantContextMiddleware())


class TenantAPI:
    def __init__(self) -> None:
        self.service = service

    def validate_tenant_creation(self, request: ValidateTenantCreationRequest) -> ValidationResponse:
        errors = self.service.validate_creation(request.tenant_code, request.primary_domain, request.requested_region)
        return ValidationResponse(validation_passed=not errors, errors=errors)

    def create_tenant(self, request: CreateTenantRequest) -> CreateTenantResponse:
        tenant, namespace = self.service.create_tenant(**request.model_dump())
        return CreateTenantResponse(
            tenant_id=tenant.tenant_id,
            bootstrap_status="complete",
            isolation_mode=tenant.isolation_mode.value,
            namespace_resource=namespace.resource_locator,
        )


api = TenantAPI()


@app.exception_handler(TenantServiceError)
async def handle_service_error(_, exc: TenantServiceError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "tenant-service"}


@app.get("/metrics")
def metrics() -> dict[str, float | int | str]:
    return {"service": "tenant-service", "service_up": 1, **metrics_registry.export()}


@app.post("/api/v1/tenants/validate", response_model=ValidationResponse)
def validate_tenant_creation(request: ValidateTenantCreationRequest) -> ValidationResponse:
    return api.validate_tenant_creation(request)


@app.post("/api/v1/tenants", response_model=CreateTenantResponse)
def create_tenant(request: CreateTenantRequest) -> CreateTenantResponse:
    return api.create_tenant(request)


@app.put("/api/v1/tenants/{tenant_id}/configuration", response_model=TenantConfigurationResponse)
def initialize_tenant_configuration(tenant_id: str, request: InitializeTenantConfigurationRequest) -> TenantConfigurationResponse:
    config = service.initialize_configuration(tenant_id, TenantConfiguration(**request.model_dump()), actor_id="system")
    tenant = service.get_tenant(tenant_id)
    return TenantConfigurationResponse(
        tenant_id=tenant_id,
        configuration=asdict(config),
        effective_settings=service.effective_settings(tenant, include_defaults=True),
    )


@app.patch("/api/v1/tenants/{tenant_id}/configuration", response_model=TenantConfigurationResponse)
def update_tenant_configuration(tenant_id: str, request: UpdateTenantConfigurationRequest) -> TenantConfigurationResponse:
    config = service.patch_configuration(tenant_id, request.config_patch, request.actor_id, request.change_reason)
    tenant = service.get_tenant(tenant_id)
    return TenantConfigurationResponse(
        tenant_id=tenant_id,
        configuration=asdict(config),
        effective_settings=service.effective_settings(tenant, include_defaults=True),
    )


@app.patch("/api/v1/tenants/{tenant_id}/feature-flags", response_model=TenantConfigurationResponse)
def manage_tenant_feature_flags(tenant_id: str, request: ManageFeatureFlagsRequest) -> TenantConfigurationResponse:
    config = service.manage_feature_flags(tenant_id, request.feature_flag_changes, request.actor_id)
    tenant = service.get_tenant(tenant_id)
    return TenantConfigurationResponse(
        tenant_id=tenant_id,
        configuration=asdict(config),
        effective_settings=service.effective_settings(tenant, include_defaults=True),
    )


@app.post("/api/v1/tenants/{tenant_id}/lifecycle/suspend")
def suspend_tenant(tenant_id: str, request: SuspendTenantRequest) -> dict:
    tenant = service.transition_lifecycle(tenant_id, LifecycleState.SUSPENDED, request.suspension_reason, request.suspended_by, datetime.now(timezone.utc))
    return {"suspension_receipt": {"tenant_id": tenant.tenant_id, "state": tenant.lifecycle_state}}


@app.post("/api/v1/tenants/{tenant_id}/lifecycle/reactivate")
def reactivate_tenant(tenant_id: str, request: ReactivateTenantRequest) -> dict:
    tenant = service.transition_lifecycle(tenant_id, LifecycleState.ACTIVE, request.reactivation_reason, request.approved_by, datetime.now(timezone.utc))
    return {"reactivation_receipt": {"tenant_id": tenant.tenant_id, "state": tenant.lifecycle_state}}


@app.post("/api/v1/tenants/{tenant_id}/lifecycle/archive")
def archive_tenant(tenant_id: str, request: ArchiveTenantRequest) -> dict:
    tenant = service.transition_lifecycle(
        tenant_id,
        LifecycleState.ARCHIVED,
        f"archive_policy:{request.archive_policy};retention:{request.retention_period}",
        request.requested_by,
        datetime.now(timezone.utc),
    )
    return {"archive_status": {"tenant_id": tenant.tenant_id, "state": tenant.lifecycle_state}}


@app.post("/api/v1/tenants/{tenant_id}/lifecycle/decommission")
def decommission_tenant(tenant_id: str, request: DecommissionTenantRequest) -> dict:
    reason = f"legal_hold={request.legal_hold_status};purge_after={request.purge_after_date.isoformat()}"
    tenant = service.transition_lifecycle(tenant_id, LifecycleState.DECOMMISSIONED, reason, request.approved_by, request.purge_after_date)
    return {"decommission_status": {"tenant_id": tenant.tenant_id, "state": tenant.lifecycle_state}}


@app.get("/api/v1/tenants/{tenant_id}/lifecycle", response_model=LifecycleStatusResponse)
def get_tenant_lifecycle_status(tenant_id: str) -> LifecycleStatusResponse:
    tenant = service.get_tenant(tenant_id)
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
        "service does not own institution hierarchy, auth, courses, or enrollments",
    ]
    history = [LifecycleEventResponse(**asdict(event)) for event in tenant.state_history]
    return LifecycleStatusResponse(
        tenant_id=tenant_id,
        lifecycle_state=tenant.lifecycle_state,
        state_history=history,
        pending_transitions=pending[tenant.lifecycle_state],
        policy_constraints=constraints,
        next_allowed_actions=pending[tenant.lifecycle_state],
    )


@app.post("/api/v1/isolation/evaluate", response_model=IsolationDecision)
def evaluate_isolation(context: IsolationContext) -> IsolationDecision:
    return service.enforce_isolation(context)

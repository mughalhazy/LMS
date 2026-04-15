from __future__ import annotations

from fastapi import FastAPI, HTTPException, Depends
from .security import apply_security_headers, require_jwt

from app.models import (
    ConsumerLaunchCompleteRequest,
    ConsumerLaunchInitiateRequest,
    ConsumerToolRegistrationRequest,
    GradePassbackRequest,
    IdentityMappingRequest,
    LaunchValidationRequest,
    MembershipSyncRequest,
    OIDCLoginInitiationRequest,
    RoleNormalizationRequest,
    ServiceAccessTokenRequest,
    SessionProvisioningRequest,
    ToolRegistrationRequest,
    ValidationActivationRequest,
)
from app.service import LTIService

app = FastAPI(title="lti-service", version="0.1.0", dependencies=[Depends(require_jwt)])

apply_security_headers(app)
service = LTIService()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "lti-service"}


@app.post("/provider/tools/register")
def provider_register_tool(req: ToolRegistrationRequest):
    return service.register_provider_tool(req)


@app.post("/provider/tools/validate-activation")
def provider_validate_activation(req: ValidationActivationRequest):
    try:
        return service.activate_provider_registration(req)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="tool_not_found") from exc


@app.post("/provider/launch/login")
def provider_launch_login(req: OIDCLoginInitiationRequest):
    return service.initiate_oidc_login(req)


@app.post("/provider/launch/validate")
def provider_launch_validate(req: LaunchValidationRequest):
    try:
        return service.validate_launch(req)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/provider/launch/session")
def provider_launch_session(req: SessionProvisioningRequest):
    return service.provision_session(req)


@app.post("/provider/identity/map")
def provider_identity_map(req: IdentityMappingRequest):
    return service.map_identity(req)


@app.post("/provider/identity/normalize-roles")
def provider_normalize_roles(req: RoleNormalizationRequest):
    return service.normalize_roles(req)


@app.post("/provider/services/token")
def provider_services_token(req: ServiceAccessTokenRequest):
    try:
        return service.issue_service_access_token(req)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/provider/services/ags/score")
def provider_services_ags_score(req: GradePassbackRequest):
    return service.grade_passback(req)


@app.post("/provider/services/nrps/sync")
def provider_services_nrps_sync(req: MembershipSyncRequest):
    return service.membership_sync(req)


@app.post("/consumer/tools/register")
def consumer_tool_register(req: ConsumerToolRegistrationRequest):
    return service.register_consumer_tool(req)


@app.post("/consumer/launch/initiate")
def consumer_launch_initiate(req: ConsumerLaunchInitiateRequest):
    try:
        return service.initiate_consumer_launch(req)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/consumer/launch/complete")
def consumer_launch_complete(req: ConsumerLaunchCompleteRequest):
    try:
        return service.complete_consumer_launch(req)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/metrics")
def metrics() -> dict[str, int | str]:
    return {"service": "lti-service", "service_up": 1}


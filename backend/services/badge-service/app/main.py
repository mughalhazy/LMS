from __future__ import annotations

from fastapi import Depends, FastAPI, Query

from .store_db import SQLiteBadgeRepository
from .schemas import (
    BadgeDefinitionCreate,
    BadgeDefinitionOut,
    BadgeDefinitionPatch,
    BadgeIssuanceCreate,
    BadgeIssuanceOut,
    BadgeIssuancePatch,
)
from .security import apply_security_headers, require_jwt
from .service import BadgeService

app = FastAPI(title="Badge Service", version="1.0.0", dependencies=[Depends(require_jwt)])


# CAT-004: api-versioning-strategy.md §1 — X-API-Version header required on every response
@app.middleware("http")
async def _add_api_version_header(request, call_next):
    response = await call_next(request)
    response.headers["X-API-Version"] = "v1"
    return response


# FA-024 / G-24: register event consumers on startup
from .consumers import register_consumers as _register_consumers
_register_consumers()


apply_security_headers(app)
repository = SQLiteBadgeRepository()
service = BadgeService(repository)


@app.post("/api/v1/badge/definitions", response_model=BadgeDefinitionOut, status_code=201)
def create_badge_definition(payload: BadgeDefinitionCreate) -> BadgeDefinitionOut:
    return service.create_badge_definition(payload.model_dump())


@app.get("/api/v1/badge/definitions", response_model=list[BadgeDefinitionOut])
def list_badge_definitions(tenant_id: str = Query(...)) -> list[BadgeDefinitionOut]:
    return service.list_badge_definitions(tenant_id)


@app.patch("/api/v1/badge/definitions/{badge_id}", response_model=BadgeDefinitionOut)
def patch_badge_definition(badge_id: str, payload: BadgeDefinitionPatch, tenant_id: str = Query(...)) -> BadgeDefinitionOut:
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    return service.patch_badge_definition(tenant_id, badge_id, updates)


@app.post("/api/v1/badge/issuances", response_model=BadgeIssuanceOut, status_code=201)
def create_badge_issuance(payload: BadgeIssuanceCreate) -> BadgeIssuanceOut:
    return service.issue_badge(payload.model_dump())


@app.patch("/api/v1/badge/issuances/{issuance_id}", response_model=BadgeIssuanceOut)
def patch_badge_issuance(
    issuance_id: str,
    payload: BadgeIssuancePatch,
    tenant_id: str = Query(...),
) -> BadgeIssuanceOut:
    return service.patch_badge_issuance(tenant_id, issuance_id, payload.model_dump())


@app.get("/api/v1/badge/learners/{learner_id}/history")
def get_learner_badge_history(tenant_id: str = Query(...), learner_id: str = "") -> dict:
    return service.list_learner_badge_history(tenant_id=tenant_id, learner_id=learner_id)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "badge-service"}

@app.get("/metrics")
def metrics() -> dict[str, int | str]:
    return {"service": "badge-service", "service_up": 1}


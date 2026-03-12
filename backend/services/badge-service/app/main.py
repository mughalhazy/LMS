from __future__ import annotations

from fastapi import FastAPI

from .repository import InMemoryBadgeRepository
from .schemas import (
    BadgeDefinitionCreate,
    BadgeDefinitionOut,
    BadgeDefinitionPatch,
    BadgeIssuanceCreate,
    BadgeIssuanceOut,
    BadgeIssuancePatch,
)
from .service import BadgeService

app = FastAPI(title="Badge Service", version="1.0.0")
repository = InMemoryBadgeRepository()
service = BadgeService(repository)


@app.post("/badges", response_model=BadgeDefinitionOut, status_code=201)
def create_badge_definition(payload: BadgeDefinitionCreate) -> BadgeDefinitionOut:
    return service.create_badge_definition(payload.model_dump())


@app.get("/badges", response_model=list[BadgeDefinitionOut])
def list_badge_definitions(tenant_id: str | None = None) -> list[BadgeDefinitionOut]:
    return service.list_badge_definitions(tenant_id)


@app.patch("/badges/{badge_id}", response_model=BadgeDefinitionOut)
def patch_badge_definition(badge_id: str, payload: BadgeDefinitionPatch) -> BadgeDefinitionOut:
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    return service.patch_badge_definition(badge_id, updates)


@app.post("/badge-issuances", response_model=BadgeIssuanceOut, status_code=201)
def create_badge_issuance(payload: BadgeIssuanceCreate) -> BadgeIssuanceOut:
    return service.issue_badge(payload.model_dump())


@app.patch("/badge-issuances/{issuance_id}", response_model=BadgeIssuanceOut)
def patch_badge_issuance(issuance_id: str, payload: BadgeIssuancePatch) -> BadgeIssuanceOut:
    return service.patch_badge_issuance(issuance_id, payload.model_dump())


@app.get("/learners/{learner_id}/badges")
def get_learner_badge_history(tenant_id: str, learner_id: str) -> dict:
    return service.list_learner_badge_history(tenant_id=tenant_id, learner_id=learner_id)

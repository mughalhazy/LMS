"""Service entrypoint — skill-analytics-service REST API."""

from __future__ import annotations

from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel

from .security import apply_security_headers, require_jwt
from .service import SkillAnalyticsApplicationService

# B13-002: multi-tenant-isolation-model §2 — JWT required
app = FastAPI(title="skill-analytics-service", version="1.0.0", dependencies=[Depends(require_jwt)])


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
_SVC = SkillAnalyticsApplicationService()


# ── Request schemas ───────────────────────────────────────────────────────────

class GapDetectionRequest(BaseModel):
    tenant_id: str
    learner_id: str
    role_profile_id: str
    urgency_factor: float = 1.0


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "skill-analytics-service"}


@app.get("/metrics")
def metrics() -> dict[str, int | str]:
    return {"service": "skill-analytics-service", "service_up": 1}


# B13-003: skill-analytics-spec.md — 3 spec metrics exposed as routes

@app.get("/api/v1/skill-analytics/learners/{learner_id}/progress")
def skill_progress(
    learner_id: str,
    tenant_id: str = Query(...),
    skill_id: str = Query(...),
    target_level: float = Query(...),
    time_window_days: int = Query(default=30),
) -> dict[str, Any]:
    """skill-analytics-spec metric 1: Skill Progress (baseline, change, velocity, milestone %)."""
    return _SVC.get_skill_progress(
        tenant_id=tenant_id,
        learner_id=learner_id,
        skill_id=skill_id,
        target_level=target_level,
        time_window_days=time_window_days,
    )


@app.post("/api/v1/skill-analytics/learners/{learner_id}/gaps")
def detect_skill_gaps(learner_id: str, request: GapDetectionRequest) -> list[dict[str, Any]]:
    """skill-analytics-spec metric 2: Skill Gap Detection (ranked gaps with interventions)."""
    return _SVC.detect_skill_gaps(
        tenant_id=request.tenant_id,
        learner_id=learner_id,
        role_profile_id=request.role_profile_id,
        urgency_factor=request.urgency_factor,
    )


@app.get("/api/v1/skill-analytics/learners/{learner_id}/mastery/{skill_id}")
def mastery_score(
    learner_id: str,
    skill_id: str,
    tenant_id: str = Query(...),
) -> dict[str, Any]:
    """skill-analytics-spec metric 3: Skill Mastery Scoring (composite mastery + bands)."""
    return _SVC.get_mastery_score(
        tenant_id=tenant_id,
        learner_id=learner_id,
        skill_id=skill_id,
    )


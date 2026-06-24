"""Service entrypoint — prerequisite-engine-service REST API."""

from __future__ import annotations

from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query, status
from pydantic import BaseModel

from .security import apply_security_headers, require_jwt
from .service import PrerequisiteEngineService

# B13-005: multi-tenant-isolation-model §2 — JWT required
app = FastAPI(title="prerequisite-engine-service", version="1.0.0", dependencies=[Depends(require_jwt)])


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
_SVC = PrerequisiteEngineService()


# ── Request schemas ───────────────────────────────────────────────────────────

class EnrollmentEvaluationRequest(BaseModel):
    tenant_id: str
    target_course_id: str
    learner_id: str
    transcript: list[dict[str, Any]]


class EnrollmentOverrideRequest(BaseModel):
    tenant_id: str
    target_course_id: str
    learner_id: str
    override_by: str
    reason_code: str
    notes: str = ""


class PathProgressionRequest(BaseModel):
    tenant_id: str
    path_id: str
    learner_id: str
    node_id: str
    attempt_outcomes: list[dict[str, Any]]


class EligibilityRequest(BaseModel):
    tenant_id: str
    learner_id: str
    course_ids: list[str]


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "prerequisite-engine-service"}


@app.get("/metrics")
def metrics() -> dict[str, int | str]:
    return {"service": "prerequisite-engine-service", "service_up": 1}


# B13-006: prerequisite-engine-spec.md — enforcement routes

@app.post("/api/v1/prerequisites/enroll")
def evaluate_enrollment(request: EnrollmentEvaluationRequest) -> dict:
    """prerequisite-engine-spec rule: course_prerequisite — evaluate enrollment eligibility."""
    result = _SVC.evaluate_enrollment(
        tenant_id=request.tenant_id,
        target_course_id=request.target_course_id,
        learner_id=request.learner_id,
        transcript=request.transcript,
    )
    return {
        "enrollment_decision": result.enrollment_decision.value,
        "unmet_prerequisites": list(result.unmet_prerequisites),
        "remedial_recommendations": result.remedial_recommendations,
        "audit_id": result.audit_id,
    }


@app.post("/api/v1/prerequisites/enroll/override")
def override_enrollment(request: EnrollmentOverrideRequest) -> dict:
    """prerequisite-engine-spec: policy override path with audit logging."""
    return _SVC.override_enrollment(
        tenant_id=request.tenant_id,
        target_course_id=request.target_course_id,
        learner_id=request.learner_id,
        override_by=request.override_by,
        reason_code=request.reason_code,
        notes=request.notes,
    )


@app.post("/api/v1/prerequisites/path-progression")
def evaluate_path_progression(request: PathProgressionRequest) -> dict:
    """prerequisite-engine-spec rule: learning_path_dependency — recompute unlock state."""
    return _SVC.evaluate_path_progression(
        tenant_id=request.tenant_id,
        path_id=request.path_id,
        learner_id=request.learner_id,
        node_id=request.node_id,
        attempt_outcomes=request.attempt_outcomes,
    )


@app.post("/api/v1/prerequisites/eligibility")
def check_eligibility(request: EligibilityRequest) -> dict:
    """Check learner eligibility for multiple courses at once."""
    return _SVC.check_learner_eligibility(
        tenant_id=request.tenant_id,
        learner_id=request.learner_id,
        course_ids=request.course_ids,
    )


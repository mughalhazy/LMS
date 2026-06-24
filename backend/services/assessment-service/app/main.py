from __future__ import annotations

from fastapi import Depends, FastAPI, Response

from .audit import AuditLogger
from .events import InMemoryEventPublisher
from .models import AssessmentStatus
from .observability import ServiceMetrics
from .schemas import (
    AssessmentCreateRequest,
    AssessmentListResponse,
    AssessmentResponse,
    AssessmentUpdateRequest,
    AttemptResponse,
    AttemptStartRequest,
    GradeAttemptRequest,
    HealthResponse,
    ItemCreateRequest,
    ItemResponse,
    ItemUpdateRequest,
    MetricsResponse,
    SubmissionCreateRequest,
    SubmissionResponse,
    VersionCreateRequest,
    VersionPublishRequest,
    VersionResponse,
)
from .service import AssessmentService
from .store_db import SQLiteAssessmentStore
from .tenant import tenant_context

app = FastAPI(title="Assessment Service", version="1.0.0")


# CAT-004: api-versioning-strategy.md §1 — X-API-Version header required on every response
@app.middleware("http")
async def _add_api_version_header(request, call_next):
    response = await call_next(request)
    response.headers["X-API-Version"] = "v1"
    return response


# FA-024 / G-24: register event consumers on startup
from .consumers import register_consumers as _register_consumers
_register_consumers()


store = SQLiteAssessmentStore()
audit_logger = AuditLogger()
event_publisher = InMemoryEventPublisher()
metrics = ServiceMetrics()
service = AssessmentService(store, event_publisher, audit_logger, metrics)


@app.post("/api/v1/assessments", response_model=AssessmentResponse)
def create_assessment(request: AssessmentCreateRequest, tenant_id: str = Depends(tenant_context)) -> AssessmentResponse:
    return service.create_assessment(tenant_id, request)


@app.get("/api/v1/assessments", response_model=AssessmentListResponse)
def list_assessments(tenant_id: str = Depends(tenant_context)) -> AssessmentListResponse:
    return service.list_assessments(tenant_id)


@app.get("/api/v1/assessments/{assessment_id}", response_model=AssessmentResponse)
def get_assessment(assessment_id: str, tenant_id: str = Depends(tenant_context)) -> AssessmentResponse:
    return service.get_assessment(tenant_id, assessment_id)


@app.patch("/api/v1/assessments/{assessment_id}", response_model=AssessmentResponse)
@app.put("/api/v1/assessments/{assessment_id}", response_model=AssessmentResponse)
def update_assessment(
    assessment_id: str,
    request: AssessmentUpdateRequest,
    tenant_id: str = Depends(tenant_context),
) -> AssessmentResponse:
    return service.update_assessment(tenant_id, assessment_id, request)


@app.post("/api/v1/assessments/{assessment_id}/publish", response_model=AssessmentResponse)
def publish_assessment(assessment_id: str, actor_id: str, tenant_id: str = Depends(tenant_context)) -> AssessmentResponse:
    return service.transition_assessment(tenant_id, assessment_id, actor_id, AssessmentStatus.PUBLISHED)


@app.post("/api/v1/assessments/{assessment_id}/activate", response_model=AssessmentResponse)
def activate_assessment(assessment_id: str, actor_id: str, tenant_id: str = Depends(tenant_context)) -> AssessmentResponse:
    return service.transition_assessment(tenant_id, assessment_id, actor_id, AssessmentStatus.ACTIVE)


@app.post("/api/v1/assessments/{assessment_id}/retire", response_model=AssessmentResponse)
def retire_assessment(assessment_id: str, actor_id: str, tenant_id: str = Depends(tenant_context)) -> AssessmentResponse:
    return service.transition_assessment(tenant_id, assessment_id, actor_id, AssessmentStatus.RETIRED)


@app.delete("/api/v1/assessments/{assessment_id}", status_code=204)
def delete_assessment(assessment_id: str, actor_id: str, tenant_id: str = Depends(tenant_context)) -> Response:
    service.delete_assessment(tenant_id, assessment_id, actor_id)
    return Response(status_code=204)


@app.post("/api/v1/assessments/{assessment_id}/attempts", response_model=AttemptResponse)
def start_attempt(
    assessment_id: str,
    request: AttemptStartRequest,
    tenant_id: str = Depends(tenant_context),
) -> AttemptResponse:
    return service.start_attempt(tenant_id, assessment_id, request)


@app.get("/api/v1/assessments/{assessment_id}/attempts", response_model=list[AttemptResponse])
def list_attempts(assessment_id: str, tenant_id: str = Depends(tenant_context)) -> list[AttemptResponse]:
    return service.list_attempts(tenant_id, assessment_id)


# AUD-005: spec §5.3 — canonical path includes assessment_id; /submissions alias kept
@app.post("/api/v1/assessments/{assessment_id}/attempts/{attempt_id}/submit", response_model=SubmissionResponse, status_code=202)
@app.post("/api/v1/attempts/{attempt_id}/submissions", response_model=SubmissionResponse)
def submit_attempt(
    attempt_id: str,
    request: SubmissionCreateRequest,
    tenant_id: str = Depends(tenant_context),
    assessment_id: str = "",
) -> SubmissionResponse:
    return service.submit_attempt(tenant_id, attempt_id, request)


# AUD-007: spec §5.4 — grade-link is canonical; /grade kept as alias
@app.post("/api/v1/attempts/{attempt_id}/grade-link", response_model=AttemptResponse)
@app.post("/api/v1/attempts/{attempt_id}/grade", response_model=AttemptResponse)
def grade_attempt(
    attempt_id: str,
    request: GradeAttemptRequest,
    tenant_id: str = Depends(tenant_context),
) -> AttemptResponse:
    return service.grade_attempt(tenant_id, attempt_id, request)


# AUD-006: spec §5.3 — canonical path includes assessment_id; bare /attempts/{id} kept as alias
@app.get("/api/v1/assessments/{assessment_id}/attempts/{attempt_id}", response_model=AttemptResponse)
@app.get("/api/v1/attempts/{attempt_id}", response_model=AttemptResponse)
def get_attempt(attempt_id: str, tenant_id: str = Depends(tenant_context), assessment_id: str = "") -> AttemptResponse:
    return service.get_attempt(tenant_id, attempt_id)


@app.get("/api/v1/attempts/{attempt_id}/results")
def get_attempt_results(attempt_id: str, tenant_id: str = Depends(tenant_context)) -> dict[str, object]:
    return service.get_attempt_results(tenant_id, attempt_id)


# ── Spec §4 — Assessment versioning system (FA-013) ──────────────────────────

@app.post("/api/v1/assessments/{assessment_id}/versions", response_model=VersionResponse, status_code=201)
def create_version(assessment_id: str, request: VersionCreateRequest, tenant_id: str = Depends(tenant_context)) -> VersionResponse:
    return service.create_version(tenant_id, assessment_id, request)


@app.post("/api/v1/assessments/{assessment_id}/versions/{version_number}/publish", response_model=VersionResponse)
def publish_version(assessment_id: str, version_number: int, request: VersionPublishRequest, tenant_id: str = Depends(tenant_context)) -> VersionResponse:
    return service.publish_version(tenant_id, assessment_id, version_number, request)


@app.post("/api/v1/assessments/{assessment_id}/versions/{version_number}/items", response_model=ItemResponse, status_code=201)
def create_item(assessment_id: str, version_number: int, request: ItemCreateRequest, tenant_id: str = Depends(tenant_context)) -> ItemResponse:
    return service.create_item(tenant_id, assessment_id, version_number, request)


@app.patch("/api/v1/assessments/{assessment_id}/versions/{version_number}/items/{item_id}", response_model=ItemResponse)
def update_item(assessment_id: str, version_number: int, item_id: str, request: ItemUpdateRequest, tenant_id: str = Depends(tenant_context)) -> ItemResponse:
    return service.update_item(tenant_id, assessment_id, version_number, item_id, request)


@app.delete("/api/v1/assessments/{assessment_id}/versions/{version_number}/items/{item_id}", status_code=204)
def delete_item(assessment_id: str, version_number: int, item_id: str, tenant_id: str = Depends(tenant_context)) -> Response:
    service.delete_item(tenant_id, assessment_id, version_number, item_id)
    return Response(status_code=204)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="assessment-service")


@app.get("/metrics", response_model=MetricsResponse)
def get_metrics() -> MetricsResponse:
    return MetricsResponse(service="assessment-service", counters=metrics.snapshot())


@app.get("/api/v1/observability/hooks")
def observability_hooks() -> dict[str, object]:
    return {
        "metrics_endpoint": "/metrics",
        "events_buffered": len(event_publisher.events),
        "audit_records": len(audit_logger.records),
    }

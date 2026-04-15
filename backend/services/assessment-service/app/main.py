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
    MetricsResponse,
    SubmissionCreateRequest,
    SubmissionResponse,
)
from .service import AssessmentService
from .store import InMemoryAssessmentStore
from .tenant import tenant_context

app = FastAPI(title="Assessment Service", version="1.0.0")

store = InMemoryAssessmentStore()
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


@app.post("/api/v1/attempts/{attempt_id}/submissions", response_model=SubmissionResponse)
def submit_attempt(
    attempt_id: str,
    request: SubmissionCreateRequest,
    tenant_id: str = Depends(tenant_context),
) -> SubmissionResponse:
    return service.submit_attempt(tenant_id, attempt_id, request)


@app.post("/api/v1/attempts/{attempt_id}/grade", response_model=AttemptResponse)
def grade_attempt(
    attempt_id: str,
    request: GradeAttemptRequest,
    tenant_id: str = Depends(tenant_context),
) -> AttemptResponse:
    return service.grade_attempt(tenant_id, attempt_id, request)


@app.get("/api/v1/attempts/{attempt_id}", response_model=AttemptResponse)
def get_attempt(attempt_id: str, tenant_id: str = Depends(tenant_context)) -> AttemptResponse:
    return service.get_attempt(tenant_id, attempt_id)


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

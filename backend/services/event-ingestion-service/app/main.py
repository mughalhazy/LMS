from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException

from .forwarders import AIForwarder, AnalyticsForwarder, ForwardingPipeline
from .observability import MetricsRecorder
from .schemas import HealthResponse, IngestionRequest, IngestionResponse
from .service import EventIngestionService
from .store import InMemoryAuditStorage, InMemoryEventStorage


app = FastAPI(title="Event Ingestion Service", version="1.0.0")
service = EventIngestionService(
    event_store=InMemoryEventStorage(),
    audit_store=InMemoryAuditStorage(),
    forwarding_pipeline=ForwardingPipeline([AnalyticsForwarder(), AIForwarder()]),
    metrics=MetricsRecorder(),
)


def require_runtime_context(
    tenant_id: Annotated[str, Header(alias="X-Tenant-Id")],
    request_id: Annotated[str, Header(alias="X-Request-Id")],
) -> tuple[str, str]:
    return tenant_id, request_id


@app.post("/events/ingest", response_model=IngestionResponse)
def ingest_event(
    request: IngestionRequest,
    runtime_context: tuple[str, str] = Depends(require_runtime_context),
) -> IngestionResponse:
    tenant_id, _request_id = runtime_context
    if tenant_id != request.tenant_id:
        raise HTTPException(status_code=400, detail="x_tenant_id_mismatch")
    return IngestionResponse(result=service.ingest(request))


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    state = service.health()
    return HealthResponse(
        status="ok" if all(state.values()) else "degraded",
        service="event-ingestion-service",
        storage_ok=state["storage_ok"],
        forwarders_ok=state["forwarders_ok"],
    )


@app.get("/metrics")
def metrics() -> dict[str, int | str]:
    return {"service": "event-ingestion-service", **service.metrics()}

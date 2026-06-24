from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException

from .forwarders import (
    AIForwarder,
    AnalyticsForwarder,
    ForwardingPipeline,
    OperationsOSForwarder,
    RevenueSignalForwarder,
    WorkflowForwarder,
)
from .observability import MetricsRecorder
from .schemas import (BatchIngestionRequest, HealthResponse, IngestionRequest,
                      IngestionResponse, ReplayRequest, ValidateRequest)
from .service import EventIngestionService
from .store import InMemoryAuditStorage, InMemoryEventStorage

# ─── Cross-layer service wiring (CGAP-019 / CGAP-020) ────────────────────────
# Load WorkflowEngine and OperationsOSService from the services/ layer so that
# ingested events are actually delivered to them via the ForwardingPipeline.
# In a production deployment these would be replaced by HTTP/gRPC/Kafka clients.
# References: workflow_engine_spec.md BC-WF-01, operations_os_spec.md BC-OPS-01

_ROOT = Path(__file__).resolve().parents[4]


def _load_module(name: str, relative_path: str):
    module_path = _ROOT / relative_path
    sys.path.append(str(module_path.parent))
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_WorkflowModule = _load_module("ei_workflow_engine", "services/workflow-engine/service.py")
_OpsOSModule = _load_module("ei_operations_os", "services/operations-os/service.py")

WorkflowEngine = _WorkflowModule.WorkflowEngine
OperationsOSService = _OpsOSModule.OperationsOSService

_workflow_engine = WorkflowEngine()
_workflow_engine.bootstrap_default_workflows()

_ops_os_service = OperationsOSService()

# ─── Service assembly ─────────────────────────────────────────────────────────

app = FastAPI(title="Event Ingestion Service", version="1.0.0")


# CAT-004: api-versioning-strategy.md §1 — X-API-Version header required on every response
@app.middleware("http")
async def _add_api_version_header(request, call_next):
    response = await call_next(request)
    response.headers["X-API-Version"] = "v1"
    return response


# FA-024 / G-24: register event consumers on startup
from .consumers import register_consumers as _register_consumers
_register_consumers()

service = EventIngestionService(
    event_store=InMemoryEventStorage(),
    audit_store=InMemoryAuditStorage(),
    forwarding_pipeline=ForwardingPipeline([
        AnalyticsForwarder(),
        AIForwarder(),
        WorkflowForwarder(_workflow_engine),          # CGAP-019
        OperationsOSForwarder(_ops_os_service),       # CGAP-020
        RevenueSignalForwarder(_ops_os_service),      # MO-035 / Phase D: BC-ECON-01 revenue → DAL
    ]),
    metrics=MetricsRecorder(),
)


def require_runtime_context(
    tenant_id: Annotated[str, Header(alias="X-Tenant-Id")],
    request_id: Annotated[str, Header(alias="X-Request-Id")],
) -> tuple[str, str]:
    return tenant_id, request_id


@app.post("/v1/events/ingest", response_model=IngestionResponse)
@app.post("/events/ingest", response_model=IngestionResponse, include_in_schema=False)
def ingest_event(
    request: IngestionRequest,
    runtime_context: tuple[str, str] = Depends(require_runtime_context),
) -> IngestionResponse:
    tenant_id, _request_id = runtime_context
    if tenant_id != request.tenant_id:
        raise HTTPException(status_code=400, detail="x_tenant_id_mismatch")
    return IngestionResponse(result=service.ingest(request))


@app.post("/v1/events/ingest/batch", status_code=200)
def ingest_batch(
    request: BatchIngestionRequest,
    runtime_context: tuple[str, str] = Depends(require_runtime_context),
) -> dict:
    """B15-038: batch ingest — multiple envelopes per call."""
    tenant_id, _ = runtime_context
    for ev in request.events:
        if ev.tenant_id != tenant_id:
            raise HTTPException(status_code=400, detail=f"tenant_mismatch on event {ev.event_id}")
    return service.ingest_batch(request.events)


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


@app.post("/v1/events/replay", status_code=202)
def replay_events(
    request: ReplayRequest,
    runtime_context: tuple[str, str] = Depends(require_runtime_context),
) -> dict:
    """B15-035: replay stored events matching filter back through forwarding pipeline."""
    tenant_id, _ = runtime_context
    if request.tenant_id != tenant_id:
        raise HTTPException(status_code=400, detail="x_tenant_id_mismatch")
    result = service.replay_events(tenant_id, request.event_type, request.from_ts,
                                   request.to_ts, request.tags)
    return {"status": "replayed", **result}


@app.post("/v1/events/validate", status_code=200)
def validate_event(
    request: ValidateRequest,
    runtime_context: tuple[str, str] = Depends(require_runtime_context),
) -> dict:
    """B15-036: validate event schema against canonical envelope contract without persisting."""
    return service.validate_event(request)

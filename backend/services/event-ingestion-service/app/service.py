from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from .forwarders import ForwardingPipeline
from .models import AuditLogEntry, EventActor, EventEntityRef, EventRecord, IngestResult, NormalizedEvent
from .observability import MetricsRecorder, Timer
from .schemas import IngestionRequest
from .store import AuditStorage, EventStorage


class EventIngestionService:
    def __init__(
        self,
        event_store: EventStorage,
        audit_store: AuditStorage,
        forwarding_pipeline: ForwardingPipeline,
        metrics: MetricsRecorder,
    ) -> None:
        self._event_store = event_store
        self._audit_store = audit_store
        self._forwarding_pipeline = forwarding_pipeline
        self._metrics = metrics

    def ingest(self, request: IngestionRequest) -> IngestResult:
        timer = Timer()
        normalized = self._normalize(request)
        record = EventRecord(
            record_id=f"evtrec_{uuid4().hex}",
            event=normalized,
            storage_partition=f"tenant::{normalized.tenant_id}",
        )

        self._event_store.persist(record)
        self._audit_store.append(
            AuditLogEntry(
                audit_id=f"audit_{uuid4().hex}",
                tenant_id=normalized.tenant_id,
                action="event_ingested",
                event_id=normalized.event_id,
                metadata={
                    "family": normalized.family.value,
                    "event_type": normalized.event_type,
                    "trace_id": normalized.trace.trace_id,
                },
            )
        )
        forward_results = self._forwarding_pipeline.publish(normalized)

        self._metrics.increment("events_ingested_total")
        self._metrics.increment(f"events_ingested_family_{normalized.family.value}")
        self._metrics.observe_duration_ms("ingestion_latency", timer.elapsed_ms())

        return IngestResult(record=record, forward_results=forward_results)

    def health(self) -> dict[str, bool]:
        return {
            "storage_ok": self._event_store.health(),
            "forwarders_ok": self._forwarding_pipeline.health(),
        }

    def metrics(self) -> dict[str, int]:
        return self._metrics.snapshot().counters

    def _normalize(self, request: IngestionRequest) -> NormalizedEvent:
        normalized_payload = {
            "keys": sorted(list(request.payload.keys())),
            "value_types": {k: type(v).__name__ for k, v in request.payload.items()},
            "source": request.source,
            "event_type": request.event_type,
        }

        return NormalizedEvent(
            event_id=request.event_id,
            tenant_id=request.tenant_id,
            family=request.family,
            event_type=request.event_type,
            source=request.source,
            occurred_at=request.occurred_at.astimezone(timezone.utc),
            ingested_at=datetime.now(timezone.utc),
            trace=request.trace,
            actor=EventActor(**request.actor) if request.actor else None,
            entity=EventEntityRef(**request.entity) if request.entity else None,
            payload=request.payload,
            normalized_payload=normalized_payload,
            tags=sorted(set(request.tags)),
        )

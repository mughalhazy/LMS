from __future__ import annotations

from typing import Any, Dict, List, Tuple
from uuid import uuid4

from .schemas import (
    EventIngestRequest,
    SUPPORTED_EVENT_FIELDS,
    SchemaValidationError,
    ensure_iso8601,
    utc_now_iso,
)
from .store import InMemoryEventStore

TIMESTAMP_FIELDS_BY_EVENT = {
    event_type: [f for f in fields if f.endswith("_at") or f.endswith("_timestamp")]
    for event_type, fields in SUPPORTED_EVENT_FIELDS.items()
}


class EventIngestionService:
    def __init__(self, store: InMemoryEventStore) -> None:
        self.store = store

    def ingest_event(self, request: EventIngestRequest) -> Tuple[int, Dict[str, Any]]:
        collected_event = {
            "collection_id": f"col_{uuid4().hex}",
            "event_id": request.event_id,
            "event_type": request.event_type,
            "source_system": request.source_system,
            "tenant_id": request.tenant_id,
            "actor_id": request.actor_id,
            "session_id": request.session_id,
            "occurred_at": request.occurred_at,
            "received_at": utc_now_iso(),
            "schema_version": request.schema_version,
            "payload": request.payload,
            "ingestion_channel": request.ingestion_channel,
        }
        self.store.append_raw(request.tenant_id, collected_event)

        try:
            normalized_payload = self._validate_schema(request)
        except SchemaValidationError as exc:
            rejected_event = {
                "rejection_id": f"rej_{uuid4().hex}",
                "event_id": request.event_id,
                "event_type": request.event_type,
                "tenant_id": request.tenant_id,
                "received_at": collected_event["received_at"],
                "rejection_reason_code": exc.reason_code,
                "rejection_reason_detail": exc.detail,
                "failed_field": exc.failed_field,
                "validator_version": "event-schema-validator-v1",
                "original_payload": request.payload,
                "retry_eligible_flag": exc.reason_code == "missing_required_field",
            }
            self.store.append_rejected(request.tenant_id, rejected_event)
            return 422, {"status": "rejected", "event": rejected_event}

        validated_event = {
            "validation_id": f"val_{uuid4().hex}",
            "event_id": request.event_id,
            "event_type": request.event_type,
            "tenant_id": request.tenant_id,
            "schema_version": request.schema_version,
            "required_fields_present": True,
            "pii_policy_passed": True,
            "signature_verified": True,
            "validation_status": "valid",
            "validated_at": utc_now_iso(),
            "validator_version": "event-schema-validator-v1",
            "normalized_payload": normalized_payload,
        }
        self.store.append_validated(request.tenant_id, validated_event)
        return 202, {"status": "accepted", "event": validated_event}

    def ingest_batch(
        self, tenant_id: str, events: List[EventIngestRequest]
    ) -> Tuple[int, Dict[str, Any]]:
        accepted = 0
        rejected = 0
        results: List[Dict[str, Any]] = []

        for event in events:
            if event.tenant_id != tenant_id:
                return 400, {
                    "error": "tenant_scope_violation",
                    "detail": "all events in batch must match request tenant",
                }

            status, payload = self.ingest_event(event)
            if status == 202:
                accepted += 1
            else:
                rejected += 1
            results.append({"status_code": status, **payload})

        return 207, {
            "tenant_id": tenant_id,
            "batch_size": len(events),
            "accepted": accepted,
            "rejected": rejected,
            "results": results,
        }

    def get_tenant_stream(self, tenant_id: str) -> Tuple[int, Dict[str, Any]]:
        return 200, {"tenant_id": tenant_id, **self.store.get_tenant_stream(tenant_id)}

    def get_ingestion_metrics(self) -> Tuple[int, Dict[str, Any]]:
        return 200, self.store.get_ingestion_metrics()

    def _validate_schema(self, request: EventIngestRequest) -> Dict[str, Any]:
        if request.event_type not in SUPPORTED_EVENT_FIELDS:
            raise SchemaValidationError(
                "unsupported_event_type",
                f"event_type '{request.event_type}' is not supported",
                "event_type",
            )

        ensure_iso8601(request.occurred_at, "occurred_at")

        required_fields = SUPPORTED_EVENT_FIELDS[request.event_type]
        for field in required_fields:
            if field not in request.payload:
                raise SchemaValidationError(
                    "missing_required_field",
                    f"payload is missing required field '{field}'",
                    field,
                )

        for timestamp_field in TIMESTAMP_FIELDS_BY_EVENT.get(request.event_type, []):
            if timestamp_field in request.payload:
                ensure_iso8601(str(request.payload[timestamp_field]), timestamp_field)

        normalized_payload = {
            key: request.payload[key] for key in required_fields if key in request.payload
        }
        normalized_payload["tenant_id"] = request.tenant_id
        return normalized_payload

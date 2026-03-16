from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EventFamily(str, Enum):
    USER = "user"
    COURSE = "course"
    LESSON = "lesson"
    ENROLLMENT = "enrollment"
    PROGRESS = "progress"
    ASSESSMENT = "assessment"
    CERTIFICATE = "certificate"
    AI = "ai"


class EventTrace(BaseModel):
    trace_id: str
    correlation_id: str
    causation_id: Optional[str] = None
    span_id: Optional[str] = None


class EventActor(BaseModel):
    actor_id: str
    actor_type: str = "user"


class EventEntityRef(BaseModel):
    entity_id: str
    entity_type: str


class NormalizedEvent(BaseModel):
    event_id: str
    tenant_id: str
    family: EventFamily
    event_type: str
    source: str
    occurred_at: datetime
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    trace: EventTrace
    actor: Optional[EventActor] = None
    entity: Optional[EventEntityRef] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    normalized_payload: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class EventRecord(BaseModel):
    record_id: str
    event: NormalizedEvent
    storage_partition: str


class ForwardResult(BaseModel):
    target: str
    accepted: bool
    reason: Optional[str] = None


class IngestResult(BaseModel):
    record: EventRecord
    forward_results: List[ForwardResult] = Field(default_factory=list)


class AuditLogEntry(BaseModel):
    audit_id: str
    tenant_id: str
    action: str
    event_id: str
    at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

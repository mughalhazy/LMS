from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .models import EventFamily, EventTrace, IngestResult


class IngestionRequest(BaseModel):
    event_id: str
    tenant_id: str
    family: EventFamily
    event_type: str
    source: str
    occurred_at: datetime
    trace: EventTrace
    actor: Optional[Dict[str, Any]] = None
    entity: Optional[Dict[str, Any]] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class IngestionResponse(BaseModel):
    result: IngestResult


class HealthResponse(BaseModel):
    status: str
    service: str
    storage_ok: bool
    forwarders_ok: bool

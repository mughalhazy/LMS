from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class OfflineDownload:
    download_id: str
    user_id: str
    tenant_id: str
    content_id: str
    content_type: str
    status: str = "requested"   # requested | approved | downloading | available | expired
    storage_bytes: int = 0
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ProgressEvent:
    event_id: str
    user_id: str
    tenant_id: str
    event_type: str
    payload: Dict[str, Any]
    idempotency_key: str
    synced: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class OperatorActionIntent:
    intent_id: str
    tenant_id: str
    operator_id: str
    action_type: str            # mark_attendance | record_payment | add_note | fee_followup | approve_reject
    payload: Dict[str, Any]
    idempotency_key: str
    synced: bool = False
    sync_failed: bool = False
    failure_reason: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

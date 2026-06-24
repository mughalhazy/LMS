from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class OfflineProgressEvent:
    """B15-027: canonical shared model for offline progress events.
    Append-only ledger — all events preserved, most-recent timestamp wins for progress state."""
    event_id: str
    user_id: str
    tenant_id: str
    content_id: str
    event_type: str          # lesson_completed | quiz_answered | progress_checkpoint
    progress_pct: float      # 0.0–100.0
    score: Optional[float]   # for quiz events
    payload: Dict[str, Any] = field(default_factory=dict)
    idempotency_key: str = ""
    recorded_offline_at: datetime = field(default_factory=datetime.utcnow)
    synced_at: Optional[datetime] = None
    conflict_resolved: bool = False
    winning_timestamp: Optional[datetime] = None  # timestamp that won conflict resolution


@dataclass
class OfflineSyncConflict:
    conflict_id: str
    user_id: str
    tenant_id: str
    content_id: str
    local_event_id: str
    server_event_id: str
    resolution: str          # local_wins | server_wins | merged
    resolved_at: datetime = field(default_factory=datetime.utcnow)

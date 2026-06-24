from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Review:
    tenant_id: str
    course_id: str
    learner_id: str
    rating: int          # 1–5
    body: str
    review_id: str = field(default_factory=lambda: str(uuid4()))
    status: str = "pending"   # pending | published | rejected
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

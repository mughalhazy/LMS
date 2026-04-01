from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class TeacherBatchEconomics:
    teacher_id: str
    batch_id: str
    ownership_mode: str
    revenue_share_percent: Decimal
    payout_schedule: str
    earnings_to_date: Decimal = Decimal("0.00")
    pending_payout_amount: Decimal = Decimal("0.00")
    metadata: dict[str, Any] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


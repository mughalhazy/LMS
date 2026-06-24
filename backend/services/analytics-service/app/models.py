from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class AnalyticsEvent:
    event_id: str
    tenant_id: str
    event_type: str        # progress | enrollment | assessment | engagement
    entity_id: str         # learner_id / course_id / cohort_id
    entity_type: str
    metric_key: str
    value: float
    period: str            # YYYY-MM-DD
    recorded_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class InsightEnvelope:
    """BC-ANALYTICS-01: every output wrapped in insight envelope."""
    metric: str
    current_value: float
    prior_value: Optional[float]
    trend: str             # e.g. "down_14pct_vs_last_period" | "up_8pct" | "stable"
    context: str           # human-readable comparative context
    suggested_action: str  # BC-ANALYTICS-01: mandatory
    action_link: str
    comparative_ref: str   # BC-ANALYTICS-02: comparative reference type
    tenant_id: str
    entity_id: str
    period: str
    generated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class BenchmarkEntry:
    entity_id: str
    entity_type: str       # learner | course | instructor | cohort
    metric_key: str
    value: float
    rank: int
    percentile: float
    vs_cohort_avg: float
    vs_platform_avg: Optional[float] = None

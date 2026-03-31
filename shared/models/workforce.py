from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

WorkforceAudience = Literal["workforce"]


@dataclass(frozen=True)
class MandatoryTrainingPolicy:
    policy_id: str
    title: str
    course_id: str
    renewal_cycle_days: int
    audience: WorkforceAudience = "workforce"


@dataclass(frozen=True)
class MandatoryTrainingAssignment:
    tenant_id: str
    learner_id: str
    manager_id: str
    policy_id: str
    course_id: str
    assigned_on: date
    due_on: date
    completion_status: Literal["not_started", "in_progress", "completed"] = "not_started"
    audience: WorkforceAudience = "workforce"


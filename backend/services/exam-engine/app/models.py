from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ProctorConfig:
    single_window: bool = True
    copy_paste_disabled: bool = True
    time_per_question_seconds: Optional[int] = None
    ip_allowlist: List[str] = field(default_factory=list)
    max_tab_switches: int = 0


@dataclass
class ExamDefinition:
    exam_id: str
    tenant_id: str
    title: str
    assessment_ref: str       # reference to assessment-service question bank
    duration_seconds: int
    proctor_config: ProctorConfig
    max_attempts: int = 1
    passing_score_pct: float = 60.0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ExamSession:
    session_id: str
    exam_id: str
    attempt_id: str           # reference to attempt-service record
    tenant_id: str
    candidate_id: str
    status: str               # started | in_progress | submitted | graded | timed_out
    started_at: datetime
    expires_at: datetime
    answers: Dict[str, Any] = field(default_factory=dict)
    proctor_events: List[Dict[str, Any]] = field(default_factory=list)
    resume_token: Optional[str] = None
    submitted_at: Optional[datetime] = None
    timed_out_at: Optional[datetime] = None

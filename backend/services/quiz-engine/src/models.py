from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional


class QuestionType(str, Enum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"


@dataclass(frozen=True)
class QuizOption:
    option_id: str
    text: str
    is_correct: bool = False


@dataclass(frozen=True)
class QuizQuestion:
    question_id: str
    prompt: str
    question_type: QuestionType
    options: List[QuizOption]
    points: float = 1.0


@dataclass(frozen=True)
class QuizDefinition:
    quiz_id: str
    tenant_id: str
    title: str
    questions: List[QuizQuestion]
    duration_seconds: int
    randomize_questions: bool = True


@dataclass
class QuizSession:
    session_id: str
    quiz_id: str
    tenant_id: str
    user_id: str
    ordered_question_ids: List[str]
    started_at: datetime
    expires_at: datetime
    submitted_at: Optional[datetime] = None
    answers: Dict[str, List[str]] = field(default_factory=dict)

    @property
    def is_submitted(self) -> bool:
        return self.submitted_at is not None

    @property
    def is_expired(self) -> bool:
        return datetime.now(tz=timezone.utc) > self.expires_at

    def time_remaining(self) -> timedelta:
        now = datetime.now(tz=timezone.utc)
        if now >= self.expires_at:
            return timedelta(seconds=0)
        return self.expires_at - now


@dataclass(frozen=True)
class QuizScore:
    score: float
    max_score: float
    percentage: float
    passed: bool
    per_question: Dict[str, float]

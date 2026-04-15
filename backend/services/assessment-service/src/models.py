from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class AssessmentStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    RETIRED = "retired"


class AssessmentType(str, Enum):
    QUIZ = "quiz"
    EXAM = "exam"
    ASSIGNMENT = "assignment"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class QuestionItem:
    question_id: str
    tenant_id: str
    prompt: str
    question_type: str
    options: List[str]
    correct_answer: str
    objective_tag: str
    difficulty: Difficulty
    points: float
    metadata: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class QuestionBank:
    question_bank_id: str
    tenant_id: str
    name: str
    description: str
    course_id: Optional[str]
    created_by: str
    questions: List[QuestionItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class GradingRule:
    grading_rule_id: str
    tenant_id: str
    name: str
    pass_threshold: float
    negative_marking_ratio: float
    max_attempts: int
    allow_partial_credit: bool
    late_penalty_percent: float
    created_by: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Assessment:
    assessment_id: str
    tenant_id: str
    course_id: str
    lesson_id: Optional[str]
    title: str
    description: str
    assessment_type: AssessmentType
    time_limit_minutes: int
    question_bank_id: Optional[str]
    grading_rule_id: Optional[str]
    status: AssessmentStatus = AssessmentStatus.DRAFT
    published_at: Optional[datetime] = None
    created_by: str = "system"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AuditEvent:
    event_type: str
    entity_id: str
    tenant_id: str
    payload: Dict
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AssessmentAttempt:
    attempt_id: str
    assessment_id: str
    tenant_id: str
    user_id: str
    course_id: str
    score_percent: float
    passed: bool
    attempted_at: datetime = field(default_factory=datetime.utcnow)

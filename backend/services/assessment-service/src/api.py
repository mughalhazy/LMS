from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .repository import InMemoryAssessmentRepository
from .service import AssessmentService

repository = InMemoryAssessmentRepository()
service = AssessmentService(repository)


class AssessmentCreateRequest(BaseModel):
    tenant_id: str
    course_id: str
    lesson_id: Optional[str] = None
    title: str
    description: str
    assessment_type: str
    time_limit_minutes: int = Field(ge=1)
    question_bank_id: Optional[str] = None
    grading_rule_id: Optional[str] = None
    created_by: str


class QuestionBankCreateRequest(BaseModel):
    tenant_id: str
    name: str
    description: str
    course_id: Optional[str] = None
    created_by: str


class QuestionBankItemCreateRequest(BaseModel):
    tenant_id: str
    prompt: str
    question_type: str
    options: List[str] = Field(default_factory=list)
    correct_answer: str
    objective_tag: str
    difficulty: str
    points: float = Field(gt=0)
    metadata: Optional[Dict[str, str]] = None


class GradingRuleCreateRequest(BaseModel):
    tenant_id: str
    name: str
    pass_threshold: float = Field(ge=0, le=100)
    negative_marking_ratio: float = Field(ge=0, le=1)
    max_attempts: int = Field(ge=1)
    allow_partial_credit: bool
    late_penalty_percent: float = Field(ge=0, le=100)
    created_by: str


class AssessmentPublishRequest(BaseModel):
    tenant_id: str
    published_by: str


# Endpoint handlers designed for framework adapters


def create_assessment(payload: AssessmentCreateRequest) -> Dict:
    return service.create_assessment(**payload.model_dump())


def create_question_bank(payload: QuestionBankCreateRequest) -> Dict:
    return service.create_question_bank(**payload.model_dump())


def add_question_item(question_bank_id: str, payload: QuestionBankItemCreateRequest) -> Dict:
    return service.add_question_bank_item(question_bank_id=question_bank_id, **payload.model_dump())


def create_grading_rule(payload: GradingRuleCreateRequest) -> Dict:
    return service.create_grading_rule(**payload.model_dump())


def publish_assessment(assessment_id: str, payload: AssessmentPublishRequest) -> Dict:
    return service.publish_assessment(assessment_id=assessment_id, **payload.model_dump())


def list_assessments(tenant_id: str) -> List[Dict]:
    return service.list_assessments(tenant_id=tenant_id)

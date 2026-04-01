from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class InteractionType(str, Enum):
    EXPLANATION = "explanation"
    QUESTION = "question"
    CONTEXTUAL_TUTORING = "contextual_tutoring"
    GUIDANCE = "guidance"


class LearningContext(BaseModel):
    course_id: str
    lesson_id: str | None = None
    skill_level: str | None = None
    preferred_language: str = "en"
    struggling_topics: list[str] = Field(default_factory=list)


class BaseTutorRequest(BaseModel):
    tenant_id: str
    learner_id: str
    context: LearningContext


class ConceptExplanationRequest(BaseTutorRequest):
    concept: str
    learner_goal: str | None = None


class LearnerQuestionRequest(BaseTutorRequest):
    question: str
    prior_answer: str | None = None


class ContextualTutoringRequest(BaseTutorRequest):
    activity_type: str
    learner_submission: str
    expected_outcome: str


class LearningGuidanceRequest(BaseTutorRequest):
    current_progress: float = Field(ge=0, le=100)
    time_available_minutes: int = Field(gt=0)
    target_date: datetime | None = None


class TutorResponse(BaseModel):
    session_id: str
    interaction_id: str
    interaction_type: InteractionType
    message: str
    follow_up_actions: list[str] = Field(default_factory=list)
    recommended_resources: list[str] = Field(default_factory=list)
    created_at: datetime


class TutorSessionSummary(BaseModel):
    session_id: str
    tenant_id: str
    learner_id: str
    context: LearningContext
    interactions: list[TutorResponse] = Field(default_factory=list)


class AnalyticsTutorRequest(BaseTutorRequest):
    completion_rate: float = Field(ge=0, le=100)
    average_sentiment: float
    trend_direction: str = "stable"
    suggested_focus: str = "practice-coaching"


class LearningInsightTutorRequest(BaseTutorRequest):
    dropout_risk_score: float = Field(ge=0, le=100)
    engagement_risk_score: float = Field(ge=0, le=100)
    predicted_performance_score: float = Field(ge=0, le=100)
    risk_band: str = "low"
    suggested_focus: str = "practice-coaching"

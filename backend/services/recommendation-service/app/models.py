from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List
from uuid import uuid4

from pydantic import BaseModel, Field


class RecommendationType(str, Enum):
    PERSONALIZED_COURSE = "personalized_course"
    SKILL_GAP = "skill_gap"
    LEARNING_PATH = "learning_path"
    BEHAVIORAL = "behavioral"


class RecommendationRationale(BaseModel):
    tags: List[str] = Field(default_factory=list)
    explanation: str


class RecommendationBase(BaseModel):
    recommendation_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    learner_id: str
    score: float = Field(ge=0.0, le=1.0)
    recommendation_type: RecommendationType
    rationale: RecommendationRationale
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PersonalizedCourseRecommendation(RecommendationBase):
    recommendation_type: RecommendationType = RecommendationType.PERSONALIZED_COURSE
    course_id: str
    estimated_minutes: int = Field(gt=0)
    difficulty_tier: str


class SkillGapRecommendation(RecommendationBase):
    recommendation_type: RecommendationType = RecommendationType.SKILL_GAP
    skill_id: str
    current_level: float = Field(ge=0.0, le=1.0)
    target_level: float = Field(ge=0.0, le=1.0)
    severity: str
    interventions: List[str] = Field(default_factory=list)


class LearningPathSuggestion(RecommendationBase):
    recommendation_type: RecommendationType = RecommendationType.LEARNING_PATH
    learning_path_id: str
    ordered_course_ids: List[str] = Field(default_factory=list)
    estimated_completion_days: int = Field(gt=0)


class BehavioralLearningRecommendation(RecommendationBase):
    recommendation_type: RecommendationType = RecommendationType.BEHAVIORAL
    behavior_signal: str
    action: str
    habit_goal: str


class LearnerRecommendationBundle(BaseModel):
    learner_id: str
    personalized_courses: List[PersonalizedCourseRecommendation] = Field(default_factory=list)
    skill_gaps: List[SkillGapRecommendation] = Field(default_factory=list)
    learning_paths: List[LearningPathSuggestion] = Field(default_factory=list)
    behavioral: List[BehavioralLearningRecommendation] = Field(default_factory=list)

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field

from .models import (
    BehavioralLearningRecommendation,
    LearnerRecommendationBundle,
    LearningPathSuggestion,
    PersonalizedCourseRecommendation,
    SkillGapRecommendation,
)


class PersonalizedRecommendationRequest(BaseModel):
    tenant_id: str
    learner_id: str
    target_skills: List[str] = Field(default_factory=list)
    preferred_modalities: List[str] = Field(default_factory=list)
    available_minutes_per_week: int = Field(default=120, gt=0)


class SkillGapRecommendationRequest(BaseModel):
    tenant_id: str
    learner_id: str
    required_skills: List[str] = Field(default_factory=list)
    current_skill_levels: dict[str, float] = Field(default_factory=dict)
    target_skill_levels: dict[str, float] = Field(default_factory=dict)


class LearningPathSuggestionRequest(BaseModel):
    tenant_id: str
    learner_id: str
    goal: str
    available_hours_per_week: int = Field(default=4, gt=0)
    mandatory_course_ids: List[str] = Field(default_factory=list)


class BehavioralRecommendationRequest(BaseModel):
    tenant_id: str
    learner_id: str
    activity_streak_days: int = Field(default=0, ge=0)
    average_session_minutes: int = Field(default=0, ge=0)
    dropoff_rate: float = Field(default=0.0, ge=0.0, le=1.0)


class PersonalizedRecommendationResponse(BaseModel):
    items: List[PersonalizedCourseRecommendation]


class SkillGapRecommendationResponse(BaseModel):
    items: List[SkillGapRecommendation]


class LearningPathSuggestionResponse(BaseModel):
    items: List[LearningPathSuggestion]


class BehavioralRecommendationResponse(BaseModel):
    items: List[BehavioralLearningRecommendation]


class LearnerRecommendationBundleResponse(BaseModel):
    bundle: LearnerRecommendationBundle


class AnalyticsRecommendationRequest(BaseModel):
    tenant_id: str
    learner_id: str
    completion_rate: float = Field(ge=0, le=100)
    engagement_score: float = Field(ge=0, le=100)
    average_sentiment: float
    trend_direction: str = "stable"

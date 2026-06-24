"""API schemas for review-service."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field


class SubmitReviewRequest(BaseModel):
    course_id: str
    learner_id: str
    rating: int = Field(ge=1, le=5)
    body: str = Field(min_length=1)


class ReviewResponse(BaseModel):
    review_id: str
    tenant_id: str
    course_id: str
    learner_id: str
    rating: int
    body: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RatingSummaryResponse(BaseModel):
    course_id: str
    average_rating: float
    total_reviews: int
    distribution: Dict[str, int]

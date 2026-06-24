"""API schemas for the quiz-engine service."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class QuizOptionIn(BaseModel):
    option_id: str
    text: str
    is_correct: bool = False


class QuizQuestionIn(BaseModel):
    question_id: str
    prompt: str
    question_type: str  # single_choice | multiple_choice | true_false
    options: List[QuizOptionIn]
    points: float = 1.0


class RegisterQuizRequest(BaseModel):
    quiz_id: str
    title: str
    questions: List[QuizQuestionIn] = Field(min_length=1)
    duration_seconds: int = Field(gt=0)
    randomize_questions: bool = True


class StartSessionRequest(BaseModel):
    user_id: str
    seed: Optional[int] = None
    quiz_id: Optional[str] = None  # B03-002: included when using spec path POST /api/v1/quiz-engine/sessions


class SubmitAnswerRequest(BaseModel):
    question_id: str
    option_ids: List[str]


class SubmitQuizRequest(BaseModel):
    submitted_at: Optional[datetime] = None

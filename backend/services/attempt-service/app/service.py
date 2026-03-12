from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict
from uuid import uuid4

from fastapi import HTTPException

from .schemas import (
    AnswerSubmission,
    AttemptAnswerResponse,
    AttemptHistoryResponse,
    AttemptResponse,
    AttemptStatus,
    RecordAnswersRequest,
    ScoreAttemptRequest,
    StartAttemptRequest,
)


@dataclass
class AttemptAnswerRecord:
    question_id: str
    response: str | list[str] | dict[str, str | int | float | bool | None]
    is_final: bool
    updated_at: datetime


@dataclass
class AttemptRecord:
    attempt_id: str
    tenant_id: str
    learner_id: str
    assessment_id: str
    enrollment_id: str | None
    course_id: str | None
    attempt_number: int
    status: AttemptStatus
    started_by: str
    started_at: datetime
    submitted_at: datetime | None = None
    scored_at: datetime | None = None
    scored_by: str | None = None
    answers: Dict[str, AttemptAnswerRecord] = field(default_factory=dict)
    max_score: float | None = None
    awarded_score: float | None = None
    passing_score: float | None = None
    passed: bool | None = None
    feedback: str | None = None


class AttemptService:
    """Tenant-scoped assessment attempt service for learner submissions and scoring."""

    def __init__(self) -> None:
        self._attempts: dict[str, AttemptRecord] = {}
        self._attempt_order: dict[tuple[str, str, str], list[str]] = {}

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def start_attempt(self, request: StartAttemptRequest) -> AttemptResponse:
        key = (request.tenant_id, request.learner_id, request.assessment_id)
        attempt_ids = self._attempt_order.setdefault(key, [])
        attempt_number = len(attempt_ids) + 1

        attempt = AttemptRecord(
            attempt_id=str(uuid4()),
            tenant_id=request.tenant_id,
            learner_id=request.learner_id,
            assessment_id=request.assessment_id,
            enrollment_id=request.enrollment_id,
            course_id=request.course_id,
            attempt_number=attempt_number,
            status=AttemptStatus.IN_PROGRESS,
            started_by=request.started_by,
            started_at=self._now(),
        )
        self._attempts[attempt.attempt_id] = attempt
        attempt_ids.append(attempt.attempt_id)
        return self._to_response(attempt)

    def record_answers(self, attempt_id: str, request: RecordAnswersRequest) -> AttemptResponse:
        attempt = self._get_tenant_attempt(request.tenant_id, attempt_id)
        if attempt.status == AttemptStatus.SCORED:
            raise HTTPException(status_code=409, detail="Scored attempts are immutable")

        for answer in request.answers:
            self._upsert_answer(attempt, answer)

        if request.answers:
            attempt.status = AttemptStatus.SUBMITTED
            attempt.submitted_at = self._now()
        return self._to_response(attempt)

    def score_attempt(self, attempt_id: str, request: ScoreAttemptRequest) -> AttemptResponse:
        attempt = self._get_tenant_attempt(request.tenant_id, attempt_id)

        if request.awarded_score > request.max_score:
            raise HTTPException(status_code=422, detail="awarded_score cannot exceed max_score")
        if request.passing_score > request.max_score:
            raise HTTPException(status_code=422, detail="passing_score cannot exceed max_score")

        attempt.status = AttemptStatus.SCORED
        attempt.max_score = request.max_score
        attempt.awarded_score = request.awarded_score
        attempt.passing_score = request.passing_score
        attempt.passed = request.awarded_score >= request.passing_score
        attempt.feedback = request.feedback
        attempt.scored_by = request.scored_by
        attempt.scored_at = self._now()
        if attempt.submitted_at is None:
            attempt.submitted_at = attempt.scored_at

        return self._to_response(attempt)

    def get_attempt(self, tenant_id: str, attempt_id: str) -> AttemptResponse:
        attempt = self._get_tenant_attempt(tenant_id, attempt_id)
        return self._to_response(attempt)

    def get_attempt_history(
        self,
        *,
        tenant_id: str,
        learner_id: str,
        assessment_id: str | None,
    ) -> AttemptHistoryResponse:
        attempts = [
            attempt
            for attempt in self._attempts.values()
            if attempt.tenant_id == tenant_id and attempt.learner_id == learner_id
        ]
        if assessment_id:
            attempts = [attempt for attempt in attempts if attempt.assessment_id == assessment_id]

        attempts.sort(key=lambda item: item.started_at)
        return AttemptHistoryResponse(
            tenant_id=tenant_id,
            learner_id=learner_id,
            assessment_id=assessment_id,
            attempts=[self._to_response(attempt) for attempt in attempts],
        )

    def _upsert_answer(self, attempt: AttemptRecord, submission: AnswerSubmission) -> None:
        attempt.answers[submission.question_id] = AttemptAnswerRecord(
            question_id=submission.question_id,
            response=submission.response,
            is_final=submission.is_final,
            updated_at=self._now(),
        )

    def _get_tenant_attempt(self, tenant_id: str, attempt_id: str) -> AttemptRecord:
        attempt = self._attempts.get(attempt_id)
        if not attempt or attempt.tenant_id != tenant_id:
            raise HTTPException(status_code=404, detail="Attempt not found for tenant")
        return attempt

    def _to_response(self, attempt: AttemptRecord) -> AttemptResponse:
        ordered_answers = sorted(attempt.answers.values(), key=lambda item: item.question_id)
        return AttemptResponse(
            attempt_id=attempt.attempt_id,
            tenant_id=attempt.tenant_id,
            learner_id=attempt.learner_id,
            assessment_id=attempt.assessment_id,
            enrollment_id=attempt.enrollment_id,
            course_id=attempt.course_id,
            attempt_number=attempt.attempt_number,
            status=attempt.status,
            started_by=attempt.started_by,
            started_at=attempt.started_at,
            submitted_at=attempt.submitted_at,
            scored_at=attempt.scored_at,
            scored_by=attempt.scored_by,
            answers=[
                AttemptAnswerResponse(
                    question_id=answer.question_id,
                    response=answer.response,
                    is_final=answer.is_final,
                    updated_at=answer.updated_at,
                )
                for answer in ordered_answers
            ],
            max_score=attempt.max_score,
            awarded_score=attempt.awarded_score,
            passing_score=attempt.passing_score,
            passed=attempt.passed,
            feedback=attempt.feedback,
        )

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from random import Random
from typing import Dict, List, Optional
from uuid import uuid4

from .models import QuizDefinition, QuizQuestion, QuizScore, QuizSession


class QuizEngineError(Exception):
    pass


class NotFoundError(QuizEngineError):
    pass


class ValidationError(QuizEngineError):
    pass


class SessionExpiredError(QuizEngineError):
    pass


class QuizEngine:
    """In-memory quiz engine implementing rendering, randomization, timer, and scoring."""

    def __init__(self, pass_threshold_percent: float = 70.0) -> None:
        self.pass_threshold_percent = pass_threshold_percent
        self._quizzes: Dict[str, QuizDefinition] = {}
        self._sessions: Dict[str, QuizSession] = {}

    def register_quiz(self, quiz: QuizDefinition) -> None:
        if quiz.duration_seconds <= 0:
            raise ValidationError("Quiz duration must be positive")
        if not quiz.questions:
            raise ValidationError("Quiz must include at least one question")
        self._quizzes[quiz.quiz_id] = quiz

    def start_session(
        self,
        tenant_id: str,
        quiz_id: str,
        user_id: str,
        seed: Optional[int] = None,
        started_at: Optional[datetime] = None,
    ) -> QuizSession:
        quiz = self._get_quiz(tenant_id, quiz_id)

        question_ids = [q.question_id for q in quiz.questions]
        if quiz.randomize_questions:
            rng = Random(seed)
            rng.shuffle(question_ids)

        start = started_at or datetime.now(tz=timezone.utc)
        session = QuizSession(
            session_id=str(uuid4()),
            quiz_id=quiz.quiz_id,
            tenant_id=tenant_id,
            user_id=user_id,
            ordered_question_ids=question_ids,
            started_at=start,
            expires_at=start + timedelta(seconds=quiz.duration_seconds),
        )
        self._sessions[session.session_id] = session
        return session

    def render_quiz(self, session_id: str) -> Dict[str, object]:
        session = self._get_session(session_id)
        quiz = self._get_quiz(session.tenant_id, session.quiz_id)
        question_lookup = {q.question_id: q for q in quiz.questions}

        questions = []
        for question_id in session.ordered_question_ids:
            question = question_lookup[question_id]
            questions.append(
                {
                    "question_id": question.question_id,
                    "prompt": question.prompt,
                    "question_type": question.question_type.value,
                    "points": question.points,
                    "options": [
                        {"option_id": opt.option_id, "text": opt.text}
                        for opt in question.options
                    ],
                }
            )

        return {
            "session_id": session.session_id,
            "quiz_id": quiz.quiz_id,
            "title": quiz.title,
            "time_remaining_seconds": int(session.time_remaining().total_seconds()),
            "submitted": session.is_submitted,
            "questions": questions,
        }

    def submit_answer(self, session_id: str, question_id: str, option_ids: List[str]) -> None:
        session = self._get_session(session_id)
        if session.is_submitted:
            raise ValidationError("Session already submitted")
        if session.is_expired:
            raise SessionExpiredError("Quiz timer has expired")
        if question_id not in session.ordered_question_ids:
            raise ValidationError("Question is not part of the quiz")

        # normalize for deterministic scoring
        session.answers[question_id] = sorted(set(option_ids))

    def submit_quiz(
        self,
        session_id: str,
        submitted_at: Optional[datetime] = None,
    ) -> QuizScore:
        session = self._get_session(session_id)
        if session.is_submitted:
            raise ValidationError("Session already submitted")

        submission_time = submitted_at or datetime.now(tz=timezone.utc)
        session.submitted_at = submission_time
        return self.score_session(session_id)

    def score_session(self, session_id: str) -> QuizScore:
        session = self._get_session(session_id)
        quiz = self._get_quiz(session.tenant_id, session.quiz_id)

        question_lookup: Dict[str, QuizQuestion] = {q.question_id: q for q in quiz.questions}
        total_points = 0.0
        earned_points = 0.0
        per_question: Dict[str, float] = {}

        for question_id in session.ordered_question_ids:
            question = question_lookup[question_id]
            total_points += question.points

            correct_option_ids = sorted(
                [option.option_id for option in question.options if option.is_correct]
            )
            selected_option_ids = session.answers.get(question_id, [])

            if selected_option_ids == correct_option_ids:
                per_question[question_id] = question.points
                earned_points += question.points
            else:
                per_question[question_id] = 0.0

        percentage = 0.0 if total_points == 0 else (earned_points / total_points) * 100
        return QuizScore(
            score=earned_points,
            max_score=total_points,
            percentage=percentage,
            passed=percentage >= self.pass_threshold_percent,
            per_question=per_question,
        )

    def _get_quiz(self, tenant_id: str, quiz_id: str) -> QuizDefinition:
        quiz = self._quizzes.get(quiz_id)
        if not quiz or quiz.tenant_id != tenant_id:
            raise NotFoundError("Quiz not found")
        return quiz

    def _get_session(self, session_id: str) -> QuizSession:
        session = self._sessions.get(session_id)
        if not session:
            raise NotFoundError("Session not found")
        return session

from __future__ import annotations

import secrets
from typing import Dict, List, Optional

from .models import ExamDefinition, ExamSession


class InMemoryExamStore:
    def __init__(self) -> None:
        self._exams: Dict[str, ExamDefinition] = {}
        self._sessions: Dict[str, ExamSession] = {}

    def save_exam(self, exam: ExamDefinition) -> None:
        self._exams[exam.exam_id] = exam

    def get_exam(self, exam_id: str) -> Optional[ExamDefinition]:
        return self._exams.get(exam_id)

    def save_session(self, session: ExamSession) -> None:
        self._sessions[session.session_id] = session

    def get_session(self, session_id: str) -> Optional[ExamSession]:
        return self._sessions.get(session_id)

    def count_attempts(self, exam_id: str, candidate_id: str) -> int:
        return sum(1 for s in self._sessions.values()
                   if s.exam_id == exam_id and s.candidate_id == candidate_id
                   and s.status not in ("timed_out",))

    def new_id(self, prefix: str = "") -> str:
        return f"{prefix}-{secrets.token_urlsafe(8)}" if prefix else secrets.token_urlsafe(10)

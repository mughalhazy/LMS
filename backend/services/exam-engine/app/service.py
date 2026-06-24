from __future__ import annotations

import secrets
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

from .models import ExamDefinition, ExamSession, ProctorConfig
from .store import InMemoryExamStore

# B03-005: best-effort event emission for exam lifecycle events
_BACKEND_ROOT = Path(__file__).resolve().parents[3]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

try:
    from services.shared.events.envelope import publish_event as _publish_event
except ImportError:
    _publish_event = None  # type: ignore[assignment]


def _emit(event_type: str, tenant_id: str, payload: Dict[str, Any]) -> None:
    if _publish_event is None:
        return
    try:
        _publish_event(event_type=event_type, producer_service="exam-engine", tenant_id=tenant_id, payload=payload)
    except Exception:
        pass  # best-effort — never fail the caller


class ExamEngineService:
    def __init__(self, store: InMemoryExamStore) -> None:
        self.store = store

    def register_exam(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        pc = body.get("proctor_config", {})
        exam = ExamDefinition(
            exam_id=body.get("exam_id") or self.store.new_id("exam"),
            tenant_id=body.get("tenant_id", ""),
            title=body.get("title", ""),
            assessment_ref=body.get("assessment_ref", ""),
            duration_seconds=int(body.get("duration_seconds", 3600)),
            proctor_config=ProctorConfig(
                single_window=pc.get("single_window", True),
                copy_paste_disabled=pc.get("copy_paste_disabled", True),
                time_per_question_seconds=pc.get("time_per_question_seconds"),
                ip_allowlist=pc.get("ip_allowlist", []),
                max_tab_switches=pc.get("max_tab_switches", 0),
            ),
            max_attempts=int(body.get("max_attempts", 1)),
            passing_score_pct=float(body.get("passing_score_pct", 60.0)),
        )
        self.store.save_exam(exam)
        return 201, self._serialize_exam(exam)

    def start_exam(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        exam_id = body.get("exam_id", "")
        candidate_id = body.get("candidate_id", "")
        tenant_id = body.get("tenant_id", "")

        exam = self.store.get_exam(exam_id)
        if not exam or exam.tenant_id != tenant_id:
            return 404, {"error": "exam_not_found"}

        attempts_used = self.store.count_attempts(exam_id, candidate_id)
        if attempts_used >= exam.max_attempts:
            return 409, {"error": "max_attempts_exceeded",
                          "max_attempts": exam.max_attempts, "used": attempts_used}

        now = datetime.now(timezone.utc)
        session = ExamSession(
            session_id=self.store.new_id("esess"),
            exam_id=exam_id,
            attempt_id=body.get("attempt_id", self.store.new_id("att")),
            tenant_id=tenant_id,
            candidate_id=candidate_id,
            status="in_progress",
            started_at=now,
            expires_at=now + timedelta(seconds=exam.duration_seconds),
            resume_token=secrets.token_urlsafe(16),
        )
        self.store.save_session(session)
        # B03-005: spec CAP-ATTEMPT-LIFECYCLE — emit exam.attempt_started
        _emit("exam.attempt_started", tenant_id, {
            "session_id": session.session_id,
            "exam_id": exam_id,
            "candidate_id": candidate_id,
            "attempt_id": session.attempt_id,
        })
        return 201, {
            "session_id": session.session_id,
            "exam_id": exam_id,
            "status": session.status,
            "started_at": session.started_at.isoformat(),
            "expires_at": session.expires_at.isoformat(),
            "duration_seconds": exam.duration_seconds,
            "resume_token": session.resume_token,
            "proctor_rules": {
                "single_window": exam.proctor_config.single_window,
                "copy_paste_disabled": exam.proctor_config.copy_paste_disabled,
                "max_tab_switches": exam.proctor_config.max_tab_switches,
            },
        }

    def get_session(self, session_id: str, tenant_id: str) -> Tuple[int, Dict[str, Any]]:
        session = self.store.get_session(session_id)
        if not session or session.tenant_id != tenant_id:
            return 404, {"error": "session_not_found"}
        self._check_expiry(session)
        return 200, self._serialize_session(session)

    def submit_answer(self, session_id: str, tenant_id: str, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        session = self.store.get_session(session_id)
        if not session or session.tenant_id != tenant_id:
            return 404, {"error": "session_not_found"}
        if session.status != "in_progress":
            return 409, {"error": "session_not_in_progress", "status": session.status}
        if self._is_expired(session):
            self._timeout_session(session)
            return 410, {"error": "session_expired"}

        question_id = body.get("question_id", "")
        answer = body.get("answer")
        session.answers[question_id] = answer
        self.store.save_session(session)
        return 200, {"session_id": session_id, "question_id": question_id, "recorded": True}

    def submit_exam(self, session_id: str, tenant_id: str) -> Tuple[int, Dict[str, Any]]:
        session = self.store.get_session(session_id)
        if not session or session.tenant_id != tenant_id:
            return 404, {"error": "session_not_found"}
        if session.status != "in_progress":
            return 409, {"error": "session_not_in_progress", "status": session.status}

        now = datetime.now(timezone.utc)
        session.status = "submitted"
        session.submitted_at = now
        self.store.save_session(session)
        # B03-005: spec CAP-ATTEMPT-LIFECYCLE — emit exam.submitted
        _emit("exam.submitted", session.tenant_id, {
            "session_id": session_id,
            "exam_id": session.exam_id,
            "candidate_id": session.candidate_id,
            "answer_count": len(session.answers),
        })
        return 200, {
            "session_id": session_id, "status": "submitted",
            "submitted_at": now.isoformat(),
            "answer_count": len(session.answers),
            "next_step": "grading_pending",
        }

    def record_proctor_event(self, session_id: str, tenant_id: str, event: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        session = self.store.get_session(session_id)
        if not session or session.tenant_id != tenant_id:
            return 404, {"error": "session_not_found"}
        session.proctor_events.append({**event, "recorded_at": datetime.now(timezone.utc).isoformat()})
        self.store.save_session(session)
        return 200, {"session_id": session_id, "proctor_event_count": len(session.proctor_events)}

    def _check_expiry(self, session: ExamSession) -> None:
        if session.status == "in_progress" and self._is_expired(session):
            self._timeout_session(session)

    def _is_expired(self, session: ExamSession) -> bool:
        now = datetime.now(timezone.utc)
        expires = session.expires_at.replace(tzinfo=timezone.utc) if session.expires_at.tzinfo is None else session.expires_at
        return now > expires

    def _timeout_session(self, session: ExamSession) -> None:
        session.status = "timed_out"
        session.timed_out_at = datetime.now(timezone.utc)
        self.store.save_session(session)
        # B03-005: spec CAP-ATTEMPT-LIFECYCLE — emit exam.timed_out
        _emit("exam.timed_out", session.tenant_id, {
            "session_id": session.session_id,
            "exam_id": session.exam_id,
            "candidate_id": session.candidate_id,
        })

    def _serialize_exam(self, e: ExamDefinition) -> Dict[str, Any]:
        return {"exam_id": e.exam_id, "title": e.title, "assessment_ref": e.assessment_ref,
                "duration_seconds": e.duration_seconds, "max_attempts": e.max_attempts,
                "passing_score_pct": e.passing_score_pct,
                "proctor_config": {"single_window": e.proctor_config.single_window,
                                    "copy_paste_disabled": e.proctor_config.copy_paste_disabled}}

    def _serialize_session(self, s: ExamSession) -> Dict[str, Any]:
        return {"session_id": s.session_id, "exam_id": s.exam_id, "status": s.status,
                "candidate_id": s.candidate_id, "answer_count": len(s.answers),
                "proctor_event_count": len(s.proctor_events),
                "started_at": s.started_at.isoformat(),
                "expires_at": s.expires_at.isoformat()}

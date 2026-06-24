from __future__ import annotations
import pytest
from datetime import datetime, timedelta, timezone
from app.service import ExamEngineService
from app.store import InMemoryExamStore


def _svc() -> ExamEngineService:
    return ExamEngineService(InMemoryExamStore())


def _exam(svc: ExamEngineService, **kwargs) -> dict:
    body = {"tenant_id": "t1", "title": "Python Cert Exam", "assessment_ref": "assess-1",
            "duration_seconds": 3600, "max_attempts": 2, "passing_score_pct": 70.0,
            "proctor_config": {"single_window": True, "copy_paste_disabled": True}, **kwargs}
    _, e = svc.register_exam(body)
    return e


def _session(svc: ExamEngineService, exam_id: str, **kwargs) -> dict:
    body = {"tenant_id": "t1", "exam_id": exam_id, "candidate_id": "c1", **kwargs}
    _, s = svc.start_exam(body)
    return s


def test_register_exam():
    svc = _svc()
    status, body = svc.register_exam({"tenant_id": "t1", "title": "Cert",
                                       "assessment_ref": "a1", "duration_seconds": 3600,
                                       "proctor_config": {}})
    assert status == 201
    assert body["proctor_config"]["single_window"] is True


def test_start_exam():
    svc = _svc()
    e = _exam(svc)
    status, body = svc.start_exam({"tenant_id": "t1", "exam_id": e["exam_id"], "candidate_id": "c1"})
    assert status == 201
    assert body["status"] == "in_progress"
    assert "resume_token" in body
    assert "proctor_rules" in body


def test_max_attempts_enforced():
    svc = _svc()
    e = _exam(svc, max_attempts=1)
    svc.start_exam({"tenant_id": "t1", "exam_id": e["exam_id"], "candidate_id": "c1"})
    status, body = svc.start_exam({"tenant_id": "t1", "exam_id": e["exam_id"], "candidate_id": "c1"})
    assert status == 409
    assert "max_attempts_exceeded" in body["error"]


def test_submit_answer():
    svc = _svc()
    e = _exam(svc)
    s = _session(svc, e["exam_id"])
    status, body = svc.submit_answer(s["session_id"], "t1",
                                      {"question_id": "q1", "answer": "option_a"})
    assert status == 200
    assert body["recorded"] is True


def test_submit_exam():
    svc = _svc()
    e = _exam(svc)
    s = _session(svc, e["exam_id"])
    svc.submit_answer(s["session_id"], "t1", {"question_id": "q1", "answer": "b"})
    status, body = svc.submit_exam(s["session_id"], "t1")
    assert status == 200
    assert body["status"] == "submitted"


def test_cannot_answer_after_submit():
    svc = _svc()
    e = _exam(svc)
    s = _session(svc, e["exam_id"])
    svc.submit_exam(s["session_id"], "t1")
    status, _ = svc.submit_answer(s["session_id"], "t1", {"question_id": "q2", "answer": "c"})
    assert status == 409


def test_proctor_event_recorded():
    svc = _svc()
    e = _exam(svc)
    s = _session(svc, e["exam_id"])
    status, body = svc.record_proctor_event(s["session_id"], "t1",
                                             {"event_type": "tab_switch", "count": 1})
    assert status == 200
    assert body["proctor_event_count"] == 1


def test_exam_not_found():
    svc = _svc()
    status, _ = svc.start_exam({"tenant_id": "t1", "exam_id": "nonexistent", "candidate_id": "c1"})
    assert status == 404

from __future__ import annotations
import pytest
from app.service import InteractionLayerService
from app.models import MANDATORY_MESSAGE_TYPES, PERSONA_COMMANDS


def _svc() -> InteractionLayerService:
    return InteractionLayerService()


def test_create_session():
    svc = _svc()
    status, body = svc.get_or_create_session("u1", "t1", "learner")
    assert status == 200
    assert body["persona"] == "learner"


def test_session_idempotent():
    svc = _svc()
    _, s1 = svc.get_or_create_session("u1", "t1", "learner")
    _, s2 = svc.get_or_create_session("u1", "t1", "learner")
    assert s1["session_id"] == s2["session_id"]


def test_build_action_message_all_mandatory_types():
    svc = _svc()
    for message_type in MANDATORY_MESSAGE_TYPES:
        status, body = svc.build_action_message({"user_id": "u1", "tenant_id": "t1",
                                                   "message_type": message_type, "context": {}})
        assert status == 200
        # BC-INT-01: every message must have at least one action option
        assert len(body["action_options"]) >= 1


def test_unknown_message_type_rejected():
    svc = _svc()
    status, _ = svc.build_action_message({"message_type": "unknown_type"})
    assert status == 400


def test_handle_valid_reply():
    svc = _svc()
    status, body = svc.handle_reply({"user_id": "u1", "tenant_id": "t1",
                                      "reply": "PAY", "action_id": "a1"})
    assert status == 200
    assert body["dispatched_to"] == "commerce.initiate_payment"


def test_handle_reply_idempotent():
    svc = _svc()
    svc.handle_reply({"user_id": "u1", "tenant_id": "t1", "reply": "PAY", "action_id": "a1"})
    status, body = svc.handle_reply({"user_id": "u1", "tenant_id": "t1", "reply": "PAY", "action_id": "a1"})
    # BC-INT-01: duplicate replies must not trigger duplicate actions
    assert body["status"] == "already_handled"


def test_unrecognised_reply():
    svc = _svc()
    status, _ = svc.handle_reply({"reply": "BLAH", "action_id": "a2"})
    assert status == 422


def test_persona_commands_all_personas():
    svc = _svc()
    for persona in PERSONA_COMMANDS:
        status, body = svc.get_persona_commands(persona)
        assert status == 200
        assert len(body["commands"]) >= 5


def test_attendance_reply_codes():
    svc = _svc()
    for code, expected_handler in [("1", "attendance.mark_present"),
                                    ("2", "attendance.mark_absent"),
                                    ("3", "attendance.mark_late")]:
        _, body = svc.handle_reply({"reply": code, "action_id": f"a-{code}"})
        assert body["dispatched_to"] == expected_handler

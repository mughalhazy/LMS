from __future__ import annotations
import pytest
from app.service import OfflineSyncService


def _svc() -> OfflineSyncService:
    return OfflineSyncService()


def test_request_download():
    svc = _svc()
    status, body = svc.request_download({"user_id": "u1", "tenant_id": "t1",
                                          "content_id": "lesson-1", "content_type": "lesson"})
    assert status == 201
    assert body["status"] == "available"


def test_queue_progress_event():
    svc = _svc()
    status, body = svc.queue_progress_event({"user_id": "u1", "tenant_id": "t1",
                                              "event_type": "lesson.completed",
                                              "payload": {}, "idempotency_key": "idk-1"})
    assert status == 201
    assert body["queued"] is True


def test_progress_event_idempotent():
    svc = _svc()
    svc.queue_progress_event({"user_id": "u1", "tenant_id": "t1", "event_type": "x",
                               "payload": {}, "idempotency_key": "idk-1"})
    svc.sync("u1", "t1")
    status, body = svc.queue_progress_event({"user_id": "u1", "tenant_id": "t1", "event_type": "x",
                                              "payload": {}, "idempotency_key": "idk-1"})
    assert body["status"] == "already_synced"


def test_queue_operator_action():
    svc = _svc()
    status, body = svc.queue_operator_action({"tenant_id": "t1", "operator_id": "op1",
                                               "action_type": "mark_attendance",
                                               "payload": {}, "idempotency_key": "op-idk-1"})
    assert status == 201
    assert body["action_type"] == "mark_attendance"


def test_invalid_operator_action_type():
    svc = _svc()
    status, _ = svc.queue_operator_action({"tenant_id": "t1", "operator_id": "op1",
                                            "action_type": "invalid_action", "payload": {}})
    assert status == 400


def test_sync_operator_actions_before_progress():
    svc = _svc()
    svc.queue_operator_action({"tenant_id": "t1", "operator_id": "op1",
                                "action_type": "mark_attendance", "payload": {},
                                "idempotency_key": "oa-1"})
    svc.queue_progress_event({"user_id": "u1", "tenant_id": "t1", "event_type": "lesson.completed",
                               "payload": {}, "idempotency_key": "pe-1"})
    status, body = svc.sync("u1", "t1")
    assert status == 200
    assert body["operator_actions_synced"] == 1
    assert body["progress_events_synced"] == 1


def test_sync_idempotent():
    svc = _svc()
    svc.queue_progress_event({"user_id": "u1", "tenant_id": "t1", "event_type": "x",
                               "payload": {}, "idempotency_key": "pe-1"})
    svc.sync("u1", "t1")
    _, body = svc.sync("u1", "t1")
    assert body["progress_events_synced"] == 0

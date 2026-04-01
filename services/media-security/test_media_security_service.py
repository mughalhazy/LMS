from __future__ import annotations

import importlib.util
import sys
from datetime import timedelta
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from shared.models.media_policy import MediaAccessPolicy

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "services/media-security/service.py"
_spec = importlib.util.spec_from_file_location("media_security_service_test_module", MODULE_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError("Unable to load media security service module")
_module = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _module
_spec.loader.exec_module(_module)

MediaSecurityService = _module.MediaSecurityService
PlaybackContext = _module.PlaybackContext


def _default_policy(service: MediaSecurityService, **overrides) -> MediaAccessPolicy:
    now = service._utc_now()
    payload = {
        "media_id": "media_1",
        "tenant_id": "tenant_secure",
        "user_id": "user_1",
        "capability_id": "course.write",
        "token_expiry": now + timedelta(minutes=10),
        "watermark_payload": {"watermark_profile_id": "forensic_v1"},
        "allowed_device_count": 1,
        "allowed_session_count": 1,
        "offline_allowed": False,
        "metadata": {"binding": {"bind_to_device": True, "bind_to_ip": True}},
    }
    payload.update(overrides)
    return MediaAccessPolicy(**payload)


def test_authorize_stream_access_issues_token_with_watermark_when_entitled() -> None:
    service = MediaSecurityService()
    context = PlaybackContext(
        tenant_id="tenant_secure",
        user_id="user_1",
        media_id="media_1",
        session_id="session_a",
        channel="web",
        device_id="device_x",
        ip_address="10.0.0.1",
    )

    authorization = service.authorize_stream_access(policy=_default_policy(service), context=context)

    assert authorization.decision == "allow"
    assert authorization.playback_token is not None
    assert authorization.watermark["watermark_required"] is True
    assert authorization.security_controls["tokenized_playback"] is True


def test_authorize_stream_access_fails_closed_when_entitlement_missing() -> None:
    service = MediaSecurityService()
    context = PlaybackContext(
        tenant_id="tenant_secure",
        user_id="user_1",
        media_id="media_1",
        session_id="session_a",
        channel="web",
        device_id="device_x",
        ip_address="10.0.0.1",
    )

    authorization = service.authorize_stream_access(
        policy=_default_policy(service, capability_id="nonexistent_media_capability"),
        context=context,
    )

    assert authorization.decision == "deny"
    assert authorization.reason_code == "ENTITLEMENT_DENIED"
    assert authorization.playback_token is None


def test_validate_device_session_blocks_limits_and_offline_policy() -> None:
    service = MediaSecurityService()
    first_context = PlaybackContext(
        tenant_id="tenant_secure",
        user_id="user_1",
        media_id="media_1",
        session_id="session_a",
        channel="web",
        device_id="device_x",
        ip_address="10.0.0.1",
    )
    second_context = PlaybackContext(
        tenant_id="tenant_secure",
        user_id="user_1",
        media_id="media_1",
        session_id="session_b",
        channel="web",
        device_id="device_y",
        ip_address="10.0.0.2",
        offline_request=True,
    )

    policy = _default_policy(service)
    first = service.authorize_stream_access(policy=policy, context=first_context)
    assert first.decision == "allow"

    reason = service.validate_device_session(policy=policy, context=second_context)
    assert reason in {"OFFLINE_PLAYBACK_DENIED", "SESSION_LIMIT_EXCEEDED", "DEVICE_LIMIT_EXCEEDED"}


def test_enforce_and_revoke_token_access() -> None:
    service = MediaSecurityService()
    context = PlaybackContext(
        tenant_id="tenant_secure",
        user_id="user_1",
        media_id="media_1",
        session_id="session_a",
        channel="web",
        device_id="device_x",
        ip_address="10.0.0.1",
    )
    policy = _default_policy(service, offline_allowed=True)

    authorization = service.authorize_stream_access(policy=policy, context=context)
    assert authorization.playback_token is not None

    token = authorization.playback_token.token
    assert service.enforce_playback_token(token, policy=policy, context=context) is True

    service.revoke_media_access(policy=policy, token=token, session_id=context.session_id)
    assert service.enforce_playback_token(token, policy=policy, context=context) is False

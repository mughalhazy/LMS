from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from shared.utils.entitlement import TenantEntitlementContext

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
TokenPolicy = _module.TokenPolicy


def test_authorize_playback_issues_token_with_watermark_when_entitled() -> None:
    service = MediaSecurityService()
    tenant = TenantEntitlementContext(tenant_id="tenant_secure", plan_type="pro")
    context = PlaybackContext(
        tenant_id="tenant_secure",
        user_id="user_1",
        asset_id="asset_1",
        session_id="session_a",
        channel="web",
        device_id="device_x",
        ip_address="10.0.0.1",
    )

    authorization = service.authorize_playback(
        tenant=tenant,
        context=context,
        token_policy=TokenPolicy(ttl_seconds=120, bind_to_device=True, bind_to_ip=True),
    )

    assert authorization.decision == "allow"
    assert authorization.playback_token is not None
    assert authorization.watermark["watermark_required"] is True
    assert authorization.security_controls["tokenized_playback"] is True


def test_authorize_playback_fails_closed_when_entitlement_missing() -> None:
    service = MediaSecurityService()
    tenant = TenantEntitlementContext(tenant_id="tenant_basic", plan_type="free")
    context = PlaybackContext(
        tenant_id="tenant_basic",
        user_id="user_2",
        asset_id="asset_2",
        session_id="session_b",
        channel="web",
    )

    authorization = service.authorize_playback(
        tenant=tenant,
        context=context,
        token_policy=TokenPolicy(ttl_seconds=120),
    )

    assert authorization.decision == "deny"
    assert authorization.reason_code == "ENTITLEMENT_DENIED"
    assert authorization.playback_token is None


def test_restriction_enforcement_blocks_concurrency_and_token_replay() -> None:
    service = MediaSecurityService()
    tenant = TenantEntitlementContext(tenant_id="tenant_restrict", plan_type="enterprise")

    first_context = PlaybackContext(
        tenant_id="tenant_restrict",
        user_id="user_3",
        asset_id="asset_3",
        session_id="session_1",
        channel="web",
    )
    second_context = PlaybackContext(
        tenant_id="tenant_restrict",
        user_id="user_3",
        asset_id="asset_3",
        session_id="session_2",
        channel="web",
    )
    policy = TokenPolicy(ttl_seconds=120, single_use=True, max_concurrent_sessions=1)

    first_authorization = service.authorize_playback(tenant=tenant, context=first_context, token_policy=policy)
    assert first_authorization.decision == "allow"
    assert first_authorization.playback_token is not None

    second_authorization = service.authorize_playback(tenant=tenant, context=second_context, token_policy=policy)
    assert second_authorization.decision == "deny"
    assert second_authorization.reason_code == "CONCURRENCY_EXCEEDED"

    token = first_authorization.playback_token.token
    assert service.enforce_playback_token(token, context=first_context, token_policy=policy) is True
    assert service.enforce_playback_token(token, context=first_context, token_policy=policy) is False

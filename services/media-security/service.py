from __future__ import annotations

import base64
import hashlib
import hmac
import importlib.util
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from shared.utils.entitlement import TenantEntitlementContext

_ROOT = Path(__file__).resolve().parents[2]
_MEDIA_SECURITY_CAPABILITY = "secure_media_delivery"


def _load_entitlement_service_module():
    module_path = _ROOT / "services/entitlement-service/service.py"
    sys.path.append(str(module_path.parent))
    spec = importlib.util.spec_from_file_location("entitlement_service_for_media_security", module_path)
    if spec is None or spec.loader is None:
        raise ImportError("Unable to load entitlement service")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_EntitlementModule = _load_entitlement_service_module()
EntitlementService = _EntitlementModule.EntitlementService


@dataclass(frozen=True)
class PlaybackContext:
    tenant_id: str
    user_id: str
    asset_id: str
    session_id: str
    channel: str
    device_id: str = ""
    ip_address: str = ""
    user_agent: str = ""
    correlation_id: str = ""


@dataclass(frozen=True)
class TokenPolicy:
    ttl_seconds: int = 300
    single_use: bool = False
    bind_to_device: bool = False
    bind_to_ip: bool = False
    max_concurrent_sessions: int = 1


@dataclass(frozen=True)
class PlaybackTokenGrant:
    token: str
    issued_at: str
    expires_at: str
    claims: dict[str, str]


@dataclass(frozen=True)
class PlaybackAuthorization:
    decision: str
    reason_code: str = ""
    entitlement: dict[str, str | bool] = field(default_factory=dict)
    playback_token: PlaybackTokenGrant | None = None
    watermark: dict[str, str | bool] = field(default_factory=dict)
    security_controls: dict[str, bool] = field(default_factory=dict)


@dataclass(frozen=True)
class OfflineDownloadContext:
    tenant_id: str
    user_id: str
    package_id: str
    content_ids: list[str]
    roles: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class OfflineDownloadAuthorization:
    decision: str
    reason_code: str = ""
    policy_ref: str = "media-security:offline-download-policy:v1"


class MediaSecurityService:
    """Enforcement-only anti-piracy service for secure media playback."""

    def __init__(
        self,
        *,
        entitlement_service: EntitlementService | None = None,
        signing_secret: str = "media-security-signing-key",
    ) -> None:
        self._entitlement_service = entitlement_service or EntitlementService()
        self._signing_secret = signing_secret.encode("utf-8")
        self._active_sessions: dict[tuple[str, str], set[str]] = {}
        self._used_token_signatures: set[str] = set()

    def authorize_playback(
        self,
        *,
        tenant: TenantEntitlementContext,
        context: PlaybackContext,
        token_policy: TokenPolicy,
    ) -> PlaybackAuthorization:
        self._entitlement_service.upsert_tenant_context(tenant)
        entitlement_decision = self._entitlement_service.decide(tenant, _MEDIA_SECURITY_CAPABILITY)
        is_entitled = self._is_media_security_entitled(tenant=tenant, entitlement_decision=entitlement_decision)
        entitlement = {
            "entitled": is_entitled,
            "entitlement_ref": f"entitlement:{entitlement_decision.capability}",
            "evaluated_at": self._utc_now().isoformat(),
        }
        if not is_entitled:
            return PlaybackAuthorization(
                decision="deny",
                reason_code="ENTITLEMENT_DENIED",
                entitlement=entitlement,
                watermark={"watermark_required": False},
                security_controls={
                    "tokenized_playback": True,
                    "anti_piracy_monitoring_enabled": True,
                    "watermark_hook_evaluated": False,
                },
            )

        restriction_reason = self._check_restrictions(context=context, token_policy=token_policy)
        if restriction_reason:
            return PlaybackAuthorization(
                decision="deny",
                reason_code=restriction_reason,
                entitlement=entitlement,
                watermark={"watermark_required": False},
                security_controls={
                    "tokenized_playback": True,
                    "anti_piracy_monitoring_enabled": True,
                    "watermark_hook_evaluated": False,
                },
            )

        token_grant = self._issue_token(context=context, token_policy=token_policy)
        self._active_sessions.setdefault((context.tenant_id.strip(), context.user_id.strip()), set()).add(context.session_id.strip())
        watermark_payload = {
            "watermark_required": True,
            "watermark_profile_id": "forensic_v1",
            "forensic_payload_ref": self._watermark_ref(context=context, token=token_grant.token),
        }
        return PlaybackAuthorization(
            decision="allow",
            entitlement=entitlement,
            playback_token=token_grant,
            watermark=watermark_payload,
            security_controls={
                "tokenized_playback": True,
                "anti_piracy_monitoring_enabled": True,
                "watermark_hook_evaluated": True,
            },
        )

    def authorize_offline_download(
        self,
        *,
        context: OfflineDownloadContext,
        tenant_plan_type: str,
    ) -> OfflineDownloadAuthorization:
        tenant = TenantEntitlementContext(tenant_id=context.tenant_id, plan_type=tenant_plan_type)
        self._entitlement_service.upsert_tenant_context(tenant)
        entitlement_decision = self._entitlement_service.decide(tenant, _MEDIA_SECURITY_CAPABILITY)
        if not self._is_media_security_entitled(tenant=tenant, entitlement_decision=entitlement_decision):
            return OfflineDownloadAuthorization(decision="deny", reason_code="ENTITLEMENT_DENIED")

        if not context.user_id.strip():
            return OfflineDownloadAuthorization(decision="deny", reason_code="INVALID_USER")
        if not context.content_ids:
            return OfflineDownloadAuthorization(decision="deny", reason_code="EMPTY_PACKAGE")

        normalized_roles = {role.strip().lower() for role in context.roles}
        if not ({"learner", "student", "admin"} & normalized_roles):
            return OfflineDownloadAuthorization(decision="deny", reason_code="ROLE_NOT_ALLOWED")
        return OfflineDownloadAuthorization(decision="allow")

    def enforce_playback_token(self, token: str, *, context: PlaybackContext, token_policy: TokenPolicy) -> bool:
        claims = self._decode_and_verify(token)
        if claims is None:
            return False

        expected_pairs = {
            "tenant_id": context.tenant_id.strip(),
            "user_id": context.user_id.strip(),
            "asset_id": context.asset_id.strip(),
            "session_id": context.session_id.strip(),
        }
        for key, expected_value in expected_pairs.items():
            if claims.get(key) != expected_value:
                return False

        if token_policy.bind_to_device and claims.get("device_id") != context.device_id.strip():
            return False
        if token_policy.bind_to_ip and claims.get("ip_address") != context.ip_address.strip():
            return False

        expires_at = datetime.fromisoformat(str(claims.get("expires_at")))
        if expires_at <= self._utc_now():
            return False

        signature = token.rsplit(".", 1)[-1]
        if token_policy.single_use:
            if signature in self._used_token_signatures:
                return False
            self._used_token_signatures.add(signature)

        return True

    def _check_restrictions(self, *, context: PlaybackContext, token_policy: TokenPolicy) -> str:
        if token_policy.max_concurrent_sessions <= 0:
            return "INVALID_POLICY"

        active_sessions = self._active_sessions.get((context.tenant_id.strip(), context.user_id.strip()), set())
        normalized_session_id = context.session_id.strip()
        prospective_count = len(active_sessions | {normalized_session_id})
        if prospective_count > token_policy.max_concurrent_sessions:
            return "CONCURRENCY_EXCEEDED"

        if token_policy.bind_to_device and not context.device_id.strip():
            return "DEVICE_REQUIRED"
        if token_policy.bind_to_ip and not context.ip_address.strip():
            return "IP_REQUIRED"
        return ""

    def _issue_token(self, *, context: PlaybackContext, token_policy: TokenPolicy) -> PlaybackTokenGrant:
        now = self._utc_now()
        expires = now + timedelta(seconds=max(token_policy.ttl_seconds, 1))
        claims = {
            "tenant_id": context.tenant_id.strip(),
            "user_id": context.user_id.strip(),
            "asset_id": context.asset_id.strip(),
            "session_id": context.session_id.strip(),
            "device_id": context.device_id.strip(),
            "ip_address": context.ip_address.strip(),
            "issued_at": now.isoformat(),
            "expires_at": expires.isoformat(),
        }
        token = self._encode(claims)
        return PlaybackTokenGrant(
            token=token,
            issued_at=claims["issued_at"],
            expires_at=claims["expires_at"],
            claims={
                "tenant_id": claims["tenant_id"],
                "user_id": claims["user_id"],
                "asset_id": claims["asset_id"],
                "session_id": claims["session_id"],
                "entitlement_ref": f"entitlement:{_MEDIA_SECURITY_CAPABILITY}",
            },
        )

    def _watermark_ref(self, *, context: PlaybackContext, token: str) -> str:
        digest = hashlib.sha256(f"{context.tenant_id}:{context.user_id}:{token}".encode("utf-8")).hexdigest()
        return f"wmk:{digest[:24]}"

    def _encode(self, claims: dict[str, str]) -> str:
        payload = json.dumps(claims, separators=(",", ":"), sort_keys=True).encode("utf-8")
        encoded_payload = base64.urlsafe_b64encode(payload).decode("utf-8")
        signature = hmac.new(self._signing_secret, encoded_payload.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"{encoded_payload}.{signature}"

    def _decode_and_verify(self, token: str) -> dict[str, str] | None:
        token_parts = token.split(".")
        if len(token_parts) != 2:
            return None
        encoded_payload, given_signature = token_parts
        expected_signature = hmac.new(self._signing_secret, encoded_payload.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(given_signature, expected_signature):
            return None
        try:
            payload = base64.urlsafe_b64decode(encoded_payload.encode("utf-8"))
            decoded = json.loads(payload.decode("utf-8"))
        except (ValueError, json.JSONDecodeError):
            return None
        if not isinstance(decoded, dict):
            return None
        return {str(key): str(value) for key, value in decoded.items()}

    def _utc_now(self) -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _is_media_security_entitled(*, tenant: TenantEntitlementContext, entitlement_decision: Any) -> bool:
        paid_plan = tenant.plan_type.strip().lower() in {"pro", "enterprise"}
        return bool(entitlement_decision.is_enabled) or paid_plan

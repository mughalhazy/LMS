from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import sys
import importlib.util
from typing import Any

sys.path.append(str(Path(__file__).resolve().parents[2]))

from shared.control_plane import build_control_plane_client
from shared.models.media_policy import MediaAccessPolicy
from shared.utils.entitlement import TenantEntitlementContext


def _load_models_module():
    module_path = Path(__file__).resolve().parent / "models.py"
    spec = importlib.util.spec_from_file_location("media_security_models", module_path)
    if spec is None or spec.loader is None:
        raise ImportError("Unable to load media security models")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_ModelsModule = _load_models_module()
PlaybackAuthorization = _ModelsModule.PlaybackAuthorization
PlaybackContext = _ModelsModule.PlaybackContext
PlaybackTokenGrant = _ModelsModule.PlaybackTokenGrant

_DEFAULT_MEDIA_CAPABILITY = "secure_media_delivery"


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
    """Anti-piracy gatekeeper for stream authorization, tokenization, and revocation."""

    def __init__(self, *, signing_secret: str = "media-security-signing-key", control_plane=None) -> None:
        self._signing_secret = signing_secret.encode("utf-8")
        self._control_plane = control_plane or build_control_plane_client()
        self._active_sessions: dict[tuple[str, str], set[str]] = {}
        self._active_devices: dict[tuple[str, str], set[str]] = {}
        self._revoked_tokens: set[str] = set()
        self._revoked_sessions: set[tuple[str, str, str]] = set()

    def authorize_stream_access(self, *, policy: MediaAccessPolicy, context: PlaybackContext) -> PlaybackAuthorization:
        normalized_policy = policy.normalized()
        entitlement = self._evaluate_entitlement(policy=normalized_policy)
        if not entitlement["entitled"]:
            return self._deny("ENTITLEMENT_DENIED", entitlement)

        validation_error = self.validate_device_session(policy=normalized_policy, context=context)
        if validation_error:
            return self._deny(validation_error, entitlement)

        try:
            token_grant = self.generate_secure_playback_token(policy=normalized_policy, context=context)
        except ValueError:
            return self._deny("TOKEN_POLICY_INVALID", entitlement)
        self._register_access(policy=normalized_policy, context=context)

        watermark_payload = dict(normalized_policy.watermark_payload)
        watermark_payload.setdefault("watermark_required", True)
        watermark_payload.setdefault(
            "forensic_payload_ref",
            self._watermark_ref(
                tenant_id=normalized_policy.tenant_id,
                user_id=normalized_policy.user_id,
                token=token_grant.token,
            ),
        )

        return PlaybackAuthorization(
            decision="allow",
            entitlement=entitlement,
            playback_token=token_grant,
            watermark={str(k): bool(v) if isinstance(v, bool) else str(v) for k, v in watermark_payload.items()},
            security_controls={
                "tokenized_playback": True,
                "anti_piracy_monitoring_enabled": True,
                "device_session_restriction": True,
                "offline_policy_enforced": True,
            },
        )

    def generate_secure_playback_token(self, *, policy: MediaAccessPolicy, context: PlaybackContext) -> PlaybackTokenGrant:
        normalized_policy = policy.normalized()
        now = self._utc_now()
        expires = normalized_policy.token_expiry

        if expires <= now:
            raise ValueError("Policy token expiry must be in the future")

        claims = {
            "tenant_id": normalized_policy.tenant_id,
            "user_id": normalized_policy.user_id,
            "media_id": normalized_policy.media_id,
            "session_id": context.session_id.strip(),
            "device_id": context.device_id.strip(),
            "ip_address": context.ip_address.strip(),
            "issued_at": now.isoformat(),
            "expires_at": expires.isoformat(),
            "offline_allowed": str(normalized_policy.offline_allowed),
            "capability_id": normalized_policy.capability_id,
        }
        token = self._encode(claims)
        return PlaybackTokenGrant(
            token=token,
            issued_at=claims["issued_at"],
            expires_at=claims["expires_at"],
            claims=claims,
        )

    def validate_device_session(self, *, policy: MediaAccessPolicy, context: PlaybackContext) -> str:
        normalized_policy = policy.normalized()
        binding_options = normalized_policy.metadata.get("binding", {}) if isinstance(normalized_policy.metadata, dict) else {}
        bind_to_device = bool(binding_options.get("bind_to_device", False))
        bind_to_ip = bool(binding_options.get("bind_to_ip", False))

        if context.offline_request and not normalized_policy.offline_allowed:
            return "OFFLINE_PLAYBACK_DENIED"

        if bind_to_device and not context.device_id.strip():
            return "DEVICE_REQUIRED"
        if bind_to_ip and not context.ip_address.strip():
            return "IP_REQUIRED"

        key = (normalized_policy.tenant_id, normalized_policy.user_id)
        active_sessions = self._active_sessions.get(key, set())
        active_devices = self._active_devices.get(key, set())

        session_count = len(active_sessions | {context.session_id.strip()})
        if normalized_policy.allowed_session_count <= 0 or session_count > normalized_policy.allowed_session_count:
            return "SESSION_LIMIT_EXCEEDED"

        candidate_devices = set(active_devices)
        if context.device_id.strip():
            candidate_devices.add(context.device_id.strip())

        if normalized_policy.allowed_device_count <= 0:
            return "DEVICE_LIMIT_EXCEEDED"
        if len(candidate_devices) > normalized_policy.allowed_device_count:
            return "DEVICE_LIMIT_EXCEEDED"

        return ""

    def revoke_media_access(self, *, policy: MediaAccessPolicy, token: str | None = None, session_id: str | None = None) -> None:
        normalized_policy = policy.normalized()
        if token:
            self._revoked_tokens.add(token)
        if session_id:
            self._revoked_sessions.add((normalized_policy.tenant_id, normalized_policy.user_id, session_id.strip()))
            key = (normalized_policy.tenant_id, normalized_policy.user_id)
            if key in self._active_sessions:
                self._active_sessions[key].discard(session_id.strip())

    def enforce_playback_token(self, token: str, *, policy: MediaAccessPolicy, context: PlaybackContext) -> bool:
        claims = self._decode_and_verify(token)
        if claims is None:
            return False
        if token in self._revoked_tokens:
            return False

        normalized_policy = policy.normalized()
        if (normalized_policy.tenant_id, normalized_policy.user_id, context.session_id.strip()) in self._revoked_sessions:
            return False

        if claims.get("tenant_id") != normalized_policy.tenant_id:
            return False
        if claims.get("user_id") != normalized_policy.user_id:
            return False
        if claims.get("media_id") != normalized_policy.media_id:
            return False
        if claims.get("session_id") != context.session_id.strip():
            return False

        binding_options = normalized_policy.metadata.get("binding", {}) if isinstance(normalized_policy.metadata, dict) else {}
        if bool(binding_options.get("bind_to_device", False)) and claims.get("device_id") != context.device_id.strip():
            return False
        if bool(binding_options.get("bind_to_ip", False)) and claims.get("ip_address") != context.ip_address.strip():
            return False

        expires_at = datetime.fromisoformat(str(claims.get("expires_at")))
        if expires_at <= self._utc_now():
            return False
        return True

    # Backwards-compatible facade to keep authorization flow policy-gated.
    def authorize_playback(self, *, tenant: TenantEntitlementContext, context: PlaybackContext, policy: MediaAccessPolicy) -> PlaybackAuthorization:
        _ = tenant
        return self.authorize_stream_access(policy=policy, context=context)

    def _evaluate_entitlement(self, *, policy: MediaAccessPolicy) -> dict[str, str | bool]:
        tenant_ctx = TenantEntitlementContext(tenant_id=policy.tenant_id, plan_type="pro")
        capability_id = policy.capability_id or _DEFAULT_MEDIA_CAPABILITY
        entitled = bool(self._control_plane.is_enabled(tenant_ctx, capability_id))
        return {
            "entitled": entitled,
            "capability_id": capability_id,
            "entitlement_ref": f"entitlement:{capability_id}",
            "evaluated_at": self._utc_now().isoformat(),
        }

    def _register_access(self, *, policy: MediaAccessPolicy, context: PlaybackContext) -> None:
        key = (policy.tenant_id, policy.user_id)
        self._active_sessions.setdefault(key, set()).add(context.session_id.strip())
        if context.device_id.strip():
            self._active_devices.setdefault(key, set()).add(context.device_id.strip())

    def _watermark_ref(self, *, tenant_id: str, user_id: str, token: str) -> str:
        digest = hashlib.sha256(f"{tenant_id}:{user_id}:{token}".encode("utf-8")).hexdigest()
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

    def _deny(self, reason: str, entitlement: dict[str, str | bool]) -> PlaybackAuthorization:
        return PlaybackAuthorization(
            decision="deny",
            reason_code=reason,
            entitlement=entitlement,
            watermark={"watermark_required": False},
            security_controls={
                "tokenized_playback": True,
                "anti_piracy_monitoring_enabled": True,
                "device_session_restriction": True,
                "offline_policy_enforced": True,
            },
        )

    def _utc_now(self) -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _is_media_security_entitled(*, tenant: TenantEntitlementContext, entitlement_decision: Any) -> bool:
        paid_plan = tenant.plan_type.strip().lower() in {"pro", "enterprise"}
        return bool(entitlement_decision.is_enabled) or paid_plan

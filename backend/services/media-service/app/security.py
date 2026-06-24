from __future__ import annotations

import hashlib
import hmac as _hmac
import os
import secrets
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


# ── B15-011/012: authorizePlayback with EntitlementVerifier ──────────────────

def _check_entitlement(tenant_id: str, user_id: str, content_id: str) -> Dict[str, Any]:
    """B15-012: EntitlementVerifier — check CAP-VIDEO-STREAMING before granting playback."""
    try:
        from backend.services.entitlement_service.app.service import EntitlementService
        svc = EntitlementService()
        status, body = svc.resolve({"tenant_id": tenant_id, "capability_key": "CAP-VIDEO-STREAMING"})
        return {"enabled": status == 200 and body.get("enabled", False), "reason": body.get("reason", "")}
    except Exception:
        return {"enabled": True, "reason": "entitlement_check_skipped"}


def _generate_playback_token(content_id: str, user_id: str, tenant_id: str, expires_in: int = 3600) -> str:
    secret = os.getenv("MEDIA_SIGNING_SECRET", "dev-media-secret")
    exp = int(time.time()) + expires_in
    payload = f"{content_id}:{user_id}:{tenant_id}:{exp}"
    sig = _hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]
    return f"{payload}:{sig}"


def _validate_playback_token(token: str, content_id: str, user_id: str, tenant_id: str) -> bool:
    try:
        parts = token.split(":")
        if len(parts) != 5:
            return False
        cid, uid, tid, exp_str, sig = parts
        if cid != content_id or uid != user_id or tid != tenant_id:
            return False
        if float(exp_str) < time.time():
            return False
        secret = os.getenv("MEDIA_SIGNING_SECRET", "dev-media-secret")
        payload = f"{cid}:{uid}:{tid}:{exp_str}"
        expected = _hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]
        return _hmac.compare_digest(expected, sig)
    except Exception:
        return False


# ── B15-013: WatermarkHooks + AntiPiracyHooks ────────────────────────────────

class WatermarkHooks:
    @staticmethod
    def on_before_playback_grant(user_id: str, content_id: str, tenant_id: str) -> str:
        """Generate invisible watermark embedding user identity in stream."""
        watermark_seed = f"{user_id}:{content_id}:{tenant_id}:{int(time.time() // 3600)}"
        return hashlib.sha256(watermark_seed.encode()).hexdigest()[:12]

    @staticmethod
    def on_watermark_signal(signal: Dict[str, Any]) -> None:
        """Called when piracy detection system detects a watermarked stream leak."""
        try:
            from backend.services.shared.events.bus import get_default_bus
            from backend.services.shared.events.envelope import build_event
            bus = get_default_bus()
            envelope = build_event(
                event_type="media.watermark.signal_detected",
                tenant_id=signal.get("tenant_id", ""),
                payload=signal,
            )
            bus.publish(envelope)
        except Exception:
            pass


class AntiPiracyHooks:
    _violation_counts: Dict[str, int] = defaultdict(int)

    @classmethod
    def on_policy_violation(cls, user_id: str, tenant_id: str, reason: str) -> None:
        """B15-025: called on piracy breach — revoke session and emit event."""
        key = f"{tenant_id}:{user_id}"
        cls._violation_counts[key] += 1
        try:
            from backend.services.shared.events.bus import get_default_bus
            from backend.services.shared.events.envelope import build_event
            bus = get_default_bus()
            envelope = build_event(
                event_type="media.piracy.policy_violation",
                tenant_id=tenant_id,
                payload={"user_id": user_id, "reason": reason,
                         "violation_count": cls._violation_counts[key]},
            )
            bus.publish(envelope)
        except Exception:
            pass


# ── B15-024: CAP-SESSION-CONTROL ─────────────────────────────────────────────

class SessionController:
    MAX_CONCURRENT_SESSIONS = 2

    def __init__(self) -> None:
        self._active_sessions: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def open_session(self, user_id: str, tenant_id: str, content_id: str,
                     device_id: str) -> Tuple[int, Dict[str, Any]]:
        """B15-024: enforce concurrent session limit per user per tenant."""
        key = f"{tenant_id}:{user_id}"
        active = [s for s in self._active_sessions[key] if not s.get("revoked")]
        if len(active) >= self.MAX_CONCURRENT_SESSIONS:
            return 429, {
                "error": "concurrent_session_limit_exceeded",
                "max_sessions": self.MAX_CONCURRENT_SESSIONS,
                "active_count": len(active),
            }
        session_id = f"msess-{secrets.token_urlsafe(8)}"
        session = {
            "session_id": session_id, "user_id": user_id, "tenant_id": tenant_id,
            "content_id": content_id, "device_id": device_id,
            "opened_at": datetime.now(timezone.utc).isoformat(), "revoked": False,
        }
        self._active_sessions[key].append(session)
        return 201, session

    def revoke_session(self, user_id: str, tenant_id: str, session_id: str,
                       reason: str = "manual") -> Tuple[int, Dict[str, Any]]:
        """B15-024: revoke session on entitlement change or security trigger."""
        key = f"{tenant_id}:{user_id}"
        for s in self._active_sessions[key]:
            if s["session_id"] == session_id:
                s["revoked"] = True
                s["revoked_reason"] = reason
                s["revoked_at"] = datetime.now(timezone.utc).isoformat()
                return 200, {"session_id": session_id, "revoked": True, "reason": reason}
        return 404, {"error": "session_not_found"}

    def list_sessions(self, user_id: str, tenant_id: str) -> List[Dict[str, Any]]:
        key = f"{tenant_id}:{user_id}"
        return [s for s in self._active_sessions[key] if not s.get("revoked")]


# ── B15-025: CAP-ANTI-PIRACY-ENFORCEMENT ─────────────────────────────────────

class AntiPiracyEnforcer:
    RATE_LIMIT_REQUESTS_PER_MINUTE = 60
    ANOMALY_THRESHOLD_MULTIPLIER = 3.0

    def __init__(self) -> None:
        self._request_buckets: Dict[str, List[float]] = defaultdict(list)

    def check_rate_limit(self, user_id: str, tenant_id: str) -> Tuple[bool, Dict[str, Any]]:
        """B15-025: rate limit stream requests per user per minute."""
        key = f"{tenant_id}:{user_id}"
        now = time.time()
        window_start = now - 60
        self._request_buckets[key] = [t for t in self._request_buckets[key] if t > window_start]
        self._request_buckets[key].append(now)
        count = len(self._request_buckets[key])
        if count > self.RATE_LIMIT_REQUESTS_PER_MINUTE:
            AntiPiracyHooks.on_policy_violation(user_id, tenant_id, "rate_limit_exceeded")
            return False, {"error": "rate_limit_exceeded", "requests_per_minute": count,
                           "limit": self.RATE_LIMIT_REQUESTS_PER_MINUTE}
        return True, {"requests_this_minute": count, "limit": self.RATE_LIMIT_REQUESTS_PER_MINUTE}

    def detect_anomaly(self, user_id: str, tenant_id: str) -> Dict[str, Any]:
        """B15-025: anomaly detection — flag unusual access patterns."""
        key = f"{tenant_id}:{user_id}"
        now = time.time()
        minute_count = len([t for t in self._request_buckets[key] if t > now - 60])
        is_anomalous = minute_count > (self.RATE_LIMIT_REQUESTS_PER_MINUTE / 2)
        if is_anomalous:
            AntiPiracyHooks.on_policy_violation(user_id, tenant_id, "anomalous_access_pattern")
        return {"anomaly_detected": is_anomalous, "minute_request_count": minute_count}


# ── Authorise playback — full flow (B15-011) ──────────────────────────────────

_session_ctrl = SessionController()
_anti_piracy = AntiPiracyEnforcer()


def authorize_playback(user_id: str, tenant_id: str, content_id: str,
                       device_id: str) -> Tuple[int, Dict[str, Any]]:
    """B15-011: full entitlement-gated playback authorization flow."""
    # 1. Entitlement check
    entitlement = _check_entitlement(tenant_id, user_id, content_id)
    if not entitlement["enabled"]:
        return 403, {"decision": "denied", "reason": "entitlement_not_granted",
                     "detail": entitlement.get("reason", "")}

    # 2. Anti-piracy rate limit
    ok, rate_info = _anti_piracy.check_rate_limit(user_id, tenant_id)
    if not ok:
        return 429, {"decision": "denied", **rate_info}

    # 3. Session control
    sess_status, sess_body = _session_ctrl.open_session(user_id, tenant_id, content_id, device_id)
    if sess_status != 201:
        return sess_status, {"decision": "denied", **sess_body}

    # 4. Watermark
    watermark = WatermarkHooks.on_before_playback_grant(user_id, content_id, tenant_id)

    # 5. Token
    playback_token = _generate_playback_token(content_id, user_id, tenant_id)

    return 200, {
        "decision": "granted",
        "playback_token": playback_token,
        "watermark": watermark,
        "session_id": sess_body["session_id"],
        "security_controls": {
            "drm_required": False,
            "rate_limit_rpm": _anti_piracy.RATE_LIMIT_REQUESTS_PER_MINUTE,
            "max_concurrent_sessions": _session_ctrl.MAX_CONCURRENT_SESSIONS,
        },
        "expires_in": 3600,
    }

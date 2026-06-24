"""MediaSecurityService — implements media-security-interface-contract.md."""
from __future__ import annotations

import hashlib
import hmac as _hmac
import os
import secrets
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple


MAX_CONCURRENT_SESSIONS = 2
RATE_LIMIT_RPM = 60


class MediaSecurityService:
    def __init__(self) -> None:
        self._sessions: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._request_buckets: Dict[str, List[float]] = defaultdict(list)
        self._violation_counts: Dict[str, int] = defaultdict(int)

    # ── EntitlementVerifier (B15-012) ─────────────────────────────────────
    def _check_entitlement(self, tenant_id: str, user_id: str, content_id: str) -> bool:
        try:
            from backend.services.entitlement_service.app.service import EntitlementService
            svc = EntitlementService()
            status, body = svc.resolve({"tenant_id": tenant_id, "capability_key": "CAP-VIDEO-STREAMING"})
            return status == 200 and body.get("enabled", False)
        except Exception:
            return True

    # ── Token management ──────────────────────────────────────────────────
    def _issue_token(self, content_id: str, user_id: str, tenant_id: str, expires_in: int) -> str:
        secret = os.getenv("MEDIA_SIGNING_SECRET", "dev-media-secret")
        exp = int(time.time()) + expires_in
        payload = f"{content_id}:{user_id}:{tenant_id}:{exp}"
        sig = _hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]
        return f"{payload}:{sig}"

    # ── CAP-SESSION-CONTROL (B15-024) ─────────────────────────────────────
    def authorize_playback(self, user_id: str, tenant_id: str, content_id: str,
                            device_id: str, expires_in: int = 3600) -> Tuple[int, Dict[str, Any]]:
        if not self._check_entitlement(tenant_id, user_id, content_id):
            return 403, {"decision": "denied", "reason": "entitlement_not_granted"}

        ok, rate_info = self._check_rate(user_id, tenant_id)
        if not ok:
            return 429, {"decision": "denied", **rate_info}

        key = f"{tenant_id}:{user_id}"
        active = [s for s in self._sessions[key] if not s.get("revoked")]
        if len(active) >= MAX_CONCURRENT_SESSIONS:
            return 429, {"decision": "denied", "error": "concurrent_session_limit_exceeded",
                          "max_sessions": MAX_CONCURRENT_SESSIONS}

        session_id = f"msec-{secrets.token_urlsafe(8)}"
        watermark_seed = f"{user_id}:{content_id}:{int(time.time() // 3600)}"
        watermark = hashlib.sha256(watermark_seed.encode()).hexdigest()[:12]

        session = {"session_id": session_id, "user_id": user_id, "tenant_id": tenant_id,
                   "content_id": content_id, "device_id": device_id,
                   "opened_at": datetime.now(timezone.utc).isoformat(), "revoked": False}
        self._sessions[key].append(session)

        return 200, {
            "decision": "granted",
            "playback_token": self._issue_token(content_id, user_id, tenant_id, expires_in),
            "watermark": watermark,
            "session_id": session_id,
            "security_controls": {
                "max_concurrent_sessions": MAX_CONCURRENT_SESSIONS,
                "rate_limit_rpm": RATE_LIMIT_RPM,
            },
            "expires_in": expires_in,
        }

    def revoke_session(self, user_id: str, tenant_id: str, session_id: str,
                       reason: str = "manual") -> Tuple[int, Dict[str, Any]]:
        key = f"{tenant_id}:{user_id}"
        for s in self._sessions[key]:
            if s["session_id"] == session_id:
                s["revoked"] = True
                s["revoked_reason"] = reason
                s["revoked_at"] = datetime.now(timezone.utc).isoformat()
                return 200, {"session_id": session_id, "revoked": True, "reason": reason}
        return 404, {"error": "session_not_found"}

    def list_sessions(self, user_id: str, tenant_id: str) -> List[Dict[str, Any]]:
        return [s for s in self._sessions[f"{tenant_id}:{user_id}"] if not s.get("revoked")]

    # ── CAP-ANTI-PIRACY-ENFORCEMENT (B15-025) ─────────────────────────────
    def _check_rate(self, user_id: str, tenant_id: str) -> Tuple[bool, Dict[str, Any]]:
        key = f"{tenant_id}:{user_id}"
        now = time.time()
        self._request_buckets[key] = [t for t in self._request_buckets[key] if t > now - 60]
        self._request_buckets[key].append(now)
        count = len(self._request_buckets[key])
        if count > RATE_LIMIT_RPM:
            self._emit_violation(user_id, tenant_id, "rate_limit_exceeded")
            return False, {"error": "rate_limit_exceeded", "count": count, "limit": RATE_LIMIT_RPM}
        return True, {"requests_this_minute": count}

    def detect_anomaly(self, user_id: str, tenant_id: str) -> Dict[str, Any]:
        key = f"{tenant_id}:{user_id}"
        now = time.time()
        count = len([t for t in self._request_buckets[key] if t > now - 60])
        anomalous = count > RATE_LIMIT_RPM / 2
        if anomalous:
            self._emit_violation(user_id, tenant_id, "anomalous_access_pattern")
        return {"anomaly_detected": anomalous, "minute_request_count": count}

    def handle_watermark_signal(self, signal: Dict[str, Any]) -> None:
        """B15-013: WatermarkHooks.on_watermark_signal."""
        try:
            from backend.services.shared.events.bus import get_default_bus
            from backend.services.shared.events.envelope import build_event
            bus = get_default_bus()
            bus.publish(build_event(event_type="media.watermark.signal_detected",
                                    tenant_id=signal.get("tenant_id", ""), payload=signal))
        except Exception:
            pass

    def _emit_violation(self, user_id: str, tenant_id: str, reason: str) -> None:
        """B15-013: AntiPiracyHooks.on_policy_violation."""
        key = f"{tenant_id}:{user_id}"
        self._violation_counts[key] += 1
        try:
            from backend.services.shared.events.bus import get_default_bus
            from backend.services.shared.events.envelope import build_event
            bus = get_default_bus()
            bus.publish(build_event(event_type="media.piracy.policy_violation",
                                    tenant_id=tenant_id,
                                    payload={"user_id": user_id, "reason": reason,
                                             "count": self._violation_counts[key]}))
        except Exception:
            pass

from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Set


class WebhookSigner:
    """Signs and verifies LMS webhook payloads using HMAC-SHA256."""

    def __init__(self, replay_window_hours: int = 24) -> None:
        self._replay_window = timedelta(hours=replay_window_hours)
        self._seen_delivery_ids: Dict[str, datetime] = {}

    @staticmethod
    def generate_signature(secret: str, timestamp: str, payload: str) -> str:
        message = f"{timestamp}.{payload}".encode("utf-8")
        digest = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
        return f"sha256={digest}"

    def build_headers(self, *, secret: str, payload: str, timestamp: str, delivery_id: str) -> Dict[str, str]:
        return {
            "X-LMS-Timestamp": timestamp,
            "X-LMS-Delivery-Id": delivery_id,
            "X-LMS-Signature": self.generate_signature(secret=secret, timestamp=timestamp, payload=payload),
        }

    def verify_request(
        self,
        *,
        secret: str,
        payload: str,
        headers: Dict[str, str],
        now: datetime,
        max_skew_seconds: int = 300,
    ) -> bool:
        timestamp = headers.get("X-LMS-Timestamp", "")
        delivery_id = headers.get("X-LMS-Delivery-Id", "")
        signature = headers.get("X-LMS-Signature", "")

        if not timestamp or not delivery_id or not signature:
            return False

        expected = self.generate_signature(secret=secret, timestamp=timestamp, payload=payload)
        if not hmac.compare_digest(expected, signature):
            return False

        try:
            request_ts = datetime.utcfromtimestamp(int(timestamp))
        except ValueError:
            return False

        if abs((now - request_ts).total_seconds()) > max_skew_seconds:
            return False

        self._cleanup(now)
        if delivery_id in self._seen_delivery_ids:
            return False

        self._seen_delivery_ids[delivery_id] = now
        return True

    def _cleanup(self, now: datetime) -> None:
        expired: Set[str] = {
            delivery_id
            for delivery_id, seen_at in self._seen_delivery_ids.items()
            if now - seen_at > self._replay_window
        }
        for delivery_id in expired:
            self._seen_delivery_ids.pop(delivery_id, None)

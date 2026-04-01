from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PlaybackContext:
    tenant_id: str
    user_id: str
    media_id: str
    session_id: str
    channel: str
    device_id: str = ""
    ip_address: str = ""
    user_agent: str = ""
    correlation_id: str = ""
    offline_request: bool = False


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


__all__ = ["PlaybackAuthorization", "PlaybackContext", "PlaybackTokenGrant"]

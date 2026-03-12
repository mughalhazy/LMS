"""Data models for the media storage module."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class AccessTier(str, Enum):
    """Access tiers for published media assets."""

    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    PREMIUM = "premium"


@dataclass(slots=True)
class MediaAsset:
    """Represents a media asset tracked by the media pipeline service."""

    title: str
    tenant_id: str
    uploaded_by: str
    object_storage_uri: str
    checksum_sha256: str
    language: str | None = None
    duration_seconds: int | None = None
    access_tier: AccessTier = AccessTier.AUTHENTICATED
    codec: str | None = None
    asset_id: str = field(default_factory=lambda: f"asset_{uuid4().hex}")
    uploaded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    published_at: datetime | None = None
    cdn_playback_url: str | None = None
    cdn_thumbnail_url: str | None = None


@dataclass(slots=True)
class StorageObject:
    """Minimal object representation returned by the storage adapter."""

    bucket: str
    key: str
    checksum_sha256: str
    size_bytes: int

    @property
    def uri(self) -> str:
        return f"s3://{self.bucket}/{self.key}"


@dataclass(slots=True)
class AccessToken:
    """A signed media-access token."""

    token: str
    asset_id: str
    tenant_id: str
    subject: str
    expires_at: datetime
    claims: dict[str, Any]

    @classmethod
    def mint(
        cls,
        asset_id: str,
        tenant_id: str,
        subject: str,
        claims: dict[str, Any] | None = None,
        ttl_seconds: int = 600,
    ) -> "AccessToken":
        claims = claims or {}
        token = uuid4().hex + uuid4().hex
        return cls(
            token=token,
            asset_id=asset_id,
            tenant_id=tenant_id,
            subject=subject,
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds),
            claims=claims,
        )

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at

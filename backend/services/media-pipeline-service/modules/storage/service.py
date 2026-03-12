"""Media storage orchestration service."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .cdn import CDNPublisher
from .config import MediaStorageModuleConfig
from .models import AccessTier, AccessToken, MediaAsset
from .object_storage import ObjectStorageClient
from .policy import AccessPolicyEnforcer


@dataclass(slots=True)
class MediaStorageService:
    """Coordinates object storage writes, CDN publication, and access policy checks."""

    config: MediaStorageModuleConfig
    object_storage: ObjectStorageClient
    cdn_publisher: CDNPublisher
    policy_enforcer: AccessPolicyEnforcer
    _assets: dict[str, MediaAsset] = field(default_factory=dict)

    def upload_video(
        self,
        *,
        title: str,
        tenant_id: str,
        uploaded_by: str,
        data: bytes,
        filename: str,
        access_tier: AccessTier = AccessTier.AUTHENTICATED,
    ) -> MediaAsset:
        key = f"raw/{tenant_id}/{filename}"
        stored = self.object_storage.put_bytes(self.config.storage.bucket_videos, key, data)
        asset = MediaAsset(
            title=title,
            tenant_id=tenant_id,
            uploaded_by=uploaded_by,
            object_storage_uri=stored.uri,
            checksum_sha256=stored.checksum_sha256,
            access_tier=access_tier,
        )
        self._assets[asset.asset_id] = asset
        return asset

    def publish_to_cdn(self, asset_id: str, thumbnail_uri: str | None = None) -> MediaAsset:
        asset = self.require_asset(asset_id)
        asset.cdn_playback_url = self.cdn_publisher.publish_asset(asset.object_storage_uri)
        if thumbnail_uri:
            asset.cdn_thumbnail_url = self.cdn_publisher.publish_thumbnail(thumbnail_uri)
        return asset

    def mint_access_token(
        self,
        *,
        asset_id: str,
        tenant_id: str,
        subject: str,
        entitlements: Iterable[str] | None = None,
        ttl_seconds: int = 600,
    ) -> AccessToken:
        claims = {"entitlements": list(entitlements or [])}
        return AccessToken.mint(
            asset_id=asset_id,
            tenant_id=tenant_id,
            subject=subject,
            claims=claims,
            ttl_seconds=ttl_seconds,
        )

    def retrieve_media(self, asset_id: str, token: AccessToken) -> dict[str, str]:
        asset = self.require_asset(asset_id)
        self.policy_enforcer.enforce(asset, token)

        playback_url = asset.cdn_playback_url or self.cdn_publisher.publish_asset(asset.object_storage_uri, ttl_seconds=300)
        return {
            "asset_id": asset.asset_id,
            "playback_url": playback_url,
            "thumbnail_url": asset.cdn_thumbnail_url or "",
            "checksum_sha256": asset.checksum_sha256,
        }

    def require_asset(self, asset_id: str) -> MediaAsset:
        asset = self._assets.get(asset_id)
        if not asset:
            raise KeyError(f"unknown media asset: {asset_id}")
        return asset

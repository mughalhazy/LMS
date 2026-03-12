"""HTTP endpoints for media retrieval and token generation.

This module intentionally uses FastAPI-compatible patterns but avoids a hard dependency.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .config import MediaStorageModuleConfig
from .cdn import CDNPublisher
from .models import AccessTier
from .object_storage import InMemoryObjectStorageClient
from .policy import AccessPolicyEnforcer
from .service import MediaStorageService


@dataclass(slots=True)
class RequestContext:
    tenant_id: str
    subject: str
    entitlements: list[str]


def build_default_service() -> MediaStorageService:
    config = MediaStorageModuleConfig.from_env()
    return MediaStorageService(
        config=config,
        object_storage=InMemoryObjectStorageClient(),
        cdn_publisher=CDNPublisher(config.cdn),
        policy_enforcer=AccessPolicyEnforcer(config.policy),
    )


def post_upload_video(
    service: MediaStorageService,
    *,
    context: RequestContext,
    title: str,
    filename: str,
    content: bytes,
    access_tier: str = "authenticated",
) -> dict:
    asset = service.upload_video(
        title=title,
        tenant_id=context.tenant_id,
        uploaded_by=context.subject,
        data=content,
        filename=filename,
        access_tier=AccessTier(access_tier),
    )
    return asdict(asset)


def post_publish_asset(service: MediaStorageService, *, asset_id: str, thumbnail_uri: str | None = None) -> dict:
    asset = service.publish_to_cdn(asset_id=asset_id, thumbnail_uri=thumbnail_uri)
    return asdict(asset)


def post_access_token(service: MediaStorageService, *, context: RequestContext, asset_id: str) -> dict:
    token = service.mint_access_token(
        asset_id=asset_id,
        tenant_id=context.tenant_id,
        subject=context.subject,
        entitlements=context.entitlements,
    )
    return {
        "token": token.token,
        "expires_at": token.expires_at.isoformat(),
        "asset_id": token.asset_id,
    }


def get_media_asset(service: MediaStorageService, *, asset_id: str, context: RequestContext, token: str) -> dict:
    # In a production implementation, token lookup/verification would happen in an auth gateway.
    access_token = service.mint_access_token(
        asset_id=asset_id,
        tenant_id=context.tenant_id,
        subject=context.subject,
        entitlements=context.entitlements,
        ttl_seconds=120,
    )
    access_token.token = token
    return service.retrieve_media(asset_id=asset_id, token=access_token)

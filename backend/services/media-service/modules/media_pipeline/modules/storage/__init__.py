"""Media storage integration module.

Implements:
- object storage integration
- CDN asset publishing
- access policy enforcement
- media retrieval endpoints
"""

from .cdn import CDNPublisher
from .config import MediaStorageModuleConfig
from .endpoints import (
    RequestContext,
    build_default_service,
    get_media_asset,
    post_access_token,
    post_publish_asset,
    post_upload_video,
)
from .object_storage import InMemoryObjectStorageClient, LocalFileObjectStorageClient
from .policy import AccessDeniedError, AccessPolicyEnforcer
from .service import MediaStorageService

__all__ = [
    "AccessDeniedError",
    "AccessPolicyEnforcer",
    "CDNPublisher",
    "InMemoryObjectStorageClient",
    "LocalFileObjectStorageClient",
    "MediaStorageModuleConfig",
    "MediaStorageService",
    "RequestContext",
    "build_default_service",
    "get_media_asset",
    "post_access_token",
    "post_publish_asset",
    "post_upload_video",
]

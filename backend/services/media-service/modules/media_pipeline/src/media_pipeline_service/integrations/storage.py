from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass
class StorageObject:
    uri: str
    checksum_sha256: str


class ObjectStorageClient:
    def __init__(self, bucket_base_uri: str = "s3://lms-content-prod/videos") -> None:
        self.bucket_base_uri = bucket_base_uri.rstrip("/")

    def upload_raw_video(self, tenant_id: str, media_asset_id: str, source_filename: str) -> StorageObject:
        object_uri = f"{self.bucket_base_uri}/{tenant_id}/raw/{media_asset_id}/{source_filename}"
        checksum = hashlib.sha256(object_uri.encode("utf-8")).hexdigest()
        return StorageObject(uri=object_uri, checksum_sha256=checksum)

    def store_streaming_manifest(self, tenant_id: str, media_asset_id: str, profile_name: str) -> str:
        return f"{self.bucket_base_uri}/{tenant_id}/streaming/{media_asset_id}/{profile_name}/index.m3u8"

    def store_thumbnail(self, tenant_id: str, media_asset_id: str, image_format: str, index: int) -> str:
        return f"{self.bucket_base_uri}/{tenant_id}/thumbnails/{media_asset_id}/{image_format}/thumb_{index:04d}.{image_format}"

    def store_poster(self, tenant_id: str, media_asset_id: str) -> str:
        return f"{self.bucket_base_uri}/{tenant_id}/thumbnails/{media_asset_id}/poster.jpg"

    def store_sprite_sheet(self, tenant_id: str, media_asset_id: str) -> str:
        return f"{self.bucket_base_uri}/{tenant_id}/thumbnails/{media_asset_id}/sprite.vtt"

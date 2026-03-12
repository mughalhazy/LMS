from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256


@dataclass
class StoredObject:
    uri: str
    checksum_sha256: str


class ObjectStorageClient:
    def __init__(self, bucket: str = "lms-content-prod") -> None:
        self.bucket = bucket

    def upload_raw_video(self, tenant_id: str, media_asset_id: str, source_filename: str) -> StoredObject:
        key = f"videos/{tenant_id}/raw/{media_asset_id}/{source_filename}"
        uri = f"s3://{self.bucket}/{key}"
        checksum = sha256(f"{tenant_id}:{media_asset_id}:{source_filename}".encode("utf-8")).hexdigest()
        return StoredObject(uri=uri, checksum_sha256=checksum)

    def store_streaming_manifest(self, tenant_id: str, media_asset_id: str, profile: str) -> str:
        return f"s3://{self.bucket}/videos/{tenant_id}/streaming/{media_asset_id}/{profile}/index.m3u8"

    def store_thumbnail(self, tenant_id: str, media_asset_id: str, image_format: str, index: int) -> str:
        return f"s3://{self.bucket}/videos/{tenant_id}/thumbnails/{media_asset_id}/{image_format}/thumb-{index:03d}.{image_format}"

    def store_poster(self, tenant_id: str, media_asset_id: str) -> str:
        return f"s3://{self.bucket}/videos/{tenant_id}/thumbnails/{media_asset_id}/poster.jpg"

    def store_sprite_sheet(self, tenant_id: str, media_asset_id: str) -> str:
        return f"s3://{self.bucket}/videos/{tenant_id}/thumbnails/{media_asset_id}/sprite.webp"

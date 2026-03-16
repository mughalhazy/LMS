from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
from uuid import uuid4


class ProcessingStatus(str, Enum):
    uploaded = "uploaded"
    transcoding = "transcoding"
    transcoded = "transcoded"
    thumbnails_generated = "thumbnails_generated"
    published = "published"


@dataclass
class UploadPolicy:
    max_size_mb: int = 1024
    allowed_codecs: List[str] = field(default_factory=lambda: ["h264", "hevc", "vp9"])


@dataclass
class UploaderMetadata:
    uploader_id: str
    title: str
    course_id: str
    tenant_id: str
    description: Optional[str] = None
    language: str = "en"
    access_tier: str = "internal"


@dataclass
class UploadRequest:
    source_filename: str
    source_video_size_bytes: int
    source_codec: str
    uploader_metadata: UploaderMetadata
    source_content_type: str = "video/mp4"
    upload_policy: UploadPolicy = field(default_factory=UploadPolicy)


@dataclass
class RenditionProfile:
    name: str
    width: int
    height: int
    bitrate_kbps: int


@dataclass
class TranscodingRequest:
    target_profiles: List[RenditionProfile] = field(
        default_factory=lambda: [
            RenditionProfile(name="1080p", width=1920, height=1080, bitrate_kbps=5000),
            RenditionProfile(name="720p", width=1280, height=720, bitrate_kbps=2800),
            RenditionProfile(name="480p", width=854, height=480, bitrate_kbps=1200),
        ]
    )
    encoding_preset: str = "h264/aac"
    drm_policy: Optional[str] = None


@dataclass
class ThumbnailRule:
    interval_seconds: int = 10
    keyframe_selection: str = "nearest"
    formats: List[str] = field(default_factory=lambda: ["jpg", "webp"])


@dataclass
class CDNDeliveryConfig:
    ttl_seconds: int = 86400
    invalidation_rules: List[str] = field(default_factory=list)
    access_policy: str = "signed_url"


@dataclass
class MediaMetadata:
    asset_id: str
    title: str
    description: Optional[str]
    language: str
    duration_seconds: int
    codec: str
    resolution_ladder: List[str]
    bitrate_profiles: Dict[str, int]
    checksum_sha256: str
    drm_policy: Optional[str]
    access_tier: str
    tenant_id: str
    uploaded_by: str
    uploaded_at: datetime
    published_at: Optional[datetime] = None
    thumbnail_uri: Optional[str] = None


@dataclass
class MediaAsset:
    uploader_metadata: UploaderMetadata
    source_filename: str
    source_content_type: str
    source_video_size_bytes: int
    source_codec: str
    object_storage_uri: str
    upload_checksum: str
    media_asset_id: str = field(default_factory=lambda: f"asset_{uuid4().hex[:12]}")
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: ProcessingStatus = ProcessingStatus.uploaded
    adaptive_streaming_assets: Dict[str, str] = field(default_factory=dict)
    rendition_metadata: Dict[str, Dict[str, str | int]] = field(default_factory=dict)
    thumbnail_set_uris: Dict[str, List[str]] = field(default_factory=dict)
    poster_image_uri: Optional[str] = None
    sprite_sheet_uri: Optional[str] = None
    cdn_playback_urls: Dict[str, str] = field(default_factory=dict)
    cdn_thumbnail_urls: Dict[str, List[str]] = field(default_factory=dict)
    metadata: Optional[MediaMetadata] = None


@dataclass
class EventRecord:
    event_name: str
    tenant_id: str
    media_asset_id: str
    payload: Dict[str, str]
    emitted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

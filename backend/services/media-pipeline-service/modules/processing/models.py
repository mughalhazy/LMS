"""Core models for the media processing pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class ProcessingStatus(str, Enum):
    QUEUED = "queued"
    VALIDATED = "validated"
    TRANSCODING = "transcoding"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class UploadPolicy:
    max_size_bytes: int
    allowed_container_formats: List[str]
    allowed_video_codecs: List[str]
    allowed_audio_codecs: List[str]


@dataclass(frozen=True)
class MediaMetadata:
    file_name: str
    container_format: str
    size_bytes: int
    duration_seconds: float
    video_codec: str
    audio_codec: str
    width: int
    height: int


@dataclass(frozen=True)
class RenditionProfile:
    name: str
    width: int
    height: int
    video_bitrate_kbps: int
    audio_bitrate_kbps: int
    video_codec: str = "h264"
    audio_codec: str = "aac"


@dataclass
class RenditionResult:
    profile_name: str
    uri: str
    bitrate_kbps: int
    width: int
    height: int
    duration_seconds: float


@dataclass
class ProcessingJob:
    media_asset_id: str
    source_uri: str
    metadata: MediaMetadata
    target_profiles: List[str]
    status: ProcessingStatus = ProcessingStatus.QUEUED
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    error: Optional[str] = None
    renditions: List[RenditionResult] = field(default_factory=list)

    def to_event_payload(self) -> Dict[str, object]:
        return {
            "media_asset_id": self.media_asset_id,
            "source_uri": self.source_uri,
            "status": self.status.value,
            "updated_at": self.updated_at.isoformat() + "Z",
            "renditions": [
                {
                    "profile": item.profile_name,
                    "uri": item.uri,
                    "bitrate_kbps": item.bitrate_kbps,
                    "width": item.width,
                    "height": item.height,
                    "duration_seconds": item.duration_seconds,
                }
                for item in self.renditions
            ],
            "error": self.error,
        }

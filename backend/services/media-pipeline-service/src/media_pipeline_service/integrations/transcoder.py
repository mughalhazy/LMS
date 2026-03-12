from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from media_pipeline_service.models import RenditionProfile


@dataclass
class RenditionArtifact:
    profile: RenditionProfile
    manifest_uri: str
    duration_seconds: int


class TranscoderClient:
    def transcode(self, master_uri: str, profile: RenditionProfile, manifest_uri: str) -> RenditionArtifact:
        _ = master_uri
        duration_seconds = 600
        return RenditionArtifact(
            profile=profile,
            manifest_uri=manifest_uri,
            duration_seconds=duration_seconds,
        )

    @staticmethod
    def metadata(artifact: RenditionArtifact) -> Dict[str, str]:
        return {
            "bitrate_kbps": str(artifact.profile.bitrate_kbps),
            "resolution": f"{artifact.profile.width}x{artifact.profile.height}",
            "duration_seconds": str(artifact.duration_seconds),
        }

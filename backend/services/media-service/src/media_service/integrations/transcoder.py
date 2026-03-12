from __future__ import annotations

from dataclasses import dataclass

from media_service.models import RenditionProfile


@dataclass
class TranscodedArtifact:
    manifest_uri: str
    duration_seconds: int


class TranscoderClient:
    def transcode(self, source_uri: str, profile: RenditionProfile, output_manifest_uri: str) -> TranscodedArtifact:
        _ = source_uri
        base_duration = 600
        profile_duration_adjustment = 0 if profile.name == "1080p" else 5 if profile.name == "720p" else 8
        return TranscodedArtifact(manifest_uri=output_manifest_uri, duration_seconds=base_duration + profile_duration_adjustment)

    def metadata(self, artifact: TranscodedArtifact, profile: RenditionProfile) -> dict[str, str | int]:
        return {
            "manifest_uri": artifact.manifest_uri,
            "bitrate_kbps": profile.bitrate_kbps,
            "resolution": f"{profile.width}x{profile.height}",
            "duration_seconds": artifact.duration_seconds,
        }

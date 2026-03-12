"""Media validation for upload and processing readiness."""

from __future__ import annotations

from dataclasses import dataclass

from .models import MediaMetadata, UploadPolicy


@dataclass
class ValidationResult:
    ok: bool
    reason: str = ""


class MediaValidator:
    """Validates media metadata against upload and processing constraints."""

    @staticmethod
    def validate(metadata: MediaMetadata, policy: UploadPolicy) -> ValidationResult:
        if metadata.size_bytes > policy.max_size_bytes:
            return ValidationResult(
                ok=False,
                reason=(
                    f"File size {metadata.size_bytes} exceeds max "
                    f"{policy.max_size_bytes} bytes"
                ),
            )

        if metadata.container_format.lower() not in {
            fmt.lower() for fmt in policy.allowed_container_formats
        }:
            return ValidationResult(
                ok=False,
                reason=f"Container {metadata.container_format} is not allowed",
            )

        if metadata.video_codec.lower() not in {
            codec.lower() for codec in policy.allowed_video_codecs
        }:
            return ValidationResult(
                ok=False,
                reason=f"Video codec {metadata.video_codec} is not allowed",
            )

        if metadata.audio_codec.lower() not in {
            codec.lower() for codec in policy.allowed_audio_codecs
        }:
            return ValidationResult(
                ok=False,
                reason=f"Audio codec {metadata.audio_codec} is not allowed",
            )

        if metadata.width <= 0 or metadata.height <= 0 or metadata.duration_seconds <= 0:
            return ValidationResult(ok=False, reason="Invalid media dimensions or duration")

        return ValidationResult(ok=True)

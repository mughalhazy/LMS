"""Encoding profile registry for adaptive streaming renditions."""

from __future__ import annotations

from typing import Dict, Iterable, List

from .models import RenditionProfile


DEFAULT_ENCODING_PROFILES: Dict[str, RenditionProfile] = {
    "1080p": RenditionProfile(
        name="1080p",
        width=1920,
        height=1080,
        video_bitrate_kbps=5000,
        audio_bitrate_kbps=192,
    ),
    "720p": RenditionProfile(
        name="720p",
        width=1280,
        height=720,
        video_bitrate_kbps=2800,
        audio_bitrate_kbps=128,
    ),
    "480p": RenditionProfile(
        name="480p",
        width=854,
        height=480,
        video_bitrate_kbps=1200,
        audio_bitrate_kbps=96,
    ),
}


class EncodingProfileRegistry:
    def __init__(self, profiles: Dict[str, RenditionProfile] | None = None) -> None:
        self._profiles = profiles or DEFAULT_ENCODING_PROFILES

    def get(self, name: str) -> RenditionProfile:
        if name not in self._profiles:
            raise KeyError(f"Unknown encoding profile: {name}")
        return self._profiles[name]

    def resolve(self, names: Iterable[str]) -> List[RenditionProfile]:
        return [self.get(name) for name in names]

from __future__ import annotations

from typing import Dict, List


class CDNClient:
    def __init__(self, base_url: str = "https://cdn.lms.example.com") -> None:
        self.base_url = base_url.rstrip("/")

    def publish_streaming_urls(self, streaming_assets: Dict[str, str]) -> Dict[str, str]:
        return {profile: self._to_cdn_url(uri) for profile, uri in streaming_assets.items()}

    def publish_thumbnail_urls(self, thumbnail_assets: Dict[str, List[str]]) -> Dict[str, List[str]]:
        return {fmt: [self._to_cdn_url(uri) for uri in uris] for fmt, uris in thumbnail_assets.items()}

    def _to_cdn_url(self, object_uri: str) -> str:
        clean = object_uri.replace("s3://", "")
        return f"{self.base_url}/{clean}"

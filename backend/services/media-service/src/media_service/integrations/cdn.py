from __future__ import annotations


class CDNClient:
    def __init__(self, base_url: str = "https://cdn.lms.example.com") -> None:
        self.base_url = base_url.rstrip("/")

    def _map_to_cdn(self, object_uri: str) -> str:
        object_path = object_uri.split("/", 3)[-1]
        return f"{self.base_url}/{object_path}"

    def publish_streaming_urls(self, manifests: dict[str, str], signed: bool) -> dict[str, str]:
        suffix = "?sig=mock-token" if signed else ""
        return {profile: f"{self._map_to_cdn(uri)}{suffix}" for profile, uri in manifests.items()}

    def publish_thumbnail_urls(self, thumbnails: dict[str, list[str]], signed: bool) -> dict[str, list[str]]:
        suffix = "?sig=mock-token" if signed else ""
        return {
            image_format: [f"{self._map_to_cdn(uri)}{suffix}" for uri in uris]
            for image_format, uris in thumbnails.items()
        }

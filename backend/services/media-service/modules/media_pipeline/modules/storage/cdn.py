"""CDN publishing support for media assets and thumbnails."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from urllib.parse import quote

from .config import CDNConfig


@dataclass(slots=True)
class CDNPublisher:
    """Generates publishable CDN URLs with deterministic signatures."""

    config: CDNConfig

    def publish_asset(self, object_uri: str, ttl_seconds: int | None = None) -> str:
        ttl = ttl_seconds or self.config.default_ttl_seconds
        encoded_uri = quote(object_uri, safe="")
        signature = sha256(f"{object_uri}:{ttl}:{self.config.signing_key}".encode("utf-8")).hexdigest()
        return f"{self.config.base_url}/stream?src={encoded_uri}&exp={ttl}&sig={signature}"

    def publish_thumbnail(self, object_uri: str, ttl_seconds: int | None = None) -> str:
        ttl = ttl_seconds or self.config.default_ttl_seconds
        encoded_uri = quote(object_uri, safe="")
        signature = sha256(f"thumb:{object_uri}:{ttl}:{self.config.signing_key}".encode("utf-8")).hexdigest()
        return f"{self.config.base_url}/thumb?src={encoded_uri}&exp={ttl}&sig={signature}"

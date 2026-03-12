"""Configuration helpers for media storage integration."""

from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True, slots=True)
class StorageConfig:
    bucket_videos: str = "lms-content-prod-videos"
    bucket_documents: str = "lms-content-prod-documents"
    bucket_interactive: str = "lms-content-prod-interactive"
    bucket_scorm: str = "lms-content-prod-scorm"
    region: str = "us-east-1"


@dataclass(frozen=True, slots=True)
class CDNConfig:
    base_url: str = "https://cdn.lms.example.com"
    signing_key: str = "dev-cdn-signing-key"
    default_ttl_seconds: int = 3600


@dataclass(frozen=True, slots=True)
class PolicyConfig:
    require_tenant_match: bool = True
    premium_entitlement_claim: str = "media:premium"


@dataclass(frozen=True, slots=True)
class MediaStorageModuleConfig:
    storage: StorageConfig
    cdn: CDNConfig
    policy: PolicyConfig

    @classmethod
    def from_env(cls) -> "MediaStorageModuleConfig":
        return cls(
            storage=StorageConfig(
                bucket_videos=os.getenv("MEDIA_BUCKET_VIDEOS", "lms-content-prod-videos"),
                bucket_documents=os.getenv("MEDIA_BUCKET_DOCUMENTS", "lms-content-prod-documents"),
                bucket_interactive=os.getenv("MEDIA_BUCKET_INTERACTIVE", "lms-content-prod-interactive"),
                bucket_scorm=os.getenv("MEDIA_BUCKET_SCORM", "lms-content-prod-scorm"),
                region=os.getenv("MEDIA_STORAGE_REGION", "us-east-1"),
            ),
            cdn=CDNConfig(
                base_url=os.getenv("MEDIA_CDN_BASE_URL", "https://cdn.lms.example.com"),
                signing_key=os.getenv("MEDIA_CDN_SIGNING_KEY", "dev-cdn-signing-key"),
                default_ttl_seconds=int(os.getenv("MEDIA_CDN_DEFAULT_TTL_SECONDS", "3600")),
            ),
            policy=PolicyConfig(
                require_tenant_match=os.getenv("MEDIA_POLICY_REQUIRE_TENANT_MATCH", "true").lower() == "true",
                premium_entitlement_claim=os.getenv("MEDIA_POLICY_PREMIUM_CLAIM", "media:premium"),
            ),
        )

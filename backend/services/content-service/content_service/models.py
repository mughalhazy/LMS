from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ContentType(str, Enum):
    video = "video"
    audio = "audio"
    document = "document"
    scorm_package = "scorm_package"
    assessment_asset = "assessment_asset"


class Visibility(str, Enum):
    private = "private"
    tenant = "tenant"
    public = "public"


@dataclass
class AccessPolicy:
    visibility: Visibility = Visibility.tenant
    allowed_roles: List[str] = field(default_factory=list)
    allowed_user_ids: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "AccessPolicy":
        visibility = Visibility(payload.get("visibility", Visibility.tenant.value))
        return cls(
            visibility=visibility,
            allowed_roles=list(payload.get("allowed_roles", [])),
            allowed_user_ids=list(payload.get("allowed_user_ids", [])),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "visibility": self.visibility.value,
            "allowed_roles": self.allowed_roles,
            "allowed_user_ids": self.allowed_user_ids,
        }


@dataclass
class MetadataPayload:
    title: str
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    language: Optional[str] = None
    duration_seconds: Optional[int] = None
    license: Optional[str] = None
    accessibility_notes: Optional[str] = None
    access_policy: AccessPolicy = field(default_factory=AccessPolicy)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "MetadataPayload":
        return cls(
            title=payload["title"],
            description=payload.get("description"),
            tags=list(payload.get("tags", [])),
            language=payload.get("language"),
            duration_seconds=payload.get("duration_seconds"),
            license=payload.get("license"),
            accessibility_notes=payload.get("accessibility_notes"),
            access_policy=AccessPolicy.from_dict(payload.get("access_policy", {})),
        )

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["access_policy"] = self.access_policy.to_dict()
        return payload


@dataclass
class ContentMetadata(MetadataPayload):
    content_id: str = ""
    tenant_id: str = ""
    content_type: ContentType = ContentType.document
    storage_uri: str = ""
    version: int = 1
    checksum_sha256: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "ContentMetadata":
        return cls(
            content_id=payload["content_id"],
            tenant_id=payload["tenant_id"],
            content_type=ContentType(payload["content_type"]),
            storage_uri=payload["storage_uri"],
            version=payload["version"],
            checksum_sha256=payload["checksum_sha256"],
            title=payload["title"],
            description=payload.get("description"),
            tags=list(payload.get("tags", [])),
            language=payload.get("language"),
            duration_seconds=payload.get("duration_seconds"),
            license=payload.get("license"),
            accessibility_notes=payload.get("accessibility_notes"),
            access_policy=AccessPolicy.from_dict(payload.get("access_policy", {})),
            created_at=datetime.fromisoformat(payload["created_at"]),
            updated_at=datetime.fromisoformat(payload["updated_at"]),
        )


@dataclass
class MetadataUpdatePayload:
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    language: Optional[str] = None
    duration_seconds: Optional[int] = None
    license: Optional[str] = None
    accessibility_notes: Optional[str] = None
    access_policy: Optional[AccessPolicy] = None

    def to_updates(self) -> Dict[str, Any]:
        updates: Dict[str, Any] = {}
        for key, value in asdict(self).items():
            if value is not None:
                updates[key] = value
        if self.access_policy is not None:
            updates["access_policy"] = self.access_policy.to_dict()
        return updates

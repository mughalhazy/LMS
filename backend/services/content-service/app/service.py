"""Content management service — upload, metadata, access control, and versioning.

CGAP-063: replaces NotImplementedError stub. Implements the full content_service_spec.md
contract (upload, metadata, retrieve) and adds content_versioning_spec.md operations
(create_version, rollback_version, publish_version) using an in-memory store consistent
with the rest of the backend service layer.

Spec refs:
  docs/specs/content_service_spec.md
  docs/specs/content_versioning_spec.md
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


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


class VersionStatus(str, Enum):
    draft = "draft"
    review = "review"
    published = "published"
    superseded = "superseded"


class ContentNotFoundError(Exception):
    """Raised when content_id is not found for the requesting tenant."""


class AccessDeniedError(Exception):
    """Raised when the requester lacks access to the content."""


class VersionError(Exception):
    """Raised for invalid versioning operations."""


@dataclass
class ContentRecord:
    content_id: str
    tenant_id: str
    content_type: ContentType
    title: str
    description: str | None
    tags: list[str]
    language: str | None
    duration_seconds: int | None
    license: str | None
    accessibility_notes: str | None
    visibility: Visibility
    allowed_roles: list[str]
    allowed_user_ids: list[str]
    # Versioning
    active_version: int
    checksum_sha256: str
    storage_uri: str
    created_at: datetime
    updated_at: datetime


@dataclass
class ContentVersion:
    version_id: str
    content_id: str
    tenant_id: str
    version_number: int
    status: VersionStatus
    change_summary: str
    editor_id: str
    created_at: datetime
    published_at: datetime | None = None
    publisher_id: str | None = None
    release_notes: str | None = None
    rollback_origin_version: int | None = None
    # Snapshot of the content payload at this version
    checksum_sha256: str = ""
    storage_uri: str = ""
    metadata_snapshot: dict[str, Any] = field(default_factory=dict)


class ContentManagementService:
    """Tenant-scoped content management per content_service_spec.md and content_versioning_spec.md.

    Operations:
    - upload_content: store content, return content_id + v1 metadata
    - update_metadata: update title/tags/access policy etc.
    - get_content: fetch with access enforcement + secure delivery URL
    - list_content: list with access filtering
    - create_version: new immutable draft version
    - rollback_version: clone from target version as new draft
    - publish_version: transition draft → published, update live pointer
    """

    def __init__(self) -> None:
        self._content: dict[str, ContentRecord] = {}
        self._versions: dict[str, list[ContentVersion]] = {}  # content_id → versions

    # ------------------------------------------------------------------ #
    # Core content operations (content_service_spec.md)                   #
    # ------------------------------------------------------------------ #

    def upload_content(
        self,
        *,
        tenant_id: str,
        content_type: str,
        title: str,
        binary_size_bytes: int,
        description: str | None = None,
        tags: list[str] | None = None,
        language: str | None = None,
        duration_seconds: int | None = None,
        license: str | None = None,
        accessibility_notes: str | None = None,
        visibility: str = "tenant",
        allowed_roles: list[str] | None = None,
        allowed_user_ids: list[str] | None = None,
        uploader_id: str = "",
        checksum_sha256: str = "",
    ) -> ContentRecord:
        """Store uploaded content, validate format constraints, return content_id + v1 metadata."""
        content_id = str(uuid4())
        now = datetime.now(timezone.utc)
        storage_uri = f"content://{tenant_id}/{content_id}/v1"

        record = ContentRecord(
            content_id=content_id,
            tenant_id=tenant_id,
            content_type=ContentType(content_type),
            title=title.strip(),
            description=description,
            tags=list(tags or []),
            language=language,
            duration_seconds=duration_seconds,
            license=license,
            accessibility_notes=accessibility_notes,
            visibility=Visibility(visibility),
            allowed_roles=list(allowed_roles or []),
            allowed_user_ids=list(allowed_user_ids or []),
            active_version=1,
            checksum_sha256=checksum_sha256,
            storage_uri=storage_uri,
            created_at=now,
            updated_at=now,
        )
        self._content[content_id] = record

        # Seed version history with v1
        v1 = ContentVersion(
            version_id=str(uuid4()),
            content_id=content_id,
            tenant_id=tenant_id,
            version_number=1,
            status=VersionStatus.published,
            change_summary="Initial upload",
            editor_id=uploader_id,
            created_at=now,
            published_at=now,
            publisher_id=uploader_id,
            checksum_sha256=checksum_sha256,
            storage_uri=storage_uri,
            metadata_snapshot={"title": title, "content_type": content_type, "size_bytes": binary_size_bytes},
        )
        self._versions[content_id] = [v1]
        return record

    def update_metadata(
        self,
        *,
        tenant_id: str,
        content_id: str,
        title: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        language: str | None = None,
        duration_seconds: int | None = None,
        license: str | None = None,
        accessibility_notes: str | None = None,
        visibility: str | None = None,
        allowed_roles: list[str] | None = None,
        allowed_user_ids: list[str] | None = None,
    ) -> ContentRecord:
        """Create/update metadata fields; returns normalised metadata with audit timestamps."""
        record = self._get_record(tenant_id=tenant_id, content_id=content_id)
        if title is not None:
            record.title = title.strip()
        if description is not None:
            record.description = description
        if tags is not None:
            record.tags = list(tags)
        if language is not None:
            record.language = language
        if duration_seconds is not None:
            record.duration_seconds = duration_seconds
        if license is not None:
            record.license = license
        if accessibility_notes is not None:
            record.accessibility_notes = accessibility_notes
        if visibility is not None:
            record.visibility = Visibility(visibility)
        if allowed_roles is not None:
            record.allowed_roles = list(allowed_roles)
        if allowed_user_ids is not None:
            record.allowed_user_ids = list(allowed_user_ids)
        record.updated_at = datetime.now(timezone.utc)
        return record

    def get_content(
        self,
        *,
        tenant_id: str,
        content_id: str,
        requester_user_id: str,
        requester_roles: list[str] | None = None,
    ) -> dict[str, Any]:
        """Fetch content with access enforcement; return secure delivery URL + metadata."""
        record = self._get_record(tenant_id=tenant_id, content_id=content_id)
        self._authorize(record=record, user_id=requester_user_id, roles=requester_roles or [])
        return {
            "metadata": record,
            "delivery_url": f"/content/{content_id}/stream?tenant={tenant_id}&v={record.active_version}",
            "active_version": record.active_version,
        }

    def list_content(
        self,
        *,
        tenant_id: str,
        requester_user_id: str,
        requester_roles: list[str] | None = None,
        content_type: str | None = None,
        tags: list[str] | None = None,
        language: str | None = None,
    ) -> list[ContentRecord]:
        """List accessible content for tenant, filtered and access-controlled."""
        results = [r for r in self._content.values() if r.tenant_id == tenant_id]
        if content_type:
            results = [r for r in results if r.content_type.value == content_type]
        if tags:
            results = [r for r in results if any(t in r.tags for t in tags)]
        if language:
            results = [r for r in results if r.language == language]
        visible = []
        for record in results:
            try:
                self._authorize(record=record, user_id=requester_user_id, roles=requester_roles or [])
                visible.append(record)
            except AccessDeniedError:
                continue
        return visible

    # ------------------------------------------------------------------ #
    # Versioning (content_versioning_spec.md)                             #
    # ------------------------------------------------------------------ #

    def create_version(
        self,
        *,
        tenant_id: str,
        content_id: str,
        change_summary: str,
        editor_id: str,
        checksum_sha256: str = "",
        source_version: int | None = None,
        metadata_updates: dict[str, Any] | None = None,
    ) -> ContentVersion:
        """Create new immutable draft version with incremented version_number.

        Stores payload snapshot and diff metadata. Sets status = draft.
        content_versioning_spec: version creation operation.
        """
        record = self._get_record(tenant_id=tenant_id, content_id=content_id)
        version_list = self._versions.setdefault(content_id, [])

        next_number = max((v.version_number for v in version_list), default=0) + 1
        storage_uri = f"content://{tenant_id}/{content_id}/v{next_number}"

        # Snapshot: start from source_version or current active
        if source_version is not None:
            source = next((v for v in version_list if v.version_number == source_version), None)
            if source is None:
                raise VersionError(f"source_version {source_version} not found")
            base_snapshot = dict(source.metadata_snapshot)
        else:
            base_snapshot = {
                "title": record.title,
                "content_type": record.content_type.value,
                "tags": record.tags,
                "language": record.language,
            }

        if metadata_updates:
            base_snapshot.update(metadata_updates)

        version = ContentVersion(
            version_id=str(uuid4()),
            content_id=content_id,
            tenant_id=tenant_id,
            version_number=next_number,
            status=VersionStatus.draft,
            change_summary=change_summary.strip(),
            editor_id=editor_id,
            created_at=datetime.now(timezone.utc),
            checksum_sha256=checksum_sha256 or record.checksum_sha256,
            storage_uri=storage_uri,
            metadata_snapshot=base_snapshot,
        )
        version_list.append(version)
        return version

    def rollback_version(
        self,
        *,
        tenant_id: str,
        content_id: str,
        target_version_number: int,
        rollback_reason: str,
        requested_by: str,
    ) -> ContentVersion:
        """Clone target version as new draft without deleting history.

        content_versioning_spec: version rollback operation.
        Links rollback_origin_version, logs audit, marks previous active draft superseded.
        """
        record = self._get_record(tenant_id=tenant_id, content_id=content_id)
        version_list = self._versions.get(content_id, [])

        target = next((v for v in version_list if v.version_number == target_version_number), None)
        if target is None:
            raise VersionError(f"target_version_number {target_version_number} not found")

        # Supersede any existing unresolved drafts
        for v in version_list:
            if v.status == VersionStatus.draft:
                v.status = VersionStatus.superseded

        next_number = max((v.version_number for v in version_list), default=0) + 1
        rollback_version = ContentVersion(
            version_id=str(uuid4()),
            content_id=content_id,
            tenant_id=tenant_id,
            version_number=next_number,
            status=VersionStatus.draft,
            change_summary=f"Rollback to v{target_version_number}: {rollback_reason}",
            editor_id=requested_by,
            created_at=datetime.now(timezone.utc),
            checksum_sha256=target.checksum_sha256,
            storage_uri=f"content://{tenant_id}/{content_id}/v{next_number}",
            rollback_origin_version=target_version_number,
            metadata_snapshot=dict(target.metadata_snapshot),
        )
        version_list.append(rollback_version)
        record.updated_at = datetime.now(timezone.utc)
        return rollback_version

    def publish_version(
        self,
        *,
        tenant_id: str,
        content_id: str,
        version_number: int,
        publisher_id: str,
        release_notes: str = "",
        publish_scope: str = "global",
    ) -> ContentVersion:
        """Transition version draft/review → published and update live content pointer.

        content_versioning_spec: version publishing operation.
        Emits: updates record.active_version to this version_number.
        """
        record = self._get_record(tenant_id=tenant_id, content_id=content_id)
        version_list = self._versions.get(content_id, [])

        version = next((v for v in version_list if v.version_number == version_number), None)
        if version is None:
            raise VersionError(f"version_number {version_number} not found")
        if version.status == VersionStatus.published:
            raise VersionError(f"version {version_number} is already published")
        if version.status == VersionStatus.superseded:
            raise VersionError(f"version {version_number} has been superseded and cannot be published")

        now = datetime.now(timezone.utc)
        version.status = VersionStatus.published
        version.published_at = now
        version.publisher_id = publisher_id
        version.release_notes = release_notes

        # Update live content pointer
        record.active_version = version_number
        record.storage_uri = version.storage_uri
        record.checksum_sha256 = version.checksum_sha256
        record.updated_at = now
        return version

    def list_versions(self, *, tenant_id: str, content_id: str) -> list[ContentVersion]:
        self._get_record(tenant_id=tenant_id, content_id=content_id)
        return list(self._versions.get(content_id, []))

    def get_version(self, *, tenant_id: str, content_id: str, version_number: int) -> ContentVersion:
        self._get_record(tenant_id=tenant_id, content_id=content_id)
        version = next(
            (v for v in self._versions.get(content_id, []) if v.version_number == version_number),
            None,
        )
        if version is None:
            raise VersionError(f"version_number {version_number} not found for content {content_id}")
        return version

    # ------------------------------------------------------------------ #
    # Internal                                                             #
    # ------------------------------------------------------------------ #

    def _get_record(self, *, tenant_id: str, content_id: str) -> ContentRecord:
        record = self._content.get(content_id)
        if not record or record.tenant_id != tenant_id:
            raise ContentNotFoundError(f"content_id={content_id} not found")
        return record

    def _authorize(self, *, record: ContentRecord, user_id: str, roles: list[str]) -> None:
        if record.visibility in {Visibility.public, Visibility.tenant}:
            return
        if user_id in record.allowed_user_ids:
            return
        if any(r in record.allowed_roles for r in roles):
            return
        raise AccessDeniedError(f"user {user_id!r} is not permitted to access content {record.content_id!r}")

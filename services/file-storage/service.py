from __future__ import annotations

"""
File Storage Service — services/file-storage/service.py
MS§5.11 Content Protection Capabilities (file storage layer)
MS§4 adapter isolation via integrations/storage/

Responsibilities:
  - Content upload orchestration (pre-signed URL generation or direct upload)
  - Content metadata registration (content_id, tenant, type, status, storage key)
  - Download URL generation (respects content_tier — paid content routed through media security)
  - Content lifecycle management (uploading → ready → archived → deleted)
  - Tenant-scoped content isolation

Per file_storage_design.md, canonical content types and buckets:
  video     → lms-video-store
  document  → lms-document-store
  scorm     → lms-scorm-store
  image     → lms-image-store

BC-CONTENT-02: content with content_tier="paid" must go through the
media security gate for download URLs — this service never returns a
raw download URL for paid content. It returns a media_security_required signal.

MO-023 / Phase B.
"""

import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

sys.path.append(str(Path(__file__).resolve().parents[2]))

from integrations.storage import (
    LocalStorageAdapter,
    StorageRouter,
    TenantStorageContext,
)


# ------------------------------------------------------------------
# Models
# ------------------------------------------------------------------

ContentStatus = Literal["uploading", "processing", "ready", "archived", "deleted"]
ContentTier = Literal["free", "paid", "preview"]
ContentCategory = Literal["video", "document", "scorm", "image"]


@dataclass
class ContentRecord:
    content_id: str
    tenant_id: str
    title: str
    content_category: ContentCategory
    content_tier: ContentTier
    status: ContentStatus
    storage_key: str          # key within the canonical bucket
    mime_type: str
    size_bytes: int
    created_at: str
    updated_at: str
    uploaded_by: str = ""
    duration_seconds: int = 0   # for video content
    page_count: int = 0         # for document content
    metadata: dict = field(default_factory=dict)


@dataclass
class UploadInitResult:
    ok: bool
    content_id: str
    upload_url: str               # pre-signed PUT URL for direct client upload
    upload_expires_in: int        # seconds until upload URL expires
    content_category: str
    storage_key: str
    error: str | None = None


@dataclass
class DownloadUrlResult:
    ok: bool
    content_id: str
    content_tier: ContentTier
    # For free/preview content: direct presigned download URL
    download_url: str = ""
    expires_in_seconds: int = 0
    # For paid content: media security gate required
    media_security_required: bool = False
    media_security_hint: str = ""   # "call media-security service to obtain playback token"
    error: str | None = None


@dataclass
class ContentDeleteResult:
    ok: bool
    content_id: str
    error: str | None = None


# ------------------------------------------------------------------
# Service
# ------------------------------------------------------------------

class FileStorageService:
    """File storage service — manages content lifecycle via storage adapter.

    Injection:
        storage_router: StorageRouter — adapter-driven storage routing.
        Default: LocalStorageAdapter (suitable for dev; replace with S3StorageAdapter in prod).
    """

    def __init__(self, *, storage_router: StorageRouter | None = None) -> None:
        if storage_router is None:
            self._router = StorageRouter(default_adapter=LocalStorageAdapter())
        else:
            self._router = storage_router
        # In-memory content registry (replace with DB-backed store for production)
        self._content_registry: dict[str, ContentRecord] = {}

    # ------------------------------------------------------------------
    # Upload flow
    # ------------------------------------------------------------------

    def initiate_upload(
        self,
        *,
        tenant_id: str,
        title: str,
        content_category: ContentCategory,
        content_tier: ContentTier = "free",
        mime_type: str,
        size_bytes: int,
        uploaded_by: str = "",
        metadata: dict | None = None,
    ) -> UploadInitResult:
        """Step 1: Register content record and return a pre-signed upload URL.

        The client uses the upload_url to PUT the file directly to object storage.
        After upload, the client calls confirm_upload() to transition status to 'ready'.
        """
        content_id = str(uuid.uuid4())
        storage_key = f"{tenant_id}/{content_category}/{content_id}/{self._safe_title(title)}"
        tenant_ctx = TenantStorageContext(tenant_id=tenant_id)
        now = self._utcnow()

        result = self._router.presigned_upload_url(
            content_category=content_category,
            key=storage_key,
            content_type=mime_type,
            tenant=tenant_ctx,
        )
        if not result.ok:
            return UploadInitResult(ok=False, content_id="", upload_url="", upload_expires_in=0, content_category=content_category, storage_key="", error=result.error)

        record = ContentRecord(
            content_id=content_id,
            tenant_id=tenant_id,
            title=title,
            content_category=content_category,
            content_tier=content_tier,
            status="uploading",
            storage_key=storage_key,
            mime_type=mime_type,
            size_bytes=size_bytes,
            created_at=now,
            updated_at=now,
            uploaded_by=uploaded_by,
            metadata=metadata or {},
        )
        self._content_registry[content_id] = record

        return UploadInitResult(
            ok=True,
            content_id=content_id,
            upload_url=result.url,
            upload_expires_in=result.expires_in_seconds,
            content_category=content_category,
            storage_key=storage_key,
        )

    def confirm_upload(self, *, content_id: str, tenant_id: str) -> dict:
        """Step 2: Mark content as ready after client has uploaded to pre-signed URL.

        For video content, this transitions to 'processing' and the media pipeline
        picks it up for transcoding. For other content, transitions directly to 'ready'.
        """
        record = self._get_record(content_id=content_id, tenant_id=tenant_id)
        if record is None:
            return {"ok": False, "error": "content_not_found"}
        if record.status != "uploading":
            return {"ok": False, "error": f"invalid_transition: current_status={record.status}"}

        new_status: ContentStatus = "processing" if record.content_category == "video" else "ready"
        self._update_status(content_id=content_id, status=new_status)

        return {
            "ok": True,
            "content_id": content_id,
            "status": new_status,
            "next": "media_pipeline_will_transcode" if new_status == "processing" else "content_ready",
        }

    def direct_upload(
        self,
        *,
        tenant_id: str,
        title: str,
        content_category: ContentCategory,
        content_tier: ContentTier = "free",
        data: bytes,
        mime_type: str,
        uploaded_by: str = "",
        metadata: dict | None = None,
    ) -> dict:
        """Direct upload (server-side) — for programmatic content ingest.

        Uploads bytes directly via the storage adapter.
        Returns content_id and status.
        """
        content_id = str(uuid.uuid4())
        storage_key = f"{tenant_id}/{content_category}/{content_id}/{self._safe_title(title)}"
        tenant_ctx = TenantStorageContext(tenant_id=tenant_id)
        now = self._utcnow()

        result = self._router.upload(
            content_category=content_category,
            key=storage_key,
            data=data,
            content_type=mime_type,
            metadata={"tenant_id": tenant_id, "content_tier": content_tier, **(metadata or {})},
            tenant=tenant_ctx,
        )
        if not result.ok:
            return {"ok": False, "error": result.error}

        new_status: ContentStatus = "processing" if content_category == "video" else "ready"
        record = ContentRecord(
            content_id=content_id,
            tenant_id=tenant_id,
            title=title,
            content_category=content_category,
            content_tier=content_tier,
            status=new_status,
            storage_key=storage_key,
            mime_type=mime_type,
            size_bytes=len(data),
            created_at=now,
            updated_at=now,
            uploaded_by=uploaded_by,
            metadata=metadata or {},
        )
        self._content_registry[content_id] = record

        return {
            "ok": True,
            "content_id": content_id,
            "status": new_status,
            "storage_key": storage_key,
            "etag": result.etag,
        }

    # ------------------------------------------------------------------
    # Download flow
    # ------------------------------------------------------------------

    def get_download_url(
        self,
        *,
        content_id: str,
        tenant_id: str,
        expires_in: int = 3600,
    ) -> DownloadUrlResult:
        """Return a download URL for content.

        BC-CONTENT-02: paid content never gets a direct URL from this service.
        Caller must use the media security service to obtain a playback token.
        """
        record = self._get_record(content_id=content_id, tenant_id=tenant_id)
        if record is None:
            return DownloadUrlResult(ok=False, content_id=content_id, content_tier="free", error="content_not_found")

        if record.status != "ready":
            return DownloadUrlResult(ok=False, content_id=content_id, content_tier=record.content_tier, error=f"content_not_ready: status={record.status}")

        # BC-CONTENT-02 enforcement: paid content requires media security gate
        if record.content_tier == "paid":
            return DownloadUrlResult(
                ok=True,
                content_id=content_id,
                content_tier="paid",
                media_security_required=True,
                media_security_hint="Call media-security service with content_id and user session to obtain a playback token. Do not use raw storage URLs for paid content.",
            )

        tenant_ctx = TenantStorageContext(tenant_id=tenant_id)
        result = self._router.presigned_download_url(
            content_category=record.content_category,
            key=record.storage_key,
            expires_in=expires_in,
            tenant=tenant_ctx,
        )
        if not result.ok:
            return DownloadUrlResult(ok=False, content_id=content_id, content_tier=record.content_tier, error=result.error)

        return DownloadUrlResult(
            ok=True,
            content_id=content_id,
            content_tier=record.content_tier,
            download_url=result.url,
            expires_in_seconds=result.expires_in_seconds,
        )

    def get_storage_key(self, *, content_id: str, tenant_id: str) -> str | None:
        """Return raw storage key for a content item (used by media security service for token binding)."""
        record = self._get_record(content_id=content_id, tenant_id=tenant_id)
        return record.storage_key if record else None

    # ------------------------------------------------------------------
    # Content metadata
    # ------------------------------------------------------------------

    def get_content(self, *, content_id: str, tenant_id: str) -> ContentRecord | None:
        return self._get_record(content_id=content_id, tenant_id=tenant_id)

    def list_content(
        self,
        *,
        tenant_id: str,
        content_category: ContentCategory | None = None,
        content_tier: ContentTier | None = None,
        status: ContentStatus | None = None,
    ) -> list[ContentRecord]:
        records = [r for r in self._content_registry.values() if r.tenant_id == tenant_id]
        if content_category:
            records = [r for r in records if r.content_category == content_category]
        if content_tier:
            records = [r for r in records if r.content_tier == content_tier]
        if status:
            records = [r for r in records if r.status == status]
        return records

    def mark_ready(self, *, content_id: str, tenant_id: str, duration_seconds: int = 0) -> dict:
        """Transition content from 'processing' to 'ready'. Called by media pipeline on completion."""
        record = self._get_record(content_id=content_id, tenant_id=tenant_id)
        if record is None:
            return {"ok": False, "error": "content_not_found"}
        if record.status not in ("processing", "uploading"):
            return {"ok": False, "error": f"invalid_transition: current_status={record.status}"}
        self._update_status(content_id=content_id, status="ready")
        if duration_seconds and record.content_category == "video":
            record.duration_seconds = duration_seconds
        return {"ok": True, "content_id": content_id, "status": "ready"}

    def archive_content(self, *, content_id: str, tenant_id: str) -> dict:
        """Archive content — still stored, no longer available for new access."""
        record = self._get_record(content_id=content_id, tenant_id=tenant_id)
        if record is None:
            return {"ok": False, "error": "content_not_found"}
        self._update_status(content_id=content_id, status="archived")
        return {"ok": True, "content_id": content_id, "status": "archived"}

    def delete_content(self, *, content_id: str, tenant_id: str) -> ContentDeleteResult:
        """Permanently delete content from storage and registry."""
        record = self._get_record(content_id=content_id, tenant_id=tenant_id)
        if record is None:
            return ContentDeleteResult(ok=False, content_id=content_id, error="content_not_found")

        tenant_ctx = TenantStorageContext(tenant_id=tenant_id)
        result = self._router.delete(
            content_category=record.content_category,
            key=record.storage_key,
            tenant=tenant_ctx,
        )
        if not result.ok:
            return ContentDeleteResult(ok=False, content_id=content_id, error=result.error)

        self._update_status(content_id=content_id, status="deleted")
        return ContentDeleteResult(ok=True, content_id=content_id)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _get_record(self, *, content_id: str, tenant_id: str) -> ContentRecord | None:
        record = self._content_registry.get(content_id)
        if record is None or record.tenant_id != tenant_id:
            return None
        return record

    def _update_status(self, *, content_id: str, status: ContentStatus) -> None:
        record = self._content_registry.get(content_id)
        if record:
            record.status = status
            record.updated_at = self._utcnow()

    @staticmethod
    def _safe_title(title: str) -> str:
        return "".join(c if c.isalnum() or c in "-_." else "_" for c in title).strip("_")[:80]

    @staticmethod
    def _utcnow() -> str:
        return datetime.now(timezone.utc).isoformat()

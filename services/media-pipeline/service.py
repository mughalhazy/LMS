from __future__ import annotations

"""
Media Pipeline Service — services/media-pipeline/service.py
MS§5.12 Offline Capabilities + MS§5.11 Content Protection (pipeline layer)
MS§4 adapter isolation via integrations/storage/

Responsibilities:
  - Video transcoding job lifecycle (queued → processing → complete → failed)
  - Image optimization job lifecycle
  - SCORM package extraction and validation
  - Document preview generation
  - Processed asset registration back to file-storage service
  - Thumbnail/poster generation for video content
  - Offline content packaging (zip + manifest for offline sync)

Integration points:
  - Consumes upload events from file-storage service (status="processing" signals)
  - Publishes media.pipeline.complete and media.pipeline.failed events
  - Calls file-storage.mark_ready() on successful completion
  - Storage adapter used for processed output assets

BC-CONTENT-02: Processed paid content output goes through the same
content_tier tag — never strips paid tag from processed assets.

BC-FAIL-01: Proactive offline packaging — when content transitions to
ready, pipeline prepares an offline package automatically for mobile pre-cache.

MO-024 / Phase B.
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

JobStatus = Literal["queued", "processing", "complete", "failed", "cancelled"]
JobType = Literal["video_transcode", "image_optimize", "scorm_extract", "doc_preview", "offline_package"]


@dataclass
class PipelineJob:
    job_id: str
    tenant_id: str
    content_id: str
    job_type: JobType
    status: JobStatus
    input_storage_key: str
    input_content_category: str
    output_storage_keys: list[str] = field(default_factory=list)
    duration_seconds: int = 0       # set on video transcode completion
    thumbnail_key: str = ""         # set on video transcode completion
    offline_package_key: str = ""   # set on offline_package completion
    error: str | None = None
    created_at: str = ""
    updated_at: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class VideoTranscodeSpec:
    """Configuration for a video transcoding job."""
    profiles: list[str] = field(default_factory=lambda: ["360p", "720p"])  # output quality profiles
    generate_thumbnail: bool = True
    thumbnail_at_second: int = 5
    generate_offline_package: bool = True   # BC-FAIL-01: proactive offline packaging


@dataclass
class OfflinePackageManifest:
    """Manifest for an offline content package."""
    package_id: str
    content_id: str
    tenant_id: str
    version: int
    assets: list[dict]   # [{key, url, content_type, size_bytes}]
    created_at: str
    expires_at: str


# ------------------------------------------------------------------
# Service
# ------------------------------------------------------------------

class MediaPipelineService:
    """Media pipeline service — manages media processing jobs.

    Injection:
        storage_router: StorageRouter — storage adapter for processed output.
        file_storage_service: any — notified when pipeline completes (mark_ready).
        event_publisher: any — publishes media.pipeline.* events.
    """

    def __init__(
        self,
        *,
        storage_router: StorageRouter | None = None,
        file_storage_service: Any = None,
        event_publisher: Any = None,
    ) -> None:
        if storage_router is None:
            self._router = StorageRouter(default_adapter=LocalStorageAdapter())
        else:
            self._router = storage_router
        self._file_storage = file_storage_service
        self._event_publisher = event_publisher
        self._jobs: dict[str, PipelineJob] = {}

    # ------------------------------------------------------------------
    # Job submission
    # ------------------------------------------------------------------

    def submit_video_transcode(
        self,
        *,
        tenant_id: str,
        content_id: str,
        input_storage_key: str,
        spec: VideoTranscodeSpec | None = None,
    ) -> PipelineJob:
        """Submit a video transcoding job.

        Called by file-storage service when a video upload is confirmed.
        On completion, calls file_storage.mark_ready() and emits media.pipeline.complete.
        """
        if spec is None:
            spec = VideoTranscodeSpec()
        job = self._create_job(
            tenant_id=tenant_id,
            content_id=content_id,
            job_type="video_transcode",
            input_storage_key=input_storage_key,
            input_content_category="video",
            metadata={"profiles": spec.profiles, "generate_thumbnail": spec.generate_thumbnail, "generate_offline": spec.generate_offline_package},
        )
        # Execute synchronously in this implementation (replace with async job queue for production)
        return self._execute_video_transcode(job=job, spec=spec)

    def submit_image_optimize(
        self,
        *,
        tenant_id: str,
        content_id: str,
        input_storage_key: str,
    ) -> PipelineJob:
        """Submit an image optimization job."""
        job = self._create_job(
            tenant_id=tenant_id,
            content_id=content_id,
            job_type="image_optimize",
            input_storage_key=input_storage_key,
            input_content_category="image",
        )
        return self._execute_image_optimize(job=job)

    def submit_scorm_extract(
        self,
        *,
        tenant_id: str,
        content_id: str,
        input_storage_key: str,
    ) -> PipelineJob:
        """Submit a SCORM package extraction job."""
        job = self._create_job(
            tenant_id=tenant_id,
            content_id=content_id,
            job_type="scorm_extract",
            input_storage_key=input_storage_key,
            input_content_category="scorm",
        )
        return self._execute_scorm_extract(job=job)

    def submit_doc_preview(
        self,
        *,
        tenant_id: str,
        content_id: str,
        input_storage_key: str,
    ) -> PipelineJob:
        """Submit a document preview generation job."""
        job = self._create_job(
            tenant_id=tenant_id,
            content_id=content_id,
            job_type="doc_preview",
            input_storage_key=input_storage_key,
            input_content_category="document",
        )
        return self._execute_doc_preview(job=job)

    def submit_offline_package(
        self,
        *,
        tenant_id: str,
        content_id: str,
        input_storage_key: str,
        content_category: str,
    ) -> PipelineJob:
        """Submit an offline content packaging job.

        BC-FAIL-01: Called automatically after content transitions to 'ready'
        to pre-build offline packages for mobile pre-cache.
        """
        job = self._create_job(
            tenant_id=tenant_id,
            content_id=content_id,
            job_type="offline_package",
            input_storage_key=input_storage_key,
            input_content_category=content_category,
        )
        return self._execute_offline_package(job=job)

    # ------------------------------------------------------------------
    # Job status
    # ------------------------------------------------------------------

    def get_job(self, *, job_id: str, tenant_id: str) -> PipelineJob | None:
        job = self._jobs.get(job_id)
        if job is None or job.tenant_id != tenant_id:
            return None
        return job

    def list_jobs(
        self,
        *,
        tenant_id: str,
        content_id: str | None = None,
        status: JobStatus | None = None,
    ) -> list[PipelineJob]:
        jobs = [j for j in self._jobs.values() if j.tenant_id == tenant_id]
        if content_id:
            jobs = [j for j in jobs if j.content_id == content_id]
        if status:
            jobs = [j for j in jobs if j.status == status]
        return jobs

    def cancel_job(self, *, job_id: str, tenant_id: str) -> dict:
        job = self.get_job(job_id=job_id, tenant_id=tenant_id)
        if job is None:
            return {"ok": False, "error": "job_not_found"}
        if job.status not in ("queued", "processing"):
            return {"ok": False, "error": f"cannot_cancel: status={job.status}"}
        job.status = "cancelled"
        job.updated_at = self._utcnow()
        return {"ok": True, "job_id": job_id, "status": "cancelled"}

    # ------------------------------------------------------------------
    # Offline package manifest
    # ------------------------------------------------------------------

    def get_offline_manifest(self, *, content_id: str, tenant_id: str) -> OfflinePackageManifest | None:
        """Return the offline package manifest for a content item if one exists."""
        jobs = [j for j in self._jobs.values() if j.tenant_id == tenant_id and j.content_id == content_id and j.job_type == "offline_package" and j.status == "complete"]
        if not jobs:
            return None
        job = jobs[-1]  # most recent
        tenant_ctx = TenantStorageContext(tenant_id=tenant_id)
        assets = []
        for key in job.output_storage_keys:
            category = "video" if "video" in key else "document" if "document" in key else "image"
            result = self._router.presigned_download_url(
                content_category=category,
                key=key,
                expires_in=86400,  # 24h for offline pre-cache
                tenant=tenant_ctx,
            )
            assets.append({
                "key": key,
                "url": result.url if result.ok else "",
                "content_type": "application/octet-stream",
                "size_bytes": 0,
            })
        return OfflinePackageManifest(
            package_id=job.job_id,
            content_id=content_id,
            tenant_id=tenant_id,
            version=1,
            assets=assets,
            created_at=job.created_at,
            expires_at=self._utcnow(),
        )

    # ------------------------------------------------------------------
    # Execution stubs (replace with real processing in production)
    # ------------------------------------------------------------------

    def _execute_video_transcode(self, *, job: PipelineJob, spec: VideoTranscodeSpec) -> PipelineJob:
        """Transcode video into multiple quality profiles and generate thumbnail.

        Production: submit to FFmpeg worker queue (Celery/RQ/cloud media service).
        This stub records the job as complete and registers synthetic output keys.
        """
        try:
            job.status = "processing"
            self._update_job(job)

            # Synthetic output keys for each profile
            output_keys = []
            for profile in spec.profiles:
                key = f"{job.input_storage_key}.{profile}.mp4"
                output_keys.append(key)

            # Thumbnail
            thumbnail_key = ""
            if spec.generate_thumbnail:
                thumbnail_key = f"{job.input_storage_key}.thumbnail.jpg"
                output_keys.append(thumbnail_key)

            job.output_storage_keys = output_keys
            job.thumbnail_key = thumbnail_key
            job.duration_seconds = job.metadata.get("duration_hint", 0)  # populated by real transcoder
            job.status = "complete"
            self._update_job(job)

            # Notify file storage service
            if self._file_storage is not None:
                self._file_storage.mark_ready(
                    content_id=job.content_id,
                    tenant_id=job.tenant_id,
                    duration_seconds=job.duration_seconds,
                )

            # BC-FAIL-01: auto-submit offline package job after video is ready
            if spec.generate_offline_package:
                self.submit_offline_package(
                    tenant_id=job.tenant_id,
                    content_id=job.content_id,
                    input_storage_key=job.input_storage_key,
                    content_category="video",
                )

            self._publish_event("media.pipeline.complete", job)
            return job

        except Exception as exc:  # noqa: BLE001
            job.status = "failed"
            job.error = str(exc)
            self._update_job(job)
            self._publish_event("media.pipeline.failed", job)
            return job

    def _execute_image_optimize(self, *, job: PipelineJob) -> PipelineJob:
        """Optimize image — resize, compress, convert to WebP.

        Production: submit to image processing worker (Pillow/ImageMagick/Cloudinary).
        This stub marks job complete immediately.
        """
        try:
            job.status = "processing"
            self._update_job(job)
            # Synthetic output: optimized WebP version
            job.output_storage_keys = [f"{job.input_storage_key}.optimized.webp"]
            job.status = "complete"
            self._update_job(job)
            if self._file_storage is not None:
                self._file_storage.mark_ready(content_id=job.content_id, tenant_id=job.tenant_id)
            self._publish_event("media.pipeline.complete", job)
            return job
        except Exception as exc:  # noqa: BLE001
            job.status = "failed"
            job.error = str(exc)
            self._update_job(job)
            self._publish_event("media.pipeline.failed", job)
            return job

    def _execute_scorm_extract(self, *, job: PipelineJob) -> PipelineJob:
        """Extract SCORM package — unzip and register assets.

        Production: extract ZIP to scorm-store, validate imsmanifest.xml,
        register each asset as a storage key.
        """
        try:
            job.status = "processing"
            self._update_job(job)
            # Synthetic: register manifest and index as output keys
            job.output_storage_keys = [
                f"{job.input_storage_key}.extracted/imsmanifest.xml",
                f"{job.input_storage_key}.extracted/index.html",
            ]
            job.status = "complete"
            self._update_job(job)
            if self._file_storage is not None:
                self._file_storage.mark_ready(content_id=job.content_id, tenant_id=job.tenant_id)
            self._publish_event("media.pipeline.complete", job)
            return job
        except Exception as exc:  # noqa: BLE001
            job.status = "failed"
            job.error = str(exc)
            self._update_job(job)
            self._publish_event("media.pipeline.failed", job)
            return job

    def _execute_doc_preview(self, *, job: PipelineJob) -> PipelineJob:
        """Generate document preview pages.

        Production: convert first N pages of PDF/DOCX to images for inline preview.
        """
        try:
            job.status = "processing"
            self._update_job(job)
            # Synthetic: first 3 page previews
            job.output_storage_keys = [
                f"{job.input_storage_key}.preview.page1.jpg",
                f"{job.input_storage_key}.preview.page2.jpg",
                f"{job.input_storage_key}.preview.page3.jpg",
            ]
            job.status = "complete"
            self._update_job(job)
            if self._file_storage is not None:
                self._file_storage.mark_ready(content_id=job.content_id, tenant_id=job.tenant_id)
            self._publish_event("media.pipeline.complete", job)
            return job
        except Exception as exc:  # noqa: BLE001
            job.status = "failed"
            job.error = str(exc)
            self._update_job(job)
            self._publish_event("media.pipeline.failed", job)
            return job

    def _execute_offline_package(self, *, job: PipelineJob) -> PipelineJob:
        """Build offline content package.

        BC-FAIL-01: Creates a manifest + asset bundle for mobile pre-cache.
        Production: downloads source assets, packages into a zip with a manifest.json,
        stores in document bucket under offline-packages/ prefix.
        """
        try:
            job.status = "processing"
            self._update_job(job)
            # Synthetic: package manifest stored as a JSON key
            manifest_key = f"offline-packages/{job.tenant_id}/{job.content_id}/manifest.json"
            job.output_storage_keys = [manifest_key]
            job.offline_package_key = manifest_key
            job.status = "complete"
            self._update_job(job)
            self._publish_event("media.pipeline.offline_package_ready", job)
            return job
        except Exception as exc:  # noqa: BLE001
            job.status = "failed"
            job.error = str(exc)
            self._update_job(job)
            self._publish_event("media.pipeline.failed", job)
            return job

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _create_job(
        self,
        *,
        tenant_id: str,
        content_id: str,
        job_type: JobType,
        input_storage_key: str,
        input_content_category: str,
        metadata: dict | None = None,
    ) -> PipelineJob:
        now = self._utcnow()
        job = PipelineJob(
            job_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            content_id=content_id,
            job_type=job_type,
            status="queued",
            input_storage_key=input_storage_key,
            input_content_category=input_content_category,
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
        )
        self._jobs[job.job_id] = job
        return job

    def _update_job(self, job: PipelineJob) -> None:
        job.updated_at = self._utcnow()
        self._jobs[job.job_id] = job

    def _publish_event(self, event_type: str, job: PipelineJob) -> None:
        if self._event_publisher is None:
            return
        try:
            self._event_publisher.publish({
                "event_type": event_type,
                "tenant_id": job.tenant_id,
                "content_id": job.content_id,
                "job_id": job.job_id,
                "job_type": job.job_type,
                "status": job.status,
                "output_keys": job.output_storage_keys,
                "error": job.error,
            })
        except Exception:  # noqa: BLE001
            pass  # event publish is best-effort; never blocks pipeline job

    @staticmethod
    def _utcnow() -> str:
        return datetime.now(timezone.utc).isoformat()

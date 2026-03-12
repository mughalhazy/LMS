"""Transcoding orchestration for media pipeline processing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, List

from .encoding_profiles import EncodingProfileRegistry
from .models import ProcessingJob, ProcessingStatus, RenditionResult, UploadPolicy
from .queue import ProcessingQueue
from .validation import MediaValidator


@dataclass
class PipelineEvents:
    upload_event: str = "video.uploaded"
    transcode_event: str = "video.transcoded"


class MediaTranscodingOrchestrator:
    """Coordinates validation, queueing, and transcoding operations."""

    def __init__(
        self,
        queue: ProcessingQueue,
        upload_policy: UploadPolicy,
        profile_registry: EncodingProfileRegistry | None = None,
        emitter: Callable[[str, Dict[str, object]], None] | None = None,
    ) -> None:
        self._queue = queue
        self._upload_policy = upload_policy
        self._profiles = profile_registry or EncodingProfileRegistry()
        self._emit = emitter or (lambda _event, _payload: None)
        self._events = PipelineEvents()

    def submit(self, job: ProcessingJob) -> ProcessingJob:
        validation = MediaValidator.validate(job.metadata, self._upload_policy)
        now = datetime.utcnow()

        if not validation.ok:
            job.status = ProcessingStatus.FAILED
            job.error = validation.reason
            job.updated_at = now
            return job

        job.status = ProcessingStatus.VALIDATED
        job.updated_at = now
        self._queue.enqueue(job)
        self._emit(self._events.upload_event, job.to_event_payload())
        return job

    def process_next(self) -> ProcessingJob | None:
        job = self._queue.dequeue()
        if job is None:
            return None

        job.status = ProcessingStatus.TRANSCODING
        job.updated_at = datetime.utcnow()

        try:
            resolved_profiles = self._profiles.resolve(job.target_profiles)
            job.renditions = self._transcode(job, resolved_profiles)
            job.status = ProcessingStatus.COMPLETED
            job.error = None
        except Exception as exc:  # defensive fail-safe for worker runtime
            job.status = ProcessingStatus.FAILED
            job.error = str(exc)
            job.renditions = []

        job.updated_at = datetime.utcnow()
        self._emit(self._events.transcode_event, job.to_event_payload())
        return job

    @staticmethod
    def _transcode(job: ProcessingJob, profiles: List) -> List[RenditionResult]:
        base_uri = job.source_uri.rsplit(".", 1)[0]
        renditions: List[RenditionResult] = []

        for profile in profiles:
            renditions.append(
                RenditionResult(
                    profile_name=profile.name,
                    uri=(
                        f"{base_uri}/{profile.name}/index.m3u8"
                    ),
                    bitrate_kbps=profile.video_bitrate_kbps,
                    width=profile.width,
                    height=profile.height,
                    duration_seconds=job.metadata.duration_seconds,
                )
            )

        return renditions

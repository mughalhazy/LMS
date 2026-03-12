from __future__ import annotations

"""Entrypoint helpers for embedding MediaPipelineService in an HTTP API layer.

This module intentionally avoids framework dependencies so the core pipeline can run
in constrained environments.
"""

from media_pipeline_service.integrations.cdn import CDNClient
from media_pipeline_service.integrations.events import EventPublisher
from media_pipeline_service.integrations.storage import ObjectStorageClient
from media_pipeline_service.integrations.transcoder import TranscoderClient
from media_pipeline_service.pipeline import MediaPipelineService


def build_service() -> MediaPipelineService:
    return MediaPipelineService(
        storage_client=ObjectStorageClient(),
        transcoder_client=TranscoderClient(),
        cdn_client=CDNClient(),
        event_publisher=EventPublisher(),
    )

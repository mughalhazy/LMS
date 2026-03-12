from __future__ import annotations

from typing import Dict, List

from media_pipeline_service.integrations.cdn import CDNClient
from media_pipeline_service.integrations.events import EventPublisher
from media_pipeline_service.integrations.storage import ObjectStorageClient
from media_pipeline_service.integrations.transcoder import TranscoderClient
from media_pipeline_service.models import (
    CDNDeliveryConfig,
    MediaAsset,
    PipelineResult,
    ProcessingStatus,
    ThumbnailRule,
    TranscodingRequest,
    UploadRequest,
)


class MediaPipelineService:
    def __init__(
        self,
        storage_client: ObjectStorageClient,
        transcoder_client: TranscoderClient,
        cdn_client: CDNClient,
        event_publisher: EventPublisher,
    ) -> None:
        self.storage_client = storage_client
        self.transcoder_client = transcoder_client
        self.cdn_client = cdn_client
        self.event_publisher = event_publisher
        self._asset_store: Dict[str, MediaAsset] = {}

    def upload_intake(self, request: UploadRequest) -> PipelineResult:
        if request.source_video_size_bytes > request.upload_policy.max_size_mb * 1024 * 1024:
            raise ValueError("source_video_size_bytes exceeds upload_policy.max_size_mb")

        storage_object = self.storage_client.upload_raw_video(
            tenant_id=request.uploader_metadata.tenant_id,
            media_asset_id="pending",
            source_filename=request.source_filename,
        )

        media_asset = MediaAsset(
            uploader_metadata=request.uploader_metadata,
            source_filename=request.source_filename,
            source_content_type=request.source_content_type,
            source_video_size_bytes=request.source_video_size_bytes,
            object_storage_uri=storage_object.uri.replace("/pending/", "/"),
            upload_checksum=storage_object.checksum_sha256,
        )
        media_asset.object_storage_uri = self.storage_client.upload_raw_video(
            tenant_id=request.uploader_metadata.tenant_id,
            media_asset_id=media_asset.media_asset_id,
            source_filename=request.source_filename,
        ).uri

        event = self.event_publisher.publish(
            "video.uploaded",
            media_asset.media_asset_id,
            {
                "object_storage_uri": media_asset.object_storage_uri,
                "upload_checksum": media_asset.upload_checksum,
            },
        )
        self._asset_store[media_asset.media_asset_id] = media_asset
        return PipelineResult(media_asset=media_asset, events=[event])

    def process_media(
        self,
        media_asset_id: str,
        transcoding_request: TranscodingRequest,
        thumbnail_rule: ThumbnailRule,
        cdn_config: CDNDeliveryConfig,
    ) -> PipelineResult:
        asset = self._asset_store[media_asset_id]
        events = []

        asset.status = ProcessingStatus.transcoding
        for profile in transcoding_request.target_profiles:
            manifest_uri = self.storage_client.store_streaming_manifest(
                asset.uploader_metadata.tenant_id,
                asset.media_asset_id,
                profile.name,
            )
            artifact = self.transcoder_client.transcode(asset.object_storage_uri, profile, manifest_uri)
            asset.adaptive_streaming_assets[profile.name] = artifact.manifest_uri
            asset.rendition_metadata[profile.name] = self.transcoder_client.metadata(artifact)

        asset.status = ProcessingStatus.transcoded
        events.append(
            self.event_publisher.publish(
                "video.transcoded",
                asset.media_asset_id,
                {
                    "transcoding_job_status": "completed",
                    "encoding_preset": transcoding_request.encoding_preset,
                },
            )
        )

        thumbs_per_format = max(1, 60 // max(1, thumbnail_rule.interval_seconds))
        for image_format in thumbnail_rule.formats:
            asset.thumbnail_set_uris[image_format] = [
                self.storage_client.store_thumbnail(
                    asset.uploader_metadata.tenant_id,
                    asset.media_asset_id,
                    image_format,
                    idx,
                )
                for idx in range(thumbs_per_format)
            ]

        asset.poster_image_uri = self.storage_client.store_poster(
            asset.uploader_metadata.tenant_id, asset.media_asset_id
        )
        asset.sprite_sheet_uri = self.storage_client.store_sprite_sheet(
            asset.uploader_metadata.tenant_id, asset.media_asset_id
        )
        asset.status = ProcessingStatus.thumbnails_generated
        events.append(
            self.event_publisher.publish(
                "video.thumbnails_generated",
                asset.media_asset_id,
                {
                    "poster_image_uri": asset.poster_image_uri,
                    "keyframe_selection": thumbnail_rule.keyframe_selection,
                },
            )
        )

        _ = cdn_config
        asset.cdn_playback_urls = self.cdn_client.publish_streaming_urls(asset.adaptive_streaming_assets)
        asset.cdn_thumbnail_urls = self.cdn_client.publish_thumbnail_urls(asset.thumbnail_set_uris)
        asset.status = ProcessingStatus.published
        events.append(
            self.event_publisher.publish(
                "video.published",
                asset.media_asset_id,
                {
                    "edge_cache_status": "warm",
                    "access_policy": cdn_config.access_policy,
                },
            )
        )
        return PipelineResult(media_asset=asset, events=events)

    def get_asset(self, media_asset_id: str) -> MediaAsset:
        return self._asset_store[media_asset_id]

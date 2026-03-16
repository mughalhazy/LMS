from __future__ import annotations

from datetime import datetime, timezone

from media_service.integrations.cdn import CDNClient
from media_service.integrations.events import EventPublisher
from media_service.integrations.storage import ObjectStorageClient
from media_service.integrations.transcoder import TranscoderClient
from media_service.models import (
    CDNDeliveryConfig,
    EventRecord,
    MediaAsset,
    MediaMetadata,
    ProcessingStatus,
    ThumbnailRule,
    TranscodingRequest,
    UploadRequest,
)


class MediaService:
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
        self._asset_store: dict[str, MediaAsset] = {}

    def upload_media(self, request: UploadRequest) -> tuple[MediaAsset, EventRecord]:
        if request.source_codec not in request.upload_policy.allowed_codecs:
            raise ValueError(f"source codec '{request.source_codec}' is not allowed")
        if request.source_video_size_bytes > request.upload_policy.max_size_mb * 1024 * 1024:
            raise ValueError("source_video_size_bytes exceeds upload_policy.max_size_mb")

        media_asset = MediaAsset(
            uploader_metadata=request.uploader_metadata,
            source_filename=request.source_filename,
            source_content_type=request.source_content_type,
            source_video_size_bytes=request.source_video_size_bytes,
            source_codec=request.source_codec,
            object_storage_uri="",
            upload_checksum="",
        )

        stored_object = self.storage_client.upload_raw_video(
            tenant_id=request.uploader_metadata.tenant_id,
            media_asset_id=media_asset.media_asset_id,
            source_filename=request.source_filename,
        )
        media_asset.object_storage_uri = stored_object.uri
        media_asset.upload_checksum = stored_object.checksum_sha256

        self._asset_store[media_asset.media_asset_id] = media_asset
        event = self.event_publisher.publish(
            "video.uploaded",
            request.uploader_metadata.tenant_id,
            media_asset.media_asset_id,
            {
                "object_storage_uri": media_asset.object_storage_uri,
                "upload_checksum": media_asset.upload_checksum,
            },
        )
        return media_asset, event

    def process_video(
        self,
        media_asset_id: str,
        transcoding_request: TranscodingRequest,
        thumbnail_rule: ThumbnailRule,
    ) -> tuple[MediaAsset, list[EventRecord]]:
        asset = self._asset_store[media_asset_id]
        events: list[EventRecord] = []

        asset.status = ProcessingStatus.transcoding
        for profile in transcoding_request.target_profiles:
            output_manifest = self.storage_client.store_streaming_manifest(
                tenant_id=asset.uploader_metadata.tenant_id,
                media_asset_id=media_asset_id,
                profile=profile.name,
            )
            artifact = self.transcoder_client.transcode(asset.object_storage_uri, profile, output_manifest)
            asset.adaptive_streaming_assets[profile.name] = artifact.manifest_uri
            asset.rendition_metadata[profile.name] = self.transcoder_client.metadata(artifact, profile)

        asset.status = ProcessingStatus.transcoded
        events.append(
            self.event_publisher.publish(
                "video.transcoded",
                asset.uploader_metadata.tenant_id,
                media_asset_id,
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
                    tenant_id=asset.uploader_metadata.tenant_id,
                    media_asset_id=media_asset_id,
                    image_format=image_format,
                    index=index,
                )
                for index in range(thumbs_per_format)
            ]

        asset.poster_image_uri = self.storage_client.store_poster(asset.uploader_metadata.tenant_id, media_asset_id)
        asset.sprite_sheet_uri = self.storage_client.store_sprite_sheet(asset.uploader_metadata.tenant_id, media_asset_id)
        asset.status = ProcessingStatus.thumbnails_generated
        events.append(
            self.event_publisher.publish(
                "video.thumbnails_generated",
                asset.uploader_metadata.tenant_id,
                media_asset_id,
                {
                    "poster_image_uri": asset.poster_image_uri,
                    "keyframe_selection": thumbnail_rule.keyframe_selection,
                },
            )
        )

        max_duration = max(item["duration_seconds"] for item in asset.rendition_metadata.values())
        asset.metadata = MediaMetadata(
            asset_id=asset.media_asset_id,
            title=asset.uploader_metadata.title,
            description=asset.uploader_metadata.description,
            language=asset.uploader_metadata.language,
            duration_seconds=int(max_duration),
            codec=asset.source_codec,
            resolution_ladder=[profile.name for profile in transcoding_request.target_profiles],
            bitrate_profiles={profile.name: profile.bitrate_kbps for profile in transcoding_request.target_profiles},
            checksum_sha256=asset.upload_checksum,
            drm_policy=transcoding_request.drm_policy,
            access_tier=asset.uploader_metadata.access_tier,
            tenant_id=asset.uploader_metadata.tenant_id,
            uploaded_by=asset.uploader_metadata.uploader_id,
            uploaded_at=asset.created_at,
            thumbnail_uri=asset.poster_image_uri,
        )

        return asset, events

    def publish_to_cdn(self, media_asset_id: str, config: CDNDeliveryConfig) -> tuple[MediaAsset, EventRecord]:
        asset = self._asset_store[media_asset_id]
        signed = config.access_policy in {"signed_url", "token"}
        asset.cdn_playback_urls = self.cdn_client.publish_streaming_urls(asset.adaptive_streaming_assets, signed=signed)
        asset.cdn_thumbnail_urls = self.cdn_client.publish_thumbnail_urls(asset.thumbnail_set_uris, signed=signed)
        asset.status = ProcessingStatus.published
        if asset.metadata is not None:
            asset.metadata.published_at = datetime.now(timezone.utc)

        event = self.event_publisher.publish(
            "video.published",
            asset.uploader_metadata.tenant_id,
            media_asset_id,
            {
                "edge_cache_status": "warm",
                "access_policy": config.access_policy,
            },
        )
        return asset, event

    def get_asset(self, media_asset_id: str) -> MediaAsset:
        return self._asset_store[media_asset_id]

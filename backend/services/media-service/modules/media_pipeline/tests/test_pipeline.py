from media_pipeline_service.integrations.cdn import CDNClient
from media_pipeline_service.integrations.events import EventPublisher
from media_pipeline_service.integrations.storage import ObjectStorageClient
from media_pipeline_service.integrations.transcoder import TranscoderClient
from media_pipeline_service.models import CDNDeliveryConfig, ThumbnailRule, TranscodingRequest, UploadRequest, UploaderMetadata
from media_pipeline_service.pipeline import MediaPipelineService


def build_service() -> MediaPipelineService:
    return MediaPipelineService(
        storage_client=ObjectStorageClient(),
        transcoder_client=TranscoderClient(),
        cdn_client=CDNClient(),
        event_publisher=EventPublisher(),
    )


def test_full_media_pipeline_generates_assets_and_events() -> None:
    service = build_service()
    upload = UploadRequest(
        source_filename="lesson-1.mp4",
        source_video_size_bytes=40 * 1024 * 1024,
        uploader_metadata=UploaderMetadata(
            uploader_id="user_1",
            title="Lesson 1",
            course_id="course_1",
            tenant_id="tenant_1",
        ),
    )
    upload_result = service.upload_intake(upload)
    media_asset_id = upload_result.media_asset.media_asset_id

    process_result = service.process_media(
        media_asset_id=media_asset_id,
        transcoding_request=TranscodingRequest(),
        thumbnail_rule=ThumbnailRule(interval_seconds=15),
        cdn_config=CDNDeliveryConfig(),
    )

    assert process_result.media_asset.status.value == "published"
    assert set(process_result.media_asset.adaptive_streaming_assets.keys()) == {"1080p", "720p", "480p"}
    assert "jpg" in process_result.media_asset.thumbnail_set_uris
    assert "webp" in process_result.media_asset.thumbnail_set_uris
    assert len(process_result.events) == 3
    assert [evt.event_type for evt in process_result.events] == [
        "video.transcoded",
        "video.thumbnails_generated",
        "video.published",
    ]

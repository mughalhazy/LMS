from media_service.main import build_service
from media_service.models import CDNDeliveryConfig, ThumbnailRule, TranscodingRequest, UploadRequest, UploaderMetadata


def test_media_service_upload_process_publish_pipeline() -> None:
    service = build_service()

    asset, upload_event = service.upload_media(
        UploadRequest(
            source_filename="module-7-overview.mp4",
            source_video_size_bytes=40 * 1024 * 1024,
            source_codec="h264",
            uploader_metadata=UploaderMetadata(
                uploader_id="author-1",
                title="Module 7 Overview",
                course_id="course-7",
                tenant_id="tenant-acme",
                description="Weekly overview lesson",
            ),
        )
    )

    processed_asset, processing_events = service.process_video(
        media_asset_id=asset.media_asset_id,
        transcoding_request=TranscodingRequest(),
        thumbnail_rule=ThumbnailRule(interval_seconds=15),
    )

    published_asset, publish_event = service.publish_to_cdn(
        media_asset_id=asset.media_asset_id,
        config=CDNDeliveryConfig(access_policy="signed_url", ttl_seconds=43200),
    )

    assert upload_event.event_name == "video.uploaded"
    assert upload_event.tenant_id == "tenant-acme"
    assert len(processed_asset.adaptive_streaming_assets) == 3
    assert [event.event_name for event in processing_events] == ["video.transcoded", "video.thumbnails_generated"]
    assert {event.tenant_id for event in processing_events} == {"tenant-acme"}
    assert processed_asset.metadata is not None
    assert processed_asset.metadata.duration_seconds >= 600
    assert processed_asset.metadata.thumbnail_uri is not None
    assert published_asset.status.value == "published"
    assert publish_event.event_name == "video.published"
    assert publish_event.tenant_id == "tenant-acme"
    assert all(url.startswith("https://cdn.lms.example.com/") for url in published_asset.cdn_playback_urls.values())
    assert all("?sig=mock-token" in url for url in published_asset.cdn_playback_urls.values())


def test_upload_rejects_disallowed_codec() -> None:
    service = build_service()

    try:
        service.upload_media(
            UploadRequest(
                source_filename="module-1.mkv",
                source_video_size_bytes=5 * 1024 * 1024,
                source_codec="av1",
                uploader_metadata=UploaderMetadata(
                    uploader_id="author-2",
                    title="Module 1",
                    course_id="course-1",
                    tenant_id="tenant-acme",
                ),
            )
        )
    except ValueError as exc:
        assert "not allowed" in str(exc)
    else:
        raise AssertionError("Expected upload_media to reject codec outside upload policy")

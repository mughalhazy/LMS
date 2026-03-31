from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

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
        config=CDNDeliveryConfig(access_policy="signed_url", ttl_seconds=43200, watermark_enabled=True),
    )

    assert upload_event.event_type == "video.uploaded"
    assert upload_event.tenant_id == "tenant-acme"
    assert len(processed_asset.adaptive_streaming_assets) == 3
    assert [event.event_type for event in processing_events] == ["video.transcoded", "video.thumbnails_generated"]
    assert {event.tenant_id for event in processing_events} == {"tenant-acme"}
    assert processed_asset.metadata is not None
    assert processed_asset.metadata.duration_seconds >= 600
    assert processed_asset.metadata.thumbnail_uri is not None
    assert published_asset.status.value == "published"
    assert publish_event.event_type == "video.published"
    assert publish_event.tenant_id == "tenant-acme"
    assert all(url.startswith("https://cdn.lms.example.com/") for url in published_asset.cdn_playback_urls.values())
    assert all("token=" in url and "exp=" in url for url in published_asset.cdn_playback_urls.values())

    playback_720p = published_asset.cdn_playback_urls["720p"]
    assert service.validate_playback_access(asset.media_asset_id, "720p", playback_720p) is True


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


def test_secure_stream_blocks_unauthorized_access_and_expired_tokens() -> None:
    service = build_service()
    asset, _ = service.upload_media(
        UploadRequest(
            source_filename="restricted.mp4",
            source_video_size_bytes=5 * 1024 * 1024,
            source_codec="h264",
            uploader_metadata=UploaderMetadata(
                uploader_id="author-3",
                title="Restricted",
                course_id="course-r",
                tenant_id="tenant-acme",
                access_tier="private",
            ),
        )
    )
    service.process_video(asset.media_asset_id, TranscodingRequest(), ThumbnailRule())
    published, _ = service.publish_to_cdn(
        asset.media_asset_id,
        CDNDeliveryConfig(ttl_seconds=120, access_policy="token", watermark_enabled=True),
    )

    playback_url = published.cdn_playback_urls["1080p"]
    parsed = urlparse(playback_url)
    query = parse_qs(parsed.query)

    assert query.get("wm")
    assert service.validate_playback_access(asset.media_asset_id, "1080p", playback_url) is True

    tampered_url = playback_url.replace("profile=1080p", "profile=480p")
    assert service.validate_playback_access(asset.media_asset_id, "1080p", tampered_url) is False

    exp = int(query["exp"][0])
    expired_now = datetime.fromtimestamp(exp, tz=timezone.utc) + timedelta(seconds=1)
    assert (
        service.security.validate_url(
            playback_url,
            tenant_id="tenant-acme",
            asset_id=asset.media_asset_id,
            profile="1080p",
            access_tier="private",
            now=expired_now,
        )
        is False
    )

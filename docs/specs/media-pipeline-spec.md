# Media Pipeline Specification

**Type:** Service Specification | **Last reviewed:** 2026-05-26

Four-stage media processing pipeline for video assets. Each stage transforms inputs into deliverable outputs.

---

| pipeline_stage | inputs | outputs |
|---|---|---|
| video_upload | source_video_file (mp4/mov/mkv), uploader_metadata (uploader_id, title, course_id), upload_policy (max_size, allowed_codecs) | object_storage_uri, upload_checksum, media_asset_id, upload_event (video.uploaded) |
| transcoding | media_asset_id, object_storage_uri, target_profiles (1080p/720p/480p), encoding_preset (h264/aac), drm_policy (optional) | adaptive_streaming_assets (HLS/DASH manifests + segments), transcoding_job_status, rendition_metadata (bitrate, resolution, duration), transcode_event (video.transcoded) |
| thumbnail_generation | media_asset_id, master_or_transcoded_video_uri, thumbnail_rules (interval_seconds, keyframe_selection), image_profile (jpg/webp sizes) | thumbnail_set_uris, poster_image_uri, sprite_sheet_uri (optional), thumbnail_event (video.thumbnails_generated) |
| cdn_delivery | adaptive_streaming_assets, thumbnail_set_uris, cache_policy (ttl, invalidation_rules), access_policy (signed_url/token) | cdn_playback_urls, cdn_thumbnail_urls, edge_cache_status, delivery_event (video.published) |


---

## See also
- `backend/services/media-service/README.md` � media service implementation
- `docs/contracts/media-security-interface-contract.md` � media security interface contract

pipeline_stage: video_upload
inputs: source_video_file (mp4/mov/mkv), uploader_metadata (uploader_id, title, course_id), upload_policy (max_size, allowed_codecs)
outputs: object_storage_uri, upload_checksum, media_asset_id, upload_event (video.uploaded)

pipeline_stage: transcoding
inputs: media_asset_id, object_storage_uri, target_profiles (1080p/720p/480p), encoding_preset (h264/aac), drm_policy (optional)
outputs: adaptive_streaming_assets (HLS/DASH manifests + segments), transcoding_job_status, rendition_metadata (bitrate, resolution, duration), transcode_event (video.transcoded)

pipeline_stage: thumbnail_generation
inputs: media_asset_id, master_or_transcoded_video_uri, thumbnail_rules (interval_seconds, keyframe_selection), image_profile (jpg/webp sizes)
outputs: thumbnail_set_uris, poster_image_uri, sprite_sheet_uri (optional), thumbnail_event (video.thumbnails_generated)

pipeline_stage: cdn_delivery
inputs: adaptive_streaming_assets, thumbnail_set_uris, cache_policy (ttl, invalidation_rules), access_policy (signed_url/token)
outputs: cdn_playback_urls, cdn_thumbnail_urls, edge_cache_status, delivery_event (video.published)

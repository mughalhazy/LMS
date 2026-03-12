content_type
storage_location
metadata_fields

videos
Object storage bucket (e.g., s3://lms-content-prod/videos/) fronted by CDN; originals in /raw, adaptive renditions (HLS/DASH) in /streaming, thumbnails in /thumbnails.
asset_id, title, description, language, duration_seconds, codec, resolution_ladder, bitrate_profiles, transcript_uri, caption_uris, thumbnail_uri, version, checksum_sha256, drm_policy, access_tier, tenant_id, uploaded_by, uploaded_at, published_at, retention_policy

documents
Object storage bucket (e.g., s3://lms-content-prod/documents/) with immutable versioned keys; optional search index stores extracted text pointers.
asset_id, title, description, file_type, file_size_bytes, page_count, language, extracted_text_uri, preview_uri, version, checksum_sha256, virus_scan_status, classification, tenant_id, tags, uploaded_by, uploaded_at, published_at, retention_policy

interactive modules
Object storage bucket (e.g., s3://lms-content-prod/interactive/) storing packaged web bundles; static assets served via CDN with signed URLs.
asset_id, module_name, description, launch_path, runtime_version, package_format, dependencies_manifest, supported_devices, estimated_duration_minutes, localization_locales, version, checksum_sha256, compatibility_matrix, sandbox_policy, tenant_id, tags, uploaded_by, uploaded_at, published_at

SCORM packages
Object storage bucket (e.g., s3://lms-content-prod/scorm/) storing uploaded ZIP + extracted manifest; registration and attempt state persisted in LMS relational DB.
asset_id, course_id, scorm_version, package_uri, manifest_uri, launch_sco, mastery_score, completion_criteria, sequencing_rules, suspend_data_limit, version, checksum_sha256, tenant_id, registration_count, uploaded_by, uploaded_at, published_at, deprecated_at

# Media Pipeline Service

Implements a media processing pipeline for LMS video assets:

1. **Media upload intake**: validates upload policy, stores raw asset, emits `video.uploaded`.
2. **Video transcoding pipeline**: creates adaptive renditions (`1080p`, `720p`, `480p`) and emits `video.transcoded`.
3. **Thumbnail generation**: produces thumbnails/poster/sprite outputs and emits `video.thumbnails_generated`.
4. **Storage integration**: writes to object-storage style URIs aligned with the LMS content storage model (`raw`, `streaming`, `thumbnails`).
5. **CDN delivery integration**: maps object URIs to CDN playback/thumbnail URLs and emits `video.published`.

## Run tests

```bash
cd backend/services/media-service/modules/media_pipeline
PYTHONPATH=src python -m pytest -q tests/test_pipeline.py
```

## Integration surface

- `media_pipeline_service.main.build_service()` constructs a ready-to-use pipeline service.
- HTTP/queue adapters can be added around the service methods:
  - `upload_intake(...)`
  - `process_media(...)`
  - `get_asset(...)`

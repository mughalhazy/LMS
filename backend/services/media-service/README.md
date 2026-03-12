# Media Service

Media Service implements LMS media lifecycle workflows aligned to the media pipeline and content storage model specifications.

> Stage-3 structure note: the media pipeline implementation now lives under `modules/media_pipeline`.

## Scope

- **Media upload pipeline**: validates upload policy (size, codec), stores raw source video under object storage `/videos/<tenant>/raw/<asset_id>/...`, and emits `video.uploaded`.
- **Video processing**: performs profile-based transcoding to adaptive outputs (`1080p`, `720p`, `480p`), generates thumbnails/poster/sprite assets, and emits `video.transcoded` and `video.thumbnails_generated`.
- **Media metadata**: persists derived media metadata (`duration_seconds`, `codec`, `resolution_ladder`, `bitrate_profiles`, `checksum_sha256`, tenant/uploader audit fields) for downstream search/catalog workflows.
- **CDN integration**: maps object storage artifacts to CDN playback/thumbnail URLs with optional signed access policy and emits `video.published`.

## Layout

- `modules/media_pipeline/`: Stage-3 media pipeline module (intake, transcoding, thumbnails, publishing).
- `src/media_service/models.py`: request/asset/metadata domain models.
- `src/media_service/service.py`: orchestrates upload, processing, metadata build, and CDN publishing.
- `src/media_service/integrations/`: object storage, transcoder, CDN, and event adapter stubs.
- `tests/test_media_service.py`: end-to-end pipeline and validation tests.
- `events/`: event contract examples.

## Run tests

```bash
cd backend/services/media-service
PYTHONPATH=src python -m pytest -q tests/test_media_service.py
```

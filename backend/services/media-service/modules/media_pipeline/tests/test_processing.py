import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "modules"))

from processing import (  # noqa: E402
    InMemoryProcessingQueue,
    MediaMetadata,
    MediaTranscodingOrchestrator,
    ProcessingJob,
    ProcessingStatus,
    UploadPolicy,
)


class TestMediaProcessing(unittest.TestCase):
    def setUp(self):
        self.policy = UploadPolicy(
            max_size_bytes=2_000_000_000,
            allowed_container_formats=["mp4", "mov", "mkv"],
            allowed_video_codecs=["h264", "hevc"],
            allowed_audio_codecs=["aac", "opus"],
        )
        self.queue = InMemoryProcessingQueue()

    def _metadata(self):
        return MediaMetadata(
            file_name="lesson-1.mp4",
            container_format="mp4",
            size_bytes=100_000_000,
            duration_seconds=120.5,
            video_codec="h264",
            audio_codec="aac",
            width=1920,
            height=1080,
        )

    def test_submit_and_process_success(self):
        events = []
        orchestrator = MediaTranscodingOrchestrator(
            queue=self.queue,
            upload_policy=self.policy,
            emitter=lambda event, payload: events.append((event, payload)),
        )

        job = ProcessingJob(
            media_asset_id="asset-123",
            source_uri="s3://lms-video-store/raw/asset-123.mp4",
            metadata=self._metadata(),
            target_profiles=["1080p", "720p", "480p"],
        )

        submitted = orchestrator.submit(job)
        self.assertEqual(submitted.status, ProcessingStatus.VALIDATED)
        self.assertEqual(len(self.queue), 1)

        processed = orchestrator.process_next()
        self.assertIsNotNone(processed)
        self.assertEqual(processed.status, ProcessingStatus.COMPLETED)
        self.assertEqual(len(processed.renditions), 3)
        self.assertEqual(events[0][0], "video.uploaded")
        self.assertEqual(events[1][0], "video.transcoded")

    def test_submit_invalid_media_fails_without_queueing(self):
        orchestrator = MediaTranscodingOrchestrator(
            queue=self.queue,
            upload_policy=self.policy,
        )
        bad_metadata = MediaMetadata(
            file_name="lesson-1.avi",
            container_format="avi",
            size_bytes=100_000_000,
            duration_seconds=120,
            video_codec="h264",
            audio_codec="aac",
            width=1920,
            height=1080,
        )
        job = ProcessingJob(
            media_asset_id="asset-124",
            source_uri="s3://lms-video-store/raw/asset-124.avi",
            metadata=bad_metadata,
            target_profiles=["720p"],
        )

        submitted = orchestrator.submit(job)
        self.assertEqual(submitted.status, ProcessingStatus.FAILED)
        self.assertIn("not allowed", submitted.error)
        self.assertEqual(len(self.queue), 0)


if __name__ == "__main__":
    unittest.main()

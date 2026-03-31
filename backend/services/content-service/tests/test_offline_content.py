from pathlib import Path
import tempfile
import unittest

from content_service.models import ContentType, MetadataPayload
from content_service.repository import ContentRepository
from content_service.service import ContentService
from offline import OfflineContentManager


class OfflineContentManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.service = ContentService(
            repository=ContentRepository(root / "content.db"),
            storage_root=root / "blobs",
        )
        self.offline = OfflineContentManager(cache_root=root / "offline-cache")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_downloads_and_persists_manifest(self) -> None:
        created = self.service.upload_content(
            tenant_id="tenant-a",
            content_type=ContentType.document,
            metadata=MetadataPayload(title="Handout"),
            binary_payload=b"offline-bytes",
        )

        record = self.offline.download_content(
            self.service,
            tenant_id="tenant-a",
            content_id=created.content_id,
            requester_user_id="u1",
            requester_roles=["learner"],
        )

        self.assertTrue(Path(record.local_uri).exists())
        self.assertEqual(Path(record.local_uri).read_bytes(), b"offline-bytes")
        lookup = self.offline.get_downloaded_content(created.content_id)
        self.assertIsNotNone(lookup)
        assert lookup is not None
        self.assertEqual(lookup.checksum_sha256, created.checksum_sha256)

    def test_reuses_existing_download_when_checksum_matches(self) -> None:
        created = self.service.upload_content(
            tenant_id="tenant-a",
            content_type=ContentType.document,
            metadata=MetadataPayload(title="Policy"),
            binary_payload=b"v1",
        )
        first = self.offline.download_content(
            self.service,
            tenant_id="tenant-a",
            content_id=created.content_id,
            requester_user_id="u1",
            requester_roles=["learner"],
        )
        second = self.offline.download_content(
            self.service,
            tenant_id="tenant-a",
            content_id=created.content_id,
            requester_user_id="u1",
            requester_roles=["learner"],
        )

        self.assertEqual(first.local_uri, second.local_uri)
        self.assertEqual(first.downloaded_at, second.downloaded_at)


if __name__ == "__main__":
    unittest.main()

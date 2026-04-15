from pathlib import Path
import tempfile
import unittest

from content_service.models import AccessPolicy, ContentType, MetadataPayload, Visibility
from content_service.repository import ContentRepository
from content_service.service import AccessDeniedError, ContentService


class ContentServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.service = ContentService(
            repository=ContentRepository(root / "content.db"),
            storage_root=root / "blobs",
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_upload_and_get_content(self):
        metadata = MetadataPayload(
            title="Intro Video",
            tags=["onboarding"],
        )
        created = self.service.upload_content(
            tenant_id="tenant-a",
            content_type=ContentType.video,
            metadata=metadata,
            binary_payload=b"hello",
        )

        fetched = self.service.get_content(
            tenant_id="tenant-a",
            content_id=created.content_id,
            requester_user_id="u1",
            requester_roles=["learner"],
        )
        self.assertEqual(fetched["metadata"].title, "Intro Video")

    def test_access_control_denies_unknown_user(self):
        metadata = MetadataPayload(
            title="Private Doc",
            access_policy=AccessPolicy(visibility=Visibility.private, allowed_user_ids=["author"]),
        )
        created = self.service.upload_content(
            tenant_id="tenant-a",
            content_type=ContentType.document,
            metadata=metadata,
            binary_payload=b"secret",
        )

        with self.assertRaises(AccessDeniedError):
            self.service.get_content(
                tenant_id="tenant-a",
                content_id=created.content_id,
                requester_user_id="u2",
                requester_roles=["learner"],
            )


if __name__ == "__main__":
    unittest.main()

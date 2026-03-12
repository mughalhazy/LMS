from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import Any, Dict, List

from .models import AccessPolicy, ContentMetadata, ContentType, MetadataPayload, MetadataUpdatePayload
from .repository import ContentRepository


class AccessDeniedError(Exception):
    pass


class NotFoundError(Exception):
    pass


class ContentService:
    def __init__(self, repository: ContentRepository, storage_root: Path) -> None:
        self.repository = repository
        self.storage_root = storage_root
        self.storage_root.mkdir(parents=True, exist_ok=True)

    def upload_content(self, tenant_id: str, content_type: ContentType, metadata: MetadataPayload, binary_payload: bytes) -> ContentMetadata:
        content_id = str(uuid.uuid4())
        extension = self._extension_for(content_type)
        tenant_dir = self.storage_root / tenant_id
        tenant_dir.mkdir(parents=True, exist_ok=True)
        blob_path = tenant_dir / f"{content_id}.v1.{extension}"
        blob_path.write_bytes(binary_payload)

        checksum = hashlib.sha256(binary_payload).hexdigest()
        created = self.repository.create(
            {
                "content_id": content_id,
                "tenant_id": tenant_id,
                "content_type": content_type.value,
                "storage_uri": str(blob_path),
                "version": 1,
                "checksum_sha256": checksum,
                **metadata.to_dict(),
            }
        )
        return ContentMetadata.from_dict(created)

    def update_metadata(self, tenant_id: str, content_id: str, payload: MetadataUpdatePayload) -> ContentMetadata:
        updated = self.repository.update(content_id, tenant_id, payload.to_updates())
        if not updated:
            raise NotFoundError(f"content_id={content_id} not found")
        return ContentMetadata.from_dict(updated)

    def get_content(self, tenant_id: str, content_id: str, requester_user_id: str, requester_roles: List[str]) -> Dict[str, Any]:
        item = self.repository.get(content_id, tenant_id)
        if not item:
            raise NotFoundError(f"content_id={content_id} not found")
        self._authorize(item["access_policy"], requester_user_id, requester_roles)
        return {"metadata": ContentMetadata.from_dict(item), "delivery_url": f"/content/{content_id}/download"}

    def list_content(self, tenant_id: str, requester_user_id: str, requester_roles: List[str], filters: Dict[str, Any]) -> List[ContentMetadata]:
        items = self.repository.list_for_tenant(tenant_id, filters)
        visible = []
        for item in items:
            try:
                self._authorize(item["access_policy"], requester_user_id, requester_roles)
                visible.append(ContentMetadata.from_dict(item))
            except AccessDeniedError:
                continue
        return visible

    @staticmethod
    def _authorize(access_policy_payload: Dict[str, Any], user_id: str, roles: List[str]) -> None:
        policy = AccessPolicy.from_dict(access_policy_payload)
        if policy.visibility.value in {"public", "tenant"}:
            return
        if user_id in policy.allowed_user_ids:
            return
        if any(role in policy.allowed_roles for role in roles):
            return
        raise AccessDeniedError("requester is not allowed to access this content")

    @staticmethod
    def _extension_for(content_type: ContentType) -> str:
        mapping = {
            ContentType.video: "mp4",
            ContentType.audio: "mp3",
            ContentType.document: "pdf",
            ContentType.scorm_package: "zip",
            ContentType.assessment_asset: "json",
        }
        return mapping[content_type]

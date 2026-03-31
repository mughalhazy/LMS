from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from content_service.service import ContentService


@dataclass
class OfflineContentRecord:
    content_id: str
    tenant_id: str
    version: int
    checksum_sha256: str
    source_uri: str
    local_uri: str
    downloaded_at: str


class OfflineContentManager:
    """Downloads and stores content for offline use with checksum validation."""

    def __init__(self, cache_root: Path) -> None:
        self.cache_root = cache_root
        self.cache_root.mkdir(parents=True, exist_ok=True)
        self._manifest_path = self.cache_root / "manifest.json"

    def download_content(
        self,
        content_service: ContentService,
        tenant_id: str,
        content_id: str,
        requester_user_id: str,
        requester_roles: list[str],
    ) -> OfflineContentRecord:
        content = content_service.get_content(tenant_id, content_id, requester_user_id, requester_roles)
        metadata = content["metadata"]
        source_path = Path(metadata.storage_uri)
        binary_payload = source_path.read_bytes()
        checksum = hashlib.sha256(binary_payload).hexdigest()

        if checksum != metadata.checksum_sha256:
            raise ValueError(f"checksum mismatch for content_id={content_id}")

        manifest = self._load_manifest()
        existing = manifest.get(content_id)
        if existing and existing["checksum_sha256"] == checksum and Path(existing["local_uri"]).exists():
            return OfflineContentRecord(**existing)

        offline_tenant_dir = self.cache_root / tenant_id
        offline_tenant_dir.mkdir(parents=True, exist_ok=True)
        extension = source_path.suffix
        offline_path = offline_tenant_dir / f"{content_id}.v{metadata.version}{extension}"
        self._safe_copy(source_path, offline_path)

        record = OfflineContentRecord(
            content_id=content_id,
            tenant_id=tenant_id,
            version=metadata.version,
            checksum_sha256=checksum,
            source_uri=str(source_path),
            local_uri=str(offline_path),
            downloaded_at=datetime.now(timezone.utc).isoformat(),
        )
        manifest[content_id] = record.__dict__.copy()
        self._write_manifest(manifest)
        return record

    def get_downloaded_content(self, content_id: str) -> OfflineContentRecord | None:
        manifest = self._load_manifest()
        payload = manifest.get(content_id)
        if not payload:
            return None
        offline_path = Path(payload["local_uri"])
        if not offline_path.exists():
            return None
        return OfflineContentRecord(**payload)

    def _load_manifest(self) -> Dict[str, Dict[str, Any]]:
        if not self._manifest_path.exists():
            return {}
        return json.loads(self._manifest_path.read_text(encoding="utf-8"))

    def _write_manifest(self, manifest: Dict[str, Dict[str, Any]]) -> None:
        tmp_path = self._manifest_path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
        tmp_path.replace(self._manifest_path)

    @staticmethod
    def _safe_copy(source: Path, target: Path) -> None:
        tmp_target = target.with_suffix(f"{target.suffix}.part")
        shutil.copy2(source, tmp_target)
        tmp_target.replace(target)

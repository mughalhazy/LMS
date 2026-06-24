from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .models import CapabilityRecord, RegistryDraft, RegistrySnapshot


class InMemoryCapabilityStore:
    def __init__(self) -> None:
        self._capabilities: Dict[str, CapabilityRecord] = {}
        self._snapshots: Dict[str, RegistrySnapshot] = {}
        self._drafts: Dict[str, RegistryDraft] = {}
        self._current_version: Optional[str] = None

    # --- capability CRUD ---

    def upsert(self, record: CapabilityRecord) -> None:
        self._capabilities[record.key] = record

    def get(self, key: str) -> Optional[CapabilityRecord]:
        return self._capabilities.get(key)

    def list_all(self) -> List[CapabilityRecord]:
        return list(self._capabilities.values())

    # --- draft management ---

    def create_draft(self, draft: RegistryDraft) -> None:
        self._drafts[draft.draft_id] = draft

    def get_draft(self, draft_id: str) -> Optional[RegistryDraft]:
        return self._drafts.get(draft_id)

    def update_draft_status(self, draft_id: str, status: str, errors: List[str] = None) -> None:
        draft = self._drafts.get(draft_id)
        if draft:
            draft.status = status
            if errors is not None:
                draft.validation_errors = errors

    # --- snapshot management ---

    def publish_snapshot(self) -> RegistrySnapshot:
        caps = dict(self._capabilities)
        dep_index: Dict[str, List[str]] = {k: list(v.dependencies) for k, v in caps.items()}
        rev_index: Dict[str, List[str]] = {k: [] for k in caps}
        for k, deps in dep_index.items():
            for d in deps:
                if d in rev_index:
                    rev_index[d].append(k)

        version = f"registry-v{datetime.now(timezone.utc).strftime('%Y.%m.%d')}.{secrets.token_hex(4)}"
        digest = hashlib.sha256(
            json.dumps({k: v.key for k, v in sorted(caps.items())}).encode()
        ).hexdigest()[:16]

        snapshot = RegistrySnapshot(
            version=version,
            capabilities=caps,
            dependency_index=dep_index,
            reverse_index=rev_index,
            published_at=datetime.now(timezone.utc),
            integrity_digest=digest,
        )
        self._snapshots[version] = snapshot
        self._current_version = version
        return snapshot

    def get_snapshot(self, version: str) -> Optional[RegistrySnapshot]:
        return self._snapshots.get(version)

    def current_snapshot(self) -> Optional[RegistrySnapshot]:
        if self._current_version:
            return self._snapshots.get(self._current_version)
        return None

    def get_dependency_graph(self) -> Dict[str, List[str]]:
        snap = self.current_snapshot()
        if snap:
            return snap.dependency_index
        return {k: list(v.dependencies) for k, v in self._capabilities.items()}

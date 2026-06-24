from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from .models import CapabilityRecord, RegistryDraft
from .store import InMemoryCapabilityStore

REQUIRED_FIELDS = {"key", "domain", "dependencies", "usage_metrics", "billing_type", "required_adapters"}
VALID_LIFECYCLE = {"draft", "active", "deprecated"}
VALID_BILLING = {"metered", "included", "add_on", "non_monetizable"}


class CapabilityRegistryService:
    def __init__(self, store: InMemoryCapabilityStore) -> None:
        self.store = store

    def get_capability(self, key: str, snapshot_version: str = None) -> Tuple[int, Dict[str, Any]]:
        if snapshot_version:
            snap = self.store.get_snapshot(snapshot_version)
            if snap is None:
                return 404, {"error": "snapshot_not_found", "version": snapshot_version}
            record = snap.capabilities.get(key)
        else:
            record = self.store.get(key)

        if record is None:
            return 404, {"error": "capability_not_found", "key": key}
        return 200, self._serialize(record)

    def list_capabilities(self, snapshot_version: str = None) -> Tuple[int, Dict[str, Any]]:
        if snapshot_version:
            snap = self.store.get_snapshot(snapshot_version)
            if snap is None:
                return 404, {"error": "snapshot_not_found"}
            records = list(snap.capabilities.values())
        else:
            records = self.store.list_all()

        return 200, {"capabilities": [self._serialize(r) for r in records], "count": len(records)}

    def get_dependency_graph(self, snapshot_version: str = None) -> Tuple[int, Dict[str, Any]]:
        if snapshot_version:
            snap = self.store.get_snapshot(snapshot_version)
            if snap is None:
                return 404, {"error": "snapshot_not_found"}
            return 200, {
                "graph": snap.dependency_index,
                "reverse": snap.reverse_index,
                "snapshot_version": snapshot_version,
            }
        graph = self.store.get_dependency_graph()
        return 200, {"graph": graph, "snapshot_version": None}

    def submit_draft(self, created_by: str, changes: List[Dict[str, Any]]) -> Tuple[int, Dict[str, Any]]:
        draft_id = f"draft-{secrets.token_urlsafe(8)}"
        draft = RegistryDraft(
            draft_id=draft_id,
            changes=changes,
            created_by=created_by,
            created_at=datetime.now(timezone.utc),
        )
        errors = self._validate_changes(changes)
        if errors:
            draft.status = "rejected"
            draft.validation_errors = errors
            self.store.create_draft(draft)
            return 422, {"draft_id": draft_id, "status": "rejected", "validation_errors": errors}

        draft.status = "validated"
        self.store.create_draft(draft)
        return 201, {"draft_id": draft_id, "status": "validated", "change_count": len(changes)}

    def publish_draft(self, draft_id: str) -> Tuple[int, Dict[str, Any]]:
        draft = self.store.get_draft(draft_id)
        if draft is None:
            return 404, {"error": "draft_not_found", "draft_id": draft_id}
        if draft.status != "validated":
            return 409, {"error": "draft_not_validated", "status": draft.status}

        now = datetime.now(timezone.utc)
        for change in draft.changes:
            record = CapabilityRecord(
                key=change["key"],
                domain=change.get("domain", ""),
                description=change.get("description", ""),
                dependencies=change.get("dependencies", []),
                usage_metrics=change.get("usage_metrics", []),
                billing_type=change.get("billing_type", "none"),
                required_adapters=change.get("required_adapters", []),
                lifecycle_status=change.get("lifecycle_status", "active"),
                owner=change.get("owner", ""),
                created_at=now,
                updated_at=now,
                created_by=draft.created_by,
                updated_by=draft.created_by,
                change_reason=change.get("change_reason", ""),
                add_on_refs=change.get("add_on_refs", []),
                activation_metadata=change.get("activation_metadata", {}),
            )
            self.store.upsert(record)

        snapshot = self.store.publish_snapshot()
        self.store.update_draft_status(draft_id, "published")

        return 200, {
            "snapshot_version": snapshot.version,
            "integrity_digest": snapshot.integrity_digest,
            "capability_count": len(snapshot.capabilities),
            "published_at": snapshot.published_at.isoformat(),
        }

    def get_snapshot(self, version: str) -> Tuple[int, Dict[str, Any]]:
        snap = self.store.get_snapshot(version)
        if snap is None:
            return 404, {"error": "snapshot_not_found", "version": version}
        return 200, {
            "version": snap.version,
            "capability_count": len(snap.capabilities),
            "published_at": snap.published_at.isoformat(),
            "integrity_digest": snap.integrity_digest,
        }

    def _validate_changes(self, changes: List[Dict[str, Any]]) -> List[str]:
        errors = []
        seen_keys = set()
        all_keys = {r.key for r in self.store.list_all()}

        for i, change in enumerate(changes):
            prefix = f"change[{i}]"

            # MS-CAP-01: all six required fields must be present and non-null
            for field in REQUIRED_FIELDS:
                if change.get(field) is None:
                    errors.append(f"{prefix}: missing required field '{field}' (MS-CAP-01)")

            key = change.get("key", "")

            # no duplicate keys within same draft
            if key in seen_keys:
                errors.append(f"{prefix}: duplicate key '{key}' in draft")
            seen_keys.add(key)

            # dependency keys must exist (in store or in this draft)
            candidate_keys = all_keys | seen_keys
            for dep in change.get("dependencies", []):
                if dep == key:
                    errors.append(f"{prefix}: self-dependency on '{key}'")
                elif dep not in candidate_keys:
                    errors.append(f"{prefix}: dependency '{dep}' does not exist in registry")

            # lifecycle must be valid
            lc = change.get("lifecycle_status", "active")
            if lc not in VALID_LIFECYCLE:
                errors.append(f"{prefix}: invalid lifecycle_status '{lc}'")

            # billing_type must be valid
            bt = change.get("billing_type", "")
            if bt not in VALID_BILLING:
                errors.append(f"{prefix}: invalid billing_type '{bt}'")

        # cycle detection
        graph = {c["key"]: c.get("dependencies", []) for c in changes if "key" in c}
        for existing in self.store.list_all():
            if existing.key not in graph:
                graph[existing.key] = existing.dependencies
        cycle = _detect_cycle(graph)
        if cycle:
            errors.append(f"dependency cycle detected involving: {', '.join(cycle)}")

        return errors

    def _serialize(self, record: CapabilityRecord) -> Dict[str, Any]:
        return {
            "key": record.key,
            "domain": record.domain,
            "description": record.description,
            "dependencies": record.dependencies,
            "usage_metrics": record.usage_metrics,
            "billing_type": record.billing_type,
            "required_adapters": record.required_adapters,
            "lifecycle_status": record.lifecycle_status,
            "owner": record.owner,
            "add_on_refs": record.add_on_refs,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
        }


def _detect_cycle(graph: Dict[str, List[str]]) -> List[str]:
    visited: set = set()
    in_stack: set = set()
    cycle_nodes: List[str] = []

    def dfs(node: str) -> bool:
        visited.add(node)
        in_stack.add(node)
        for neighbour in graph.get(node, []):
            if neighbour not in visited:
                if dfs(neighbour):
                    return True
            elif neighbour in in_stack:
                cycle_nodes.append(neighbour)
                return True
        in_stack.discard(node)
        return False

    for node in list(graph.keys()):
        if node not in visited:
            if dfs(node):
                break

    return cycle_nodes

from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4
import base64
import hashlib
import hmac


ROOT = Path(__file__).resolve().parents[2]


def _load_module(module_name: str, relative_path: str):
    module_path = ROOT / relative_path
    sys.path.append(str(module_path.parent))
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_ContentOfflineModule = _load_module("offline_sync_content_module", "backend/services/content-service/offline.py")
_ModelsModule = _load_module("offline_sync_models_module", "services/offline-sync/models.py")
_MediaSecurityModule = _load_module("offline_media_security_module", "services/media-security/service.py")
def _load_progress_module():
    package_name = "offline_sync_progress_src"
    package_path = ROOT / "backend/services/progress-service/src"
    package_spec = importlib.util.spec_from_file_location(
        package_name,
        package_path / "__init__.py",
        submodule_search_locations=[str(package_path)],
    )
    if package_spec is None or package_spec.loader is None:
        raise ImportError("Unable to initialize progress-service package")
    package_module = importlib.util.module_from_spec(package_spec)
    sys.modules[package_name] = package_module
    package_spec.loader.exec_module(package_module)

    module_spec = importlib.util.spec_from_file_location(
        f"{package_name}.progress_service",
        package_path / "progress_service.py",
    )
    if module_spec is None or module_spec.loader is None:
        raise ImportError("Unable to load progress_service module")
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)
    return module


_ProgressModule = _load_progress_module()

OfflineContentManager = _ContentOfflineModule.OfflineContentManager
OfflinePackage = _ModelsModule.OfflinePackage
MediaSecurityService = _MediaSecurityModule.MediaSecurityService
OfflineDownloadContext = _MediaSecurityModule.OfflineDownloadContext
ProgressTrackingService = _ProgressModule.ProgressTrackingService


@dataclass
class OfflineProgressEnvelope:
    operation_id: str
    tenant_id: str
    learner_id: str
    course_id: str
    lesson_id: str
    enrollment_id: str
    completion_status: str
    score: float | None
    time_spent_seconds: int
    attempt_count: int
    timestamp: str
    sync_attempts: int = 0
    last_error: str | None = None


class OfflineSyncService:
    """Offline downloads + progress sync with failure-safe retries and conflict resolution."""

    def __init__(
        self,
        *,
        cache_root: Path,
        state_file: Path,
        learning_service: ProgressTrackingService | None = None,
        media_security_service: MediaSecurityService | None = None,
        manifest_secret: str = "offline-package-signing-key",
        package_ttl_seconds: int = 86400,
    ) -> None:
        self.downloads = OfflineContentManager(cache_root=cache_root)
        self.learning_service = learning_service or ProgressTrackingService()
        self.media_security_service = media_security_service or MediaSecurityService()
        self._manifest_secret = manifest_secret.encode("utf-8")
        self._package_ttl_seconds = max(package_ttl_seconds, 1)
        self.state_file = state_file
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self._state = self._load_state()

    def download_for_offline(
        self,
        *,
        content_service: Any,
        tenant_id: str,
        content_id: str,
        requester_user_id: str,
        requester_roles: list[str],
    ) -> Any:
        return self.downloads.download_content(
            content_service=content_service,
            tenant_id=tenant_id,
            content_id=content_id,
            requester_user_id=requester_user_id,
            requester_roles=requester_roles,
        )

    def prepare_offline_package(
        self,
        *,
        tenant_id: str,
        student_id: str,
        content_ids: list[str],
        requester_user_id: str,
        requester_roles: list[str],
        tenant_plan_type: str,
        metadata: dict[str, str] | None = None,
        expires_in_seconds: int | None = None,
    ) -> OfflinePackage:
        auth = self.authorize_offline_download(
            tenant_id=tenant_id,
            student_id=student_id,
            requester_user_id=requester_user_id,
            requester_roles=requester_roles,
            tenant_plan_type=tenant_plan_type,
            requested_content_ids=content_ids,
        )
        if auth["decision"] != "allow":
            raise PermissionError(f"offline package denied: {auth['reason_code']}")

        issued_at = datetime.now(timezone.utc)
        ttl_seconds = self._package_ttl_seconds if expires_in_seconds is None else max(expires_in_seconds, 1)
        expires_at = issued_at + timedelta(seconds=ttl_seconds)
        package_id = str(uuid4())
        sync_token = str(uuid4())
        normalized_content_ids = sorted({content_id.strip() for content_id in content_ids if content_id.strip()})

        manifest_payload = {
            "package_id": package_id,
            "student_id": student_id.strip(),
            "tenant_id": tenant_id.strip(),
            "content_ids": normalized_content_ids,
            "issued_at": issued_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "sync_token": sync_token,
            "metadata": metadata or {},
        }
        encrypted_manifest = self._seal_manifest(manifest_payload)
        package = OfflinePackage(
            package_id=package_id,
            student_id=student_id.strip(),
            tenant_id=tenant_id.strip(),
            content_ids=normalized_content_ids,
            encrypted_manifest=encrypted_manifest,
            issued_at=issued_at.isoformat(),
            expires_at=expires_at.isoformat(),
            sync_token=sync_token,
            metadata=metadata or {},
        )
        self._state["packages"][package.package_id] = asdict(package)
        self._persist_state()
        return package

    def authorize_offline_download(
        self,
        *,
        tenant_id: str,
        student_id: str,
        requester_user_id: str,
        requester_roles: list[str],
        tenant_plan_type: str,
        requested_content_ids: list[str],
        package_id: str | None = None,
    ) -> dict[str, str | bool]:
        if requester_user_id.strip() != student_id.strip() and "admin" not in {role.strip().lower() for role in requester_roles}:
            return {"decision": "deny", "reason_code": "UNAUTHORIZED_REQUESTER"}

        media_auth = self.media_security_service.authorize_offline_download(
            context=OfflineDownloadContext(
                tenant_id=tenant_id,
                user_id=student_id,
                package_id=package_id or "",
                content_ids=requested_content_ids,
                roles=requester_roles,
            ),
            tenant_plan_type=tenant_plan_type,
        )
        if media_auth.decision != "allow":
            return {"decision": "deny", "reason_code": media_auth.reason_code}

        if package_id:
            package = self._state["packages"].get(package_id)
            if not package:
                return {"decision": "deny", "reason_code": "PACKAGE_NOT_FOUND"}
            if package.get("student_id") != student_id.strip() or package.get("tenant_id") != tenant_id.strip():
                return {"decision": "deny", "reason_code": "PACKAGE_SUBJECT_MISMATCH"}
            if datetime.fromisoformat(str(package["expires_at"])) <= datetime.now(timezone.utc):
                return {"decision": "deny", "reason_code": "PACKAGE_EXPIRED"}
            if package_id in self._state["invalidated_package_ids"]:
                return {"decision": "deny", "reason_code": "PACKAGE_INVALIDATED"}

        return {"decision": "allow", "reason_code": "", "policy_ref": media_auth.policy_ref}

    def invalidate_offline_package(self, *, package_id: str) -> bool:
        if package_id not in self._state["packages"]:
            return False
        self._state["invalidated_package_ids"].append(package_id)
        self._state["invalidated_package_ids"] = sorted(set(self._state["invalidated_package_ids"]))
        self._persist_state()
        return True

    def queue_progress(
        self,
        *,
        tenant_id: str,
        learner_id: str,
        course_id: str,
        lesson_id: str,
        enrollment_id: str,
        completion_status: str,
        score: float | None,
        time_spent_seconds: int,
        attempt_count: int,
        timestamp: datetime | None = None,
        operation_id: str | None = None,
    ) -> OfflineProgressEnvelope:
        envelope = OfflineProgressEnvelope(
            operation_id=operation_id or str(uuid4()),
            tenant_id=tenant_id,
            learner_id=learner_id,
            course_id=course_id,
            lesson_id=lesson_id,
            enrollment_id=enrollment_id,
            completion_status=completion_status,
            score=score,
            time_spent_seconds=time_spent_seconds,
            attempt_count=attempt_count,
            timestamp=(timestamp or datetime.now(timezone.utc)).isoformat(),
        )
        self._state["pending"].append(asdict(envelope))
        self._persist_state()
        return envelope

    def pending_operations(self) -> list[OfflineProgressEnvelope]:
        rows = sorted(self._state["pending"], key=lambda row: (row["timestamp"], row["operation_id"]))
        return [OfflineProgressEnvelope(**row) for row in rows]

    def sync_progress(self, *, server_learning_service: ProgressTrackingService | None = None) -> dict[str, Any]:
        server = server_learning_service or self.learning_service
        pending = self.pending_operations()

        succeeded = 0
        conflicts = 0
        failed: list[dict[str, str]] = []
        still_pending: list[dict[str, Any]] = []

        for op in pending:
            if op.operation_id in self._state["applied_operation_ids"]:
                continue

            try:
                resolution = self._resolve_conflict(op=op, server=server)
                if resolution == "drop_as_conflict":
                    conflicts += 1
                    self._state["applied_operation_ids"].append(op.operation_id)
                    self._state["conflicts"].append(
                        {
                            "operation_id": op.operation_id,
                            "tenant_id": op.tenant_id,
                            "learner_id": op.learner_id,
                            "course_id": op.course_id,
                            "lesson_id": op.lesson_id,
                            "strategy": "server_wins_due_to_fresher_remote_update",
                            "at": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                    continue

                server.track_lesson_completion(
                    tenant_id=op.tenant_id,
                    learner_id=op.learner_id,
                    course_id=op.course_id,
                    lesson_id=op.lesson_id,
                    enrollment_id=op.enrollment_id,
                    completion_status=op.completion_status,
                    score=op.score,
                    time_spent_seconds=op.time_spent_seconds,
                    attempt_count=op.attempt_count,
                )
                self._state["applied_operation_ids"].append(op.operation_id)
                succeeded += 1
            except Exception as exc:  # nosec - failure-safe retry queue
                op.sync_attempts += 1
                row = asdict(op)
                row["last_error"] = str(exc)
                still_pending.append(row)
                failed.append({"operation_id": op.operation_id, "error": str(exc)})

        self._state["pending"] = still_pending
        self._state["applied_operation_ids"] = sorted(set(self._state["applied_operation_ids"]))
        self._persist_state()

        return {
            "attempted": len(pending),
            "succeeded": succeeded,
            "conflicts": conflicts,
            "failed": failed,
            "pending": len(still_pending),
        }

    def _resolve_conflict(self, *, op: OfflineProgressEnvelope, server: ProgressTrackingService) -> str:
        snapshot = server.get_learner_progress(op.tenant_id, op.learner_id)
        lesson = snapshot.get("lessons", {}).get(op.course_id, {}).get(op.lesson_id)
        if not lesson:
            return "apply"

        remote_attempt_count = int(lesson.get("attempt_count") or 0)
        remote_status = str(lesson.get("completion_status") or "")

        remote_completed_at = lesson.get("completed_at")
        local_time = datetime.fromisoformat(op.timestamp)
        if local_time.tzinfo is not None:
            local_time = local_time.astimezone(timezone.utc).replace(tzinfo=None)

        remote_completed_dt: datetime | None = None
        if isinstance(remote_completed_at, datetime):
            remote_completed_dt = remote_completed_at
        elif isinstance(remote_completed_at, str) and remote_completed_at:
            remote_completed_dt = datetime.fromisoformat(remote_completed_at)
        if remote_completed_dt and remote_completed_dt.tzinfo is not None:
            remote_completed_dt = remote_completed_dt.astimezone(timezone.utc).replace(tzinfo=None)

        if remote_completed_dt and remote_completed_dt > local_time and remote_status == "completed":
            return "drop_as_conflict"

        if remote_attempt_count > op.attempt_count and remote_status == "completed":
            return "drop_as_conflict"

        return "apply"

    def _load_state(self) -> dict[str, Any]:
        if not self.state_file.exists():
            return {"pending": [], "applied_operation_ids": [], "conflicts": [], "packages": {}, "invalidated_package_ids": []}

        payload = json.loads(self.state_file.read_text(encoding="utf-8"))
        payload.setdefault("pending", [])
        payload.setdefault("applied_operation_ids", [])
        payload.setdefault("conflicts", [])
        payload.setdefault("packages", {})
        payload.setdefault("invalidated_package_ids", [])
        return payload

    def _persist_state(self) -> None:
        tmp_file = self.state_file.with_suffix(".tmp")
        tmp_file.write_text(json.dumps(self._state, indent=2, sort_keys=True), encoding="utf-8")
        tmp_file.replace(self.state_file)

    def _seal_manifest(self, payload: dict[str, Any]) -> str:
        serialized = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        digest = hashlib.sha256(serialized).hexdigest()
        wrapped = json.dumps({"digest": digest, "payload": payload}, separators=(",", ":"), sort_keys=True).encode("utf-8")
        encoded = base64.urlsafe_b64encode(wrapped).decode("utf-8")
        signature = hmac.new(self._manifest_secret, encoded.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"{encoded}.{signature}"


__all__ = ["OfflinePackage", "OfflineProgressEnvelope", "OfflineSyncService"]

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class OfflinePackage:
    package_id: str
    student_id: str
    tenant_id: str
    content_ids: list[str]
    encrypted_manifest: str
    issued_at: str
    expires_at: str
    sync_token: str
    metadata: dict[str, str] = field(default_factory=dict)


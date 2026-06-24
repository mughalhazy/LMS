from __future__ import annotations

import secrets
from typing import Dict, List, Optional

from .models import AuditRecord, PolicyBundle, PolicyDecision


class InMemoryAuditStore:
    def __init__(self) -> None:
        self._bundles: Dict[str, PolicyBundle] = {}
        self._active_bundle_id: Optional[str] = None
        self._decisions: Dict[str, PolicyDecision] = {}
        self._records: List[AuditRecord] = []
        self._last_hash: str = "genesis"

    # Policy bundles
    def save_bundle(self, bundle: PolicyBundle) -> None:
        self._bundles[bundle.bundle_id] = bundle

    def activate_bundle(self, bundle_id: str) -> bool:
        if bundle_id not in self._bundles:
            return False
        self._active_bundle_id = bundle_id
        return True

    def active_bundle(self) -> Optional[PolicyBundle]:
        if self._active_bundle_id:
            return self._bundles.get(self._active_bundle_id)
        return None

    # Decisions
    def save_decision(self, decision: PolicyDecision) -> None:
        self._decisions[decision.decision_id] = decision

    def get_decision(self, decision_id: str) -> Optional[PolicyDecision]:
        return self._decisions.get(decision_id)

    # Audit records — append-only
    def append_record(self, record: AuditRecord) -> None:
        record.prev_hash = self._last_hash
        record.record_hash = self._compute_hash(record)
        self._last_hash = record.record_hash
        self._records.append(record)

    def query_records(self, tenant_id: str, event_type: Optional[str] = None,
                      from_dt: Optional[str] = None, to_dt: Optional[str] = None) -> List[AuditRecord]:
        results = [r for r in self._records if r.tenant_id == tenant_id]
        if event_type:
            results = [r for r in results if r.event_type == event_type]
        return results

    def get_record(self, record_id: str) -> Optional[AuditRecord]:
        return next((r for r in self._records if r.record_id == record_id), None)

    def new_id(self, prefix: str = "") -> str:
        return f"{prefix}-{secrets.token_urlsafe(8)}" if prefix else secrets.token_urlsafe(10)

    @staticmethod
    def _compute_hash(record: AuditRecord) -> str:
        import hashlib
        data = f"{record.event_id}:{record.tenant_id}:{record.action}:{record.prev_hash}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock
from typing import Any, Deque, Dict, List


@dataclass
class InMemoryEventStore:
    """In-memory append-only storage model for raw, validated, and rejected events."""

    max_events_per_tenant: int = 50000

    def __post_init__(self) -> None:
        self._raw_by_tenant: Dict[str, Deque[Dict[str, Any]]] = defaultdict(
            lambda: deque(maxlen=self.max_events_per_tenant)
        )
        self._validated_by_tenant: Dict[str, Deque[Dict[str, Any]]] = defaultdict(
            lambda: deque(maxlen=self.max_events_per_tenant)
        )
        self._rejected_by_tenant: Dict[str, Deque[Dict[str, Any]]] = defaultdict(
            lambda: deque(maxlen=self.max_events_per_tenant)
        )
        self._lock = Lock()

    def append_raw(self, tenant_id: str, event: Dict[str, Any]) -> None:
        with self._lock:
            self._raw_by_tenant[tenant_id].append(event)

    def append_validated(self, tenant_id: str, event: Dict[str, Any]) -> None:
        with self._lock:
            self._validated_by_tenant[tenant_id].append(event)

    def append_rejected(self, tenant_id: str, event: Dict[str, Any]) -> None:
        with self._lock:
            self._rejected_by_tenant[tenant_id].append(event)

    def get_tenant_stream(self, tenant_id: str) -> Dict[str, List[Dict[str, Any]]]:
        with self._lock:
            return {
                "raw": list(self._raw_by_tenant[tenant_id]),
                "validated": list(self._validated_by_tenant[tenant_id]),
                "rejected": list(self._rejected_by_tenant[tenant_id]),
            }

    def get_ingestion_metrics(self) -> Dict[str, int]:
        with self._lock:
            return {
                "raw_events": sum(len(stream) for stream in self._raw_by_tenant.values()),
                "validated_events": sum(
                    len(stream) for stream in self._validated_by_tenant.values()
                ),
                "rejected_events": sum(
                    len(stream) for stream in self._rejected_by_tenant.values()
                ),
                "tenant_streams": len(
                    {
                        *self._raw_by_tenant.keys(),
                        *self._validated_by_tenant.keys(),
                        *self._rejected_by_tenant.keys(),
                    }
                ),
            }

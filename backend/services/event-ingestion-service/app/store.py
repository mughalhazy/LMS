from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Dict, List

from .models import AuditLogEntry, EventRecord


class EventStorage(ABC):
    """Contract for tenant-aware event storage owned by this service only."""

    @abstractmethod
    def persist(self, record: EventRecord) -> EventRecord:
        raise NotImplementedError

    @abstractmethod
    def list_by_tenant(self, tenant_id: str) -> List[EventRecord]:
        raise NotImplementedError

    @abstractmethod
    def health(self) -> bool:
        raise NotImplementedError


class AuditStorage(ABC):
    @abstractmethod
    def append(self, entry: AuditLogEntry) -> AuditLogEntry:
        raise NotImplementedError

    @abstractmethod
    def list_by_tenant(self, tenant_id: str) -> List[AuditLogEntry]:
        raise NotImplementedError


class InMemoryEventStorage(EventStorage):
    def __init__(self) -> None:
        self._records: Dict[str, List[EventRecord]] = defaultdict(list)

    def persist(self, record: EventRecord) -> EventRecord:
        self._records[record.event.tenant_id].append(record)
        return record

    def list_by_tenant(self, tenant_id: str) -> List[EventRecord]:
        return list(self._records.get(tenant_id, []))

    def health(self) -> bool:
        return True


class InMemoryAuditStorage(AuditStorage):
    def __init__(self) -> None:
        self._entries: Dict[str, List[AuditLogEntry]] = defaultdict(list)

    def append(self, entry: AuditLogEntry) -> AuditLogEntry:
        self._entries[entry.tenant_id].append(entry)
        return entry

    def list_by_tenant(self, tenant_id: str) -> List[AuditLogEntry]:
        return list(self._entries.get(tenant_id, []))

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

    def get_by_event_id(self, tenant_id: str, event_id: str) -> "EventRecord | None":
        for rec in self._records.get(tenant_id, []):
            if rec.event.event_id == event_id:
                return rec
        return None

    def query_by_filter(self, tenant_id: str, event_type: str | None,
                        from_ts: str | None, to_ts: str | None,
                        tags: list[str] | None) -> "List[EventRecord]":
        from datetime import datetime, timezone
        records = self._records.get(tenant_id, [])
        results = []
        for rec in records:
            ev = rec.event
            if event_type and ev.event_type != event_type:
                continue
            if from_ts:
                ft = datetime.fromisoformat(from_ts).astimezone(timezone.utc)
                if ev.ingested_at < ft:
                    continue
            if to_ts:
                tt = datetime.fromisoformat(to_ts).astimezone(timezone.utc)
                if ev.ingested_at > tt:
                    continue
            if tags and not set(tags).issubset(set(ev.tags)):
                continue
            results.append(rec)
        return results

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

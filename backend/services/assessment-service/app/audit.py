from __future__ import annotations

from dataclasses import asdict
from typing import Any


class AuditLogger:
    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    def log(self, record: dict[str, Any]) -> None:
        self.records.append(record)

    def snapshot(self) -> list[dict[str, Any]]:
        return [asdict(item) if hasattr(item, "__dataclass_fields__") else dict(item) for item in self.records]

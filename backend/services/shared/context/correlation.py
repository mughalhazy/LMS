from __future__ import annotations

from uuid import uuid4


def ensure_correlation_id(correlation_id: str | None) -> str:
    return correlation_id or str(uuid4())

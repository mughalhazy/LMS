from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Optional

from .models import FlagDefinition


class InMemoryFlagStore:
    def __init__(self) -> None:
        self._flags: Dict[str, FlagDefinition] = {}
        self._snapshot_version = "snap-1"

    def save_flag(self, flag: FlagDefinition) -> None:
        flag.updated_at = datetime.now(timezone.utc)
        self._flags[flag.feature_key] = flag

    def get_flag(self, feature_key: str) -> Optional[FlagDefinition]:
        return self._flags.get(feature_key)

    def list_flags(self) -> list:
        return list(self._flags.values())

    def snapshot_version(self) -> str:
        return self._snapshot_version

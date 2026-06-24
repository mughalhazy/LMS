from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .models import ConfigEntry, ConfigLayer


class InMemoryLayerStore:
    """LayerProviderPort implementation — storage-agnostic layer retrieval."""

    def __init__(self) -> None:
        self._entries: List[ConfigEntry] = []
        self._revision = "rev-initial"

    def seed(self, entries: List[ConfigEntry]) -> None:
        self._entries.extend(entries)

    def get_global_layer(self, keys: Optional[List[str]] = None) -> ConfigLayer:
        return self._build_layer("global", keys, lambda e: e.level == "global")

    def get_country_layer(self, country_code: str, keys: Optional[List[str]] = None) -> ConfigLayer:
        return self._build_layer(
            "country", keys,
            lambda e: e.level == "country" and e.country_code == country_code,
        )

    def get_segment_layer(self, segment_key: str, keys: Optional[List[str]] = None) -> ConfigLayer:
        return self._build_layer(
            "segment", keys,
            lambda e: e.level == "segment" and e.segment_key == segment_key,
        )

    def get_plan_layer(self, plan_key: str, keys: Optional[List[str]] = None) -> ConfigLayer:
        return self._build_layer(
            "plan", keys,
            lambda e: e.level == "plan" and e.plan_key == plan_key,
        )

    def get_tenant_layer(self, tenant_id: str, keys: Optional[List[str]] = None) -> ConfigLayer:
        return self._build_layer(
            "tenant", keys,
            lambda e: e.level == "tenant" and e.tenant_id == tenant_id,
        )

    def _build_layer(self, level: str, keys: Optional[List[str]], predicate) -> ConfigLayer:
        matched = {e.key: e.value for e in self._entries if predicate(e)}
        if keys is not None:
            matched = {k: v for k, v in matched.items() if k in keys}
        return ConfigLayer(
            level=level,
            values=matched,
            revision=self._revision,
            fetched_at=datetime.now(timezone.utc),
        )

    def get_capability_keys(self, capability_key: str) -> List[str]:
        return [e.key for e in self._entries if e.capability_key == capability_key]

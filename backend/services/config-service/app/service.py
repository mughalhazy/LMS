from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .models import ResolutionResult, RuntimeOverride
from .schemas import ResolutionContext
from .store import InMemoryLayerStore


class ConfigService:
    def __init__(self, store: InMemoryLayerStore) -> None:
        self.store = store
        self._overrides: Dict[str, RuntimeOverride] = {}

    def resolve_key(self, context: ResolutionContext, key: str) -> Tuple[int, Dict[str, Any]]:
        result = self._resolve(context, keys=[key])
        if key not in result.values:
            return 404, {"error": "key_not_found", "key": key}
        return 200, {
            "key": key,
            "value": result.values[key],
            "provenance": result.provenance.get(key),
            "resolved_at": result.resolved_at.isoformat(),
        }

    def resolve_keys(self, context: ResolutionContext, keys: List[str]) -> Tuple[int, Dict[str, Any]]:
        result = self._resolve(context, keys=keys)
        return 200, {
            "values": result.values,
            "provenance": result.provenance,
            "applied_levels": result.applied_levels,
            "revisions": result.revisions,
            "resolved_at": result.resolved_at.isoformat(),
        }

    def resolve_namespace(self, context: ResolutionContext, namespace: str) -> Tuple[int, Dict[str, Any]]:
        result = self._resolve(context, namespace=namespace)
        return 200, {
            "namespace": namespace,
            "values": result.values,
            "provenance": result.provenance,
            "applied_levels": result.applied_levels,
            "revisions": result.revisions,
            "resolved_at": result.resolved_at.isoformat(),
        }

    def _resolve(
        self,
        context: ResolutionContext,
        keys: Optional[List[str]] = None,
        namespace: Optional[str] = None,
    ) -> ResolutionResult:
        effective: Dict[str, Any] = {}
        provenance: Dict[str, str] = {}
        applied_levels: List[str] = []
        revisions: Dict[str, str] = {}

        layers = [
            self.store.get_global_layer(keys),
            self.store.get_country_layer(context.country_code, keys),
            self.store.get_segment_layer(context.segment_key, keys),
            self.store.get_plan_layer(context.plan_key, keys),
            self.store.get_tenant_layer(context.tenant_id, keys),
        ]

        for layer in layers:
            filtered = layer.values
            if namespace:
                filtered = {k: v for k, v in filtered.items() if k.startswith(namespace + ".")}
            if filtered:
                applied_levels.append(layer.level)
                revisions[layer.level] = layer.revision
            for k, v in filtered.items():
                effective[k] = v
                provenance[k] = layer.level

        # runtime overrides — highest precedence, ephemeral
        active_overrides = self._active_overrides()
        if active_overrides:
            for k, override in active_overrides.items():
                if keys is None or k in keys:
                    if namespace is None or k.startswith(namespace + "."):
                        effective[k] = override.value
                        provenance[k] = "override"
            if active_overrides:
                applied_levels.append("override")

        # capability projection
        if context.capability_key:
            cap_keys = set(self.store.get_capability_keys(context.capability_key))
            effective = {k: v for k, v in effective.items() if k in cap_keys}
            provenance = {k: v for k, v in provenance.items() if k in cap_keys}

        return ResolutionResult(
            values=effective,
            provenance=provenance,
            applied_levels=applied_levels,
            revisions=revisions,
            resolved_at=datetime.now(timezone.utc),
        )

    def _active_overrides(self) -> Dict[str, RuntimeOverride]:
        now = datetime.now(timezone.utc)
        active = {}
        for k, o in self._overrides.items():
            age = (now - o.created_at.replace(tzinfo=timezone.utc)).total_seconds()
            if age <= o.ttl_seconds:
                active[k] = o
        return active

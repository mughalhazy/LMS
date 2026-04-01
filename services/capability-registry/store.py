from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2]))

from shared.models.capability import Capability

_REGISTRY_PATH = Path(__file__).with_name("capabilities.json")


def _parse_price(value: object) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def _parse_string_list(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(
        item.strip().lower()
        for item in value
        if isinstance(item, str) and item.strip()
    )


def _parse_metadata(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    metadata: dict[str, str] = {}
    for key, item in value.items():
        normalized_key = str(key).strip()
        normalized_value = str(item).strip()
        if normalized_key and normalized_value:
            metadata[normalized_key] = normalized_value
    return metadata


@lru_cache(maxsize=1)
def _registry_payload() -> dict[str, object]:
    payload = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("capability registry payload must be an object")
    return payload


@lru_cache(maxsize=1)
def capability_index() -> dict[str, Capability]:
    payload = _registry_payload()
    raw_capabilities = payload.get("capabilities", [])
    if not isinstance(raw_capabilities, list):
        raise ValueError("capabilities must be a list")

    index: dict[str, Capability] = {}
    for item in raw_capabilities:
        if not isinstance(item, dict):
            continue
        capability = Capability(
            capability_id=str(item.get("capability_id", "")).strip(),
            name=str(item.get("name", "")).strip(),
            description=str(item.get("description", "")).strip(),
            category=str(item.get("category", "")).strip(),
            default_enabled=bool(item.get("default_enabled", False)),
            monetizable=bool(item.get("monetizable", True)),
            usage_metered=bool(item.get("usage_metered", item.get("usage_based", False))),
            metadata=_parse_metadata(item.get("metadata", {})),
            price=_parse_price(item.get("price", "0")),
            usage_based=bool(item.get("usage_metered", item.get("usage_based", False))),
            included_in_plans=_parse_string_list(item.get("included_in_plans", [])),
            included_in_add_ons=_parse_string_list(item.get("included_in_add_ons", [])),
        )
        if not capability.capability_id:
            continue
        index[capability.capability_id] = capability
    return index


@lru_cache(maxsize=1)
def feature_capability_mapping() -> dict[str, str]:
    payload = _registry_payload()
    raw_mapping = payload.get("feature_to_capability", {})
    if not isinstance(raw_mapping, dict):
        raise ValueError("feature_to_capability must be an object")

    mapping: dict[str, str] = {}
    for feature_id, capability_id in raw_mapping.items():
        if not isinstance(feature_id, str) or not isinstance(capability_id, str):
            continue
        normalized_feature_id = feature_id.strip()
        normalized_capability_id = capability_id.strip()
        if normalized_feature_id and normalized_capability_id:
            mapping[normalized_feature_id] = normalized_capability_id
    return mapping

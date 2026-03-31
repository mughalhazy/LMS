from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[2]))

from shared.models.capability import Capability

_REGISTRY_PATH = Path(__file__).with_name("capabilities.json")


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

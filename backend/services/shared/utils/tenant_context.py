from __future__ import annotations

import json
import os
from typing import Any

from backend.services.shared.models.tenant import TenantContract

_TENANT_CONTEXT_ENV = "TENANT_CAPABILITY_CONTEXT_JSON"
_DEFAULT_PLAN_ENV = "DEFAULT_TENANT_PLAN_TYPE"


def _load_tenant_context() -> dict[str, dict[str, Any]]:
    raw_context = os.getenv(_TENANT_CONTEXT_ENV, "")
    if not raw_context.strip():
        return {}

    try:
        parsed = json.loads(raw_context)
    except json.JSONDecodeError:
        return {}

    if not isinstance(parsed, dict):
        return {}

    normalized: dict[str, dict[str, Any]] = {}
    for tenant_id, payload in parsed.items():
        if isinstance(tenant_id, str) and isinstance(payload, dict):
            normalized[tenant_id] = payload
    return normalized


def tenant_contract_from_inputs(
    *,
    tenant_id: str,
    tenant_name: str | None = None,
    country_code: str | None = None,
    segment_context: dict[str, Any] | None = None,
    plan_type: str | None = None,
    addon_flags: list[str] | None = None,
) -> TenantContract:
    context = _load_tenant_context().get(tenant_id, {})

    resolved_country = str(country_code or context.get("country_code") or "ZZ")
    resolved_segment_context = segment_context or context.get("segment_context") or {
        "type": "default",
        "attributes": {},
    }
    if not isinstance(resolved_segment_context, dict):
        resolved_segment_context = {"type": "default", "attributes": {}}
    resolved_plan = str(plan_type or context.get("plan_type") or os.getenv(_DEFAULT_PLAN_ENV, "free"))
    resolved_flags = addon_flags if addon_flags is not None else context.get("addon_flags", [])

    return TenantContract(
        tenant_id=tenant_id,
        name=tenant_name or tenant_id,
        country_code=resolved_country,
        plan_type=resolved_plan,
        segment_context={
            "type": str(resolved_segment_context.get("type", "default")),
            "attributes": dict(resolved_segment_context.get("attributes", {})),
        },
        addon_flags=resolved_flags if isinstance(resolved_flags, list) else [],
    ).normalized()

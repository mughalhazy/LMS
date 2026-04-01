from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]


def _load_module(module_name: str, relative_path: str):
    module_path = _ROOT / relative_path
    sys.path.append(str(module_path.parent))
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_OwnerEconomicsModule = _load_module("owner_economics_module_for_analytics", "services/commerce/owner_economics.py")
OwnerEconomicsEngine = _OwnerEconomicsModule.OwnerEconomicsEngine


class AnalyticsService:
    """Analytics facade that delegates owner economics to canonical commerce engine."""

    def __init__(self) -> None:
        self._owner_economics_engine = OwnerEconomicsEngine()

    def compute_owner_economics(
        self,
        *,
        tenant_id: str,
        reporting_period: str,
        ledger_entries: tuple[Any, ...],
        commerce_invoices: tuple[Any, ...],
        academy_batches: tuple[Any, ...],
        academy_branches: tuple[Any, ...],
        metadata: dict[str, Any] | None = None,
    ) -> Any:
        return self._owner_economics_engine.compute_profitability_snapshot(
            tenant_id=tenant_id,
            reporting_period=reporting_period,
            ledger_entries=ledger_entries,
            commerce_invoices=commerce_invoices,
            batches=academy_batches,
            branches=academy_branches,
            metadata=metadata,
        )

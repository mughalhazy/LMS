from __future__ import annotations

import secrets
from typing import Dict, List, Optional, Tuple

from .models import RevenueCapabilityDaily, RevenueFact, RevenueTenantDaily


class InMemoryRevenueStore:
    def __init__(self) -> None:
        self._facts: Dict[str, RevenueFact] = {}
        self._tenant_daily: Dict[Tuple[str, str, str], RevenueTenantDaily] = {}
        self._cap_daily: Dict[Tuple[str, str, str], RevenueCapabilityDaily] = {}

    def save_fact(self, fact: RevenueFact) -> None:
        self._facts[fact.fact_id] = fact

    def get_fact(self, fact_id: str) -> Optional[RevenueFact]:
        return self._facts.get(fact_id)

    def fact_exists(self, source_event_id: str) -> bool:
        return any(f.source_event_id == source_event_id for f in self._facts.values())

    def add_to_tenant_daily(self, tenant_id: str, date: str, currency: str, net: float, is_refund: bool = False) -> None:
        key = (tenant_id, date, currency)
        row = self._tenant_daily.setdefault(key, RevenueTenantDaily(tenant_id, date, currency))
        if is_refund:
            row.refund_delta += net
        else:
            row.recognized_revenue += net

    def add_to_cap_daily(self, capability_key: str, date: str, currency: str, net: float, is_refund: bool = False) -> None:
        key = (capability_key, date, currency)
        row = self._cap_daily.setdefault(key, RevenueCapabilityDaily(capability_key, date, currency))
        if is_refund:
            row.refund_delta += net
        else:
            row.recognized_revenue += net

    def query_tenant(self, tenant_id: str, from_date: str, to_date: str) -> List[RevenueTenantDaily]:
        return [r for (tid, d, _), r in self._tenant_daily.items()
                if tid == tenant_id and from_date <= d <= to_date]

    def query_capability(self, capability_key: str, from_date: str, to_date: str) -> List[RevenueCapabilityDaily]:
        return [r for (ck, d, _), r in self._cap_daily.items()
                if ck == capability_key and from_date <= d <= to_date]

    def new_id(self) -> str:
        return secrets.token_urlsafe(10)

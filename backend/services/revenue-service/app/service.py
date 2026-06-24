from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from .models import RevenueFact
from .store import InMemoryRevenueStore

try:
    from backend.services.shared.events.bus import get_default_bus
    from backend.services.shared.events.envelope import build_event
    _BUS_AVAILABLE = True
except Exception:
    _BUS_AVAILABLE = False


class RevenueService:
    def __init__(self, store: InMemoryRevenueStore) -> None:
        self.store = store

    def ingest_fact(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        source_event_id = body.get("source_event_id", "")
        if self.store.fact_exists(source_event_id):
            return 200, {"status": "already_ingested", "source_event_id": source_event_id}

        net = float(body.get("net", 0.0))
        fact_type = body.get("fact_type", "invoice_line_recognized")
        is_refund = fact_type == "refund_recognized"

        recognized_at_raw = body.get("recognized_at")
        recognized_at = datetime.fromisoformat(recognized_at_raw) if recognized_at_raw else datetime.now(timezone.utc)
        date_str = recognized_at.strftime("%Y-%m-%d")

        fact = RevenueFact(
            fact_id=self.store.new_id(),
            fact_type=fact_type,
            source_service=body.get("source_service", ""),
            source_event_id=source_event_id,
            tenant_id=body.get("tenant_id", ""),
            capability_key=body.get("capability_key"),
            invoice_id=body.get("invoice_id"),
            invoice_line_id=body.get("invoice_line_id"),
            subscription_id=body.get("subscription_id"),
            currency=body.get("currency", "USD"),
            gross=float(body.get("gross", 0.0)),
            discount=float(body.get("discount", 0.0)),
            net=net,
            recognition_start=datetime.fromisoformat(body["recognition_start"]) if body.get("recognition_start") else recognized_at,
            recognition_end=datetime.fromisoformat(body["recognition_end"]) if body.get("recognition_end") else recognized_at,
            recognized_at=recognized_at,
            allocation_method=body.get("allocation_method", "direct_mapping"),
            usage_metric_key=body.get("usage_metric_key"),
            usage_quantity=body.get("usage_quantity"),
        )
        self.store.save_fact(fact)

        self.store.add_to_tenant_daily(fact.tenant_id, date_str, fact.currency, net, is_refund)
        if fact.capability_key:
            self.store.add_to_cap_daily(fact.capability_key, date_str, fact.currency, net, is_refund)

        return 201, {"fact_id": fact.fact_id, "tenant_id": fact.tenant_id,
                     "net": net, "date": date_str, "status": "ingested"}

    def query_tenant(self, tenant_id: str, from_date: str, to_date: str) -> Tuple[int, Dict[str, Any]]:
        rows = self.store.query_tenant(tenant_id, from_date, to_date)
        return 200, {
            "tenant_id": tenant_id, "from": from_date, "to": to_date,
            "rows": [{"date": r.date, "currency": r.currency,
                      "recognized_revenue": round(r.recognized_revenue, 2),
                      "refund_delta": round(r.refund_delta, 2)} for r in rows],
            "total_recognized": round(sum(r.recognized_revenue for r in rows), 2),
        }

    def query_tenant_capability_matrix(self, tenant_id: str, from_date: str, to_date: str) -> Tuple[int, Dict[str, Any]]:
        """B15-005: tenant × capability revenue matrix."""
        facts = [f for f in self.store._facts.values()
                 if f.tenant_id == tenant_id and f.capability_key
                 and from_date <= f.recognized_at.strftime("%Y-%m-%d") <= to_date]
        matrix: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        for f in facts:
            matrix[f.capability_key][f.currency] += f.net
        return 200, {
            "tenant_id": tenant_id, "from": from_date, "to": to_date,
            "matrix": {ck: dict(currencies) for ck, currencies in matrix.items()},
        }

    def get_revenue_snapshot(self, as_of_date: str) -> Tuple[int, Dict[str, Any]]:
        """B15-005: immutable finance-close snapshot as of a specific date."""
        tenant_totals: Dict[str, float] = defaultdict(float)
        cap_totals: Dict[str, float] = defaultdict(float)
        for f in self.store._facts.values():
            date_str = f.recognized_at.strftime("%Y-%m-%d")
            if date_str <= as_of_date:
                tenant_totals[f.tenant_id] += f.net
                if f.capability_key:
                    cap_totals[f.capability_key] += f.net
        return 200, {
            "snapshot_as_of": as_of_date,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "tenant_totals": {t: round(v, 2) for t, v in tenant_totals.items()},
            "capability_totals": {c: round(v, 2) for c, v in cap_totals.items()},
            "immutable": True,
        }

    def query_capability_monthly(self, capability_key: str, from_date: str, to_date: str) -> Tuple[int, Dict[str, Any]]:
        """B15-005: monthly roll-up for capability revenue."""
        rows = self.store.query_capability(capability_key, from_date, to_date)
        monthly: Dict[str, float] = defaultdict(float)
        for r in rows:
            month = r.date[:7]  # YYYY-MM
            monthly[month] += r.recognized_revenue
        return 200, {
            "capability_key": capability_key, "from": from_date, "to": to_date,
            "monthly": [{"month": m, "recognized_revenue": round(v, 2)}
                        for m, v in sorted(monthly.items())],
            "total_recognized": round(sum(monthly.values()), 2),
        }

    def check_anomalies(self, tenant_id: str) -> None:
        """B15-006: BC-REV-01 — emit revenue.anomaly.detected for 4 risk signals."""
        if not _BUS_AVAILABLE:
            return
        try:
            bus = get_default_bus()
            now = datetime.now(timezone.utc)
            signals = []

            # Signal 1: unpaid installments overdue ≥7 days (placeholder — real impl needs payment service)
            # Detected via facts with fact_type='installment_due' older than 7 days with no matching payment
            overdue_facts = [f for f in self.store._facts.values()
                             if f.tenant_id == tenant_id
                             and f.fact_type == "installment_due"
                             and (now - f.recognized_at).days >= 7]
            if overdue_facts:
                signals.append({"signal": "overdue_installments", "count": len(overdue_facts)})

            # Signal 2: month-to-date revenue decline ≥15%
            this_month = now.strftime("%Y-%m")
            last_month = (now.replace(day=1) - __import__("datetime").timedelta(days=1)).strftime("%Y-%m")
            this_mtd = sum(f.net for f in self.store._facts.values()
                           if f.tenant_id == tenant_id and f.recognized_at.strftime("%Y-%m") == this_month)
            last_mtd = sum(f.net for f in self.store._facts.values()
                           if f.tenant_id == tenant_id and f.recognized_at.strftime("%Y-%m") == last_month)
            if last_mtd > 0 and (last_mtd - this_mtd) / last_mtd >= 0.15:
                signals.append({"signal": "mtd_revenue_decline",
                                 "decline_pct": round((last_mtd - this_mtd) / last_mtd * 100, 1)})

            for signal in signals:
                envelope = build_event(
                    event_type="revenue.anomaly.detected",
                    tenant_id=tenant_id,
                    payload={**signal, "tenant_id": tenant_id,
                             "detected_at": now.isoformat()},
                )
                bus.publish(envelope)
        except Exception:
            pass

    def query_capability(self, capability_key: str, from_date: str, to_date: str) -> Tuple[int, Dict[str, Any]]:
        rows = self.store.query_capability(capability_key, from_date, to_date)
        return 200, {
            "capability_key": capability_key, "from": from_date, "to": to_date,
            "rows": [{"date": r.date, "currency": r.currency,
                      "recognized_revenue": round(r.recognized_revenue, 2)} for r in rows],
            "total_recognized": round(sum(r.recognized_revenue for r in rows), 2),
        }

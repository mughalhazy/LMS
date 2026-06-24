from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .models import EarningsEntry, PayoutRecord
from .store import InMemoryEconomicsStore

DEFAULT_COMMISSION_RATE = 0.20
DEFAULT_PROCESSING_FEE_RATE = 0.02
DEFAULT_TAX_WITHHOLDING_RATE = 0.05
DEFAULT_PAYOUT_SCHEDULE = "monthly"


def _fetch_payout_config(tenant_id: str) -> Dict[str, Any]:
    """B15-009: fetch payout config from config-service; fall back to defaults."""
    try:
        from backend.services.config_service.app.service import ConfigService
        svc = ConfigService.__new__(ConfigService)
        schedule = svc.resolve_key(f"payout.schedule.{tenant_id}") or DEFAULT_PAYOUT_SCHEDULE
        processing_fee = float(svc.resolve_key("payout.processing_fee_rate") or DEFAULT_PROCESSING_FEE_RATE)
        tax_rate = float(svc.resolve_key("payout.tax_withholding_rate") or DEFAULT_TAX_WITHHOLDING_RATE)
        return {"schedule": schedule, "processing_fee_rate": processing_fee, "tax_withholding_rate": tax_rate}
    except Exception:
        return {"schedule": DEFAULT_PAYOUT_SCHEDULE,
                "processing_fee_rate": DEFAULT_PROCESSING_FEE_RATE,
                "tax_withholding_rate": DEFAULT_TAX_WITHHOLDING_RATE}


class TeacherEconomicsView:
    """B15-007: teacher/tutor earnings view distinct from owner economics.
    Driven by session delivery and tutor rating events."""

    def __init__(self) -> None:
        self._entries: List[Dict[str, Any]] = []
        self._ledgers: Dict[str, Dict[str, Any]] = {}  # tutor_id:period → ledger

    def record_session_earning(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        tutor_id = body.get("tutor_id", "")
        tenant_id = body.get("tenant_id", "")
        session_id = body.get("session_id", "")
        period = body.get("period", datetime.now(timezone.utc).strftime("%Y-%m"))
        base_amount = float(body.get("base_amount", 0.0))
        rating_score = body.get("rating_score")
        rating_multiplier = 1.0 + (max(0.0, float(rating_score) - 3.0) * 0.1) if rating_score else 1.0
        gross = round(base_amount * rating_multiplier, 2)
        platform_fee = round(gross * 0.15, 2)
        net = round(gross - platform_fee, 2)

        entry = {
            "entry_id": f"te-{secrets.token_urlsafe(8)}",
            "tutor_id": tutor_id, "tenant_id": tenant_id, "session_id": session_id,
            "period": period, "base_amount": base_amount, "rating_multiplier": rating_multiplier,
            "gross_amount": gross, "platform_fee": platform_fee, "net_amount": net,
            "rating_score": rating_score, "currency": body.get("currency", "USD"),
        }
        self._entries.append(entry)

        key = f"{tutor_id}:{period}"
        ledger = self._ledgers.setdefault(key, {
            "tutor_id": tutor_id, "tenant_id": tenant_id, "period": period,
            "currency": body.get("currency", "USD"), "total_sessions": 0,
            "total_gross": 0.0, "total_platform_fee": 0.0, "total_net": 0.0,
            "rating_sum": 0.0, "rating_count": 0,
        })
        ledger["total_sessions"] += 1
        ledger["total_gross"] = round(ledger["total_gross"] + gross, 2)
        ledger["total_platform_fee"] = round(ledger["total_platform_fee"] + platform_fee, 2)
        ledger["total_net"] = round(ledger["total_net"] + net, 2)
        if rating_score:
            ledger["rating_sum"] += float(rating_score)
            ledger["rating_count"] += 1
            ledger["average_rating"] = round(ledger["rating_sum"] / ledger["rating_count"], 2)

        return 201, entry

    def get_teacher_ledger(self, tutor_id: str, tenant_id: str, period: str) -> Tuple[int, Dict[str, Any]]:
        key = f"{tutor_id}:{period}"
        ledger = self._ledgers.get(key)
        if not ledger or ledger["tenant_id"] != tenant_id:
            return 404, {"error": "teacher_ledger_not_found"}
        return 200, ledger

    def list_teacher_entries(self, tutor_id: str, tenant_id: str) -> Tuple[int, Dict[str, Any]]:
        entries = [e for e in self._entries if e["tutor_id"] == tutor_id and e["tenant_id"] == tenant_id]
        return 200, {"tutor_id": tutor_id, "entries": entries, "count": len(entries)}


class OwnerEconomicsService:
    def __init__(self, store: InMemoryEconomicsStore) -> None:
        self.store = store
        self.teacher_view = TeacherEconomicsView()

    def record_earning(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        source_event_id = body.get("source_event_id", "")
        if self.store.event_ingested(source_event_id):
            return 200, {"status": "already_recorded", "source_event_id": source_event_id}

        gross = float(body.get("gross_amount", 0.0))
        commission_rate = float(body.get("commission_rate", DEFAULT_COMMISSION_RATE))
        commission = round(gross * commission_rate, 2)
        net = round(gross - commission, 2)
        period = body.get("period", datetime.now(timezone.utc).strftime("%Y-%m"))

        entry = EarningsEntry(
            entry_id=self.store.new_id("earn"),
            participant_id=body.get("participant_id", ""),
            tenant_id=body.get("tenant_id", ""),
            event_type=body.get("event_type", "enrollment_revenue_share"),
            source_event_id=source_event_id,
            period=period,
            gross_amount=gross,
            platform_commission=commission,
            net_amount=net,
            currency=body.get("currency", "USD"),
            metadata=body.get("metadata", {}),
        )
        self.store.save_entry(entry)
        self.store.update_ledger(
            entry.participant_id, entry.tenant_id, period,
            entry.currency, gross, commission, net
        )
        return 201, {
            "entry_id": entry.entry_id, "participant_id": entry.participant_id,
            "gross_amount": gross, "platform_commission": commission, "net_amount": net,
            "period": period, "currency": entry.currency,
        }

    def get_ledger(self, participant_id: str, tenant_id: str, period: str) -> Tuple[int, Dict[str, Any]]:
        ledger = self.store.get_ledger(participant_id, tenant_id, period)
        if not ledger:
            return 404, {"error": "ledger_not_found"}
        return 200, {
            "participant_id": ledger.participant_id, "tenant_id": ledger.tenant_id,
            "period": ledger.period, "currency": ledger.currency,
            "total_gross": round(ledger.total_gross, 2),
            "total_commission": round(ledger.total_commission, 2),
            "total_net": round(ledger.total_net, 2),
            "entry_count": ledger.entry_count,
        }

    def list_ledgers(self, participant_id: str, tenant_id: str) -> Tuple[int, Dict[str, Any]]:
        ledgers = self.store.list_ledgers(participant_id, tenant_id)
        return 200, {
            "participant_id": participant_id,
            "ledgers": [
                {"period": l.period, "currency": l.currency,
                 "total_net": round(l.total_net, 2), "entry_count": l.entry_count}
                for l in sorted(ledgers, key=lambda x: x.period, reverse=True)
            ],
        }

    def calculate_payout(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        participant_id = body.get("participant_id", "")
        tenant_id = body.get("tenant_id", "")
        period = body.get("period", "")

        ledger = self.store.get_ledger(participant_id, tenant_id, period)
        if not ledger:
            return 404, {"error": "no_earnings_for_period"}

        payout_cfg = _fetch_payout_config(tenant_id)
        gross = ledger.total_net
        processing_fee = round(gross * payout_cfg["processing_fee_rate"], 2)
        tax_withholding = round(gross * payout_cfg["tax_withholding_rate"], 2)
        net_payout = round(gross - processing_fee - tax_withholding, 2)

        payout = PayoutRecord(
            payout_id=self.store.new_id("pay"),
            participant_id=participant_id,
            tenant_id=tenant_id,
            period=period,
            currency=ledger.currency,
            gross_earnings=round(ledger.total_gross, 2),
            platform_commission=round(ledger.total_commission, 2),
            processing_fee=processing_fee,
            tax_withholding=tax_withholding,
            net_payout=net_payout,
            deduction_breakdown={
                "platform_commission": round(ledger.total_commission, 2),
                "processing_fee": processing_fee,
                "tax_withholding": tax_withholding,
            },
        )
        self.store.save_payout(payout)
        return 200, {
            "payout_id": payout.payout_id, "participant_id": participant_id,
            "period": period, "currency": payout.currency,
            "gross_earnings": payout.gross_earnings,
            "deduction_breakdown": payout.deduction_breakdown,
            "net_payout": payout.net_payout, "status": payout.status,
        }

    def list_payouts(self, participant_id: str, tenant_id: str) -> Tuple[int, Dict[str, Any]]:
        payouts = self.store.list_payouts(participant_id, tenant_id)
        return 200, {
            "participant_id": participant_id,
            "payouts": [{"payout_id": p.payout_id, "period": p.period,
                          "net_payout": p.net_payout, "status": p.status} for p in payouts],
        }

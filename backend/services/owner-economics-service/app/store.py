from __future__ import annotations

import secrets
from typing import Dict, List, Optional, Tuple

from .models import EarningsEntry, ParticipantLedger, PayoutRecord


class InMemoryEconomicsStore:
    def __init__(self) -> None:
        self._entries: Dict[str, EarningsEntry] = {}
        self._ledgers: Dict[Tuple[str, str, str], ParticipantLedger] = {}
        self._payouts: Dict[str, PayoutRecord] = {}

    def event_ingested(self, source_event_id: str) -> bool:
        return any(e.source_event_id == source_event_id for e in self._entries.values())

    def save_entry(self, entry: EarningsEntry) -> None:
        self._entries[entry.entry_id] = entry

    def update_ledger(self, participant_id: str, tenant_id: str, period: str,
                      currency: str, gross: float, commission: float, net: float) -> None:
        key = (participant_id, tenant_id, period)
        ledger = self._ledgers.setdefault(
            key, ParticipantLedger(participant_id, tenant_id, period, currency)
        )
        ledger.total_gross += gross
        ledger.total_commission += commission
        ledger.total_net += net
        ledger.entry_count += 1

    def get_ledger(self, participant_id: str, tenant_id: str, period: str) -> Optional[ParticipantLedger]:
        return self._ledgers.get((participant_id, tenant_id, period))

    def list_ledgers(self, participant_id: str, tenant_id: str) -> List[ParticipantLedger]:
        return [l for (pid, tid, _), l in self._ledgers.items()
                if pid == participant_id and tid == tenant_id]

    def save_payout(self, payout: PayoutRecord) -> None:
        self._payouts[payout.payout_id] = payout

    def list_payouts(self, participant_id: str, tenant_id: str) -> List[PayoutRecord]:
        return [p for p in self._payouts.values()
                if p.participant_id == participant_id and p.tenant_id == tenant_id]

    def new_id(self, prefix: str = "") -> str:
        return f"{prefix}-{secrets.token_urlsafe(8)}" if prefix else secrets.token_urlsafe(10)

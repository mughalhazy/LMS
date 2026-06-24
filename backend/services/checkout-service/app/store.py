from __future__ import annotations

import secrets
from typing import Dict, List, Optional

from .models import CheckoutPaymentAttempt, CheckoutSession, Order


class InMemoryCheckoutStore:
    def __init__(self) -> None:
        self._sessions: Dict[str, CheckoutSession] = {}
        self._orders: Dict[str, Order] = {}
        self._attempts: Dict[str, List[CheckoutPaymentAttempt]] = {}

    def save_session(self, session: CheckoutSession) -> None:
        self._sessions[session.session_id] = session

    def get_session(self, session_id: str) -> Optional[CheckoutSession]:
        return self._sessions.get(session_id)

    def get_order_by_session(self, session_id: str) -> Optional[Order]:
        return next((o for o in self._orders.values() if o.source_session_id == session_id), None)

    def save_order(self, order: Order) -> None:
        self._orders[order.order_id] = order

    def get_order(self, order_id: str) -> Optional[Order]:
        return self._orders.get(order_id)

    def save_attempt(self, attempt: CheckoutPaymentAttempt) -> None:
        self._attempts.setdefault(attempt.order_id, []).append(attempt)

    def list_attempts(self, order_id: str) -> List[CheckoutPaymentAttempt]:
        return self._attempts.get(order_id, [])

    def new_id(self, prefix: str = "") -> str:
        return f"{prefix}-{secrets.token_urlsafe(8)}" if prefix else secrets.token_urlsafe(10)

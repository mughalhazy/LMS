from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Tuple

from .models import CheckoutPaymentAttempt, CheckoutSession, Order, OrderLine
from .store import InMemoryCheckoutStore


class CheckoutService:
    def __init__(self, store: InMemoryCheckoutStore, session_ttl_minutes: int = 30) -> None:
        self.store = store
        self.session_ttl_minutes = session_ttl_minutes

    def create_session(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        session = CheckoutSession(
            session_id=self.store.new_id("sess"),
            tenant_id=body.get("tenant_id", ""),
            customer_id=body.get("customer_id", ""),
            status="open",
            line_items=[],
            currency=body.get("currency", "USD"),
            catalog_snapshot_ref=body.get("catalog_snapshot_ref"),
            expires_at=now + timedelta(minutes=self.session_ttl_minutes),
            created_at=now,
            updated_at=now,
        )
        self.store.save_session(session)
        return 201, self._serialize_session(session)

    def update_items(self, session_id: str, tenant_id: str, items: List[Dict[str, Any]]) -> Tuple[int, Dict[str, Any]]:
        session = self._get_open_session(session_id, tenant_id)
        if session is None:
            return 404, {"error": "session_not_found_or_not_open"}

        from .models import LineItem
        session.line_items = [
            LineItem(sku=i["sku"], quantity=i.get("quantity", 1),
                     display_price_ref=i.get("display_price_ref", ""),
                     offer_id=i.get("offer_id"))
            for i in items
        ]
        session.updated_at = datetime.now(timezone.utc)
        self.store.save_session(session)
        return 200, self._serialize_session(session)

    def submit_session(self, session_id: str, tenant_id: str, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        # Idempotent submit — check for existing order before any status gating
        existing_order = self.store.get_order_by_session(session_id)
        if existing_order and existing_order.tenant_id == tenant_id:
            return 200, {"order_id": existing_order.order_id, "status": existing_order.status, "idempotent_replay": True}

        session = self._get_open_session(session_id, tenant_id)
        if session is None:
            return 404, {"error": "session_not_found_or_not_open"}

        now = datetime.now(timezone.utc)
        if now > session.expires_at.replace(tzinfo=timezone.utc) if session.expires_at.tzinfo is None else now > session.expires_at:
            session.status = "expired"
            self.store.save_session(session)
            return 410, {"error": "session_expired"}

        if not session.line_items:
            session.status = "failed_validation"
            self.store.save_session(session)
            return 422, {"error": "session_has_no_items"}

        idempotency_key = body.get("idempotency_key", "")

        session.status = "submitted"
        session.idempotency_key_last_submit = idempotency_key
        session.updated_at = now
        self.store.save_session(session)

        order = Order(
            order_id=self.store.new_id("order"),
            tenant_id=tenant_id,
            customer_id=session.customer_id,
            source_session_id=session_id,
            status="created",
            currency=session.currency,
            lines=[OrderLine(sku=li.sku, quantity=li.quantity, display_price_ref=li.display_price_ref)
                   for li in session.line_items],
            created_at=now,
            updated_at=now,
        )
        self.store.save_order(order)
        return 202, {"order_id": order.order_id, "status": order.status}

    def initiate_payment(self, order_id: str, tenant_id: str, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        order = self.store.get_order(order_id)
        if not order or order.tenant_id != tenant_id:
            return 404, {"error": "order_not_found"}
        attempts = self.store.list_attempts(order_id)
        request_id = body.get("request_id", self.store.new_id("req"))

        # Idempotent: check before status gate
        for prev in attempts:
            if prev.request_id == request_id and prev.status == "accepted":
                return 200, {"attempt_id": prev.attempt_id, "status": "accepted", "idempotent_replay": True}

        if order.status not in ("created", "pending_payment"):
            return 409, {"error": "order_not_in_payable_state", "status": order.status}

        attempt = CheckoutPaymentAttempt(
            attempt_id=self.store.new_id("att"),
            order_id=order_id,
            request_id=request_id,
            attempt_no=len(attempts) + 1,
            status="accepted",
        )
        self.store.save_attempt(attempt)
        order.status = "payment_initiated"
        order.updated_at = datetime.now(timezone.utc)
        self.store.save_order(order)
        return 200, {"attempt_id": attempt.attempt_id, "order_id": order_id, "status": "payment_initiated"}

    def get_session(self, session_id: str, tenant_id: str) -> Tuple[int, Dict[str, Any]]:
        session = self.store.get_session(session_id)
        if not session or session.tenant_id != tenant_id:
            return 404, {"error": "session_not_found"}
        return 200, self._serialize_session(session)

    def get_order(self, order_id: str, tenant_id: str) -> Tuple[int, Dict[str, Any]]:
        order = self.store.get_order(order_id)
        if not order or order.tenant_id != tenant_id:
            return 404, {"error": "order_not_found"}
        return 200, self._serialize_order(order)

    def _get_open_session(self, session_id: str, tenant_id: str):
        session = self.store.get_session(session_id)
        if not session or session.tenant_id != tenant_id or session.status != "open":
            return None
        return session

    def _serialize_session(self, s: CheckoutSession) -> Dict[str, Any]:
        return {
            "session_id": s.session_id, "tenant_id": s.tenant_id, "customer_id": s.customer_id,
            "status": s.status, "currency": s.currency, "catalog_snapshot_ref": s.catalog_snapshot_ref,
            "line_items": [{"sku": li.sku, "quantity": li.quantity} for li in s.line_items],
            "expires_at": s.expires_at.isoformat(),
        }

    def _serialize_order(self, o: Order) -> Dict[str, Any]:
        return {
            "order_id": o.order_id, "tenant_id": o.tenant_id, "customer_id": o.customer_id,
            "source_session_id": o.source_session_id, "status": o.status, "currency": o.currency,
            "lines": [{"sku": l.sku, "quantity": l.quantity} for l in o.lines],
            "created_at": o.created_at.isoformat(),
        }

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class LineItem:
    sku: str
    quantity: int
    display_price_ref: str
    offer_id: Optional[str] = None


@dataclass
class CheckoutSession:
    session_id: str
    tenant_id: str
    customer_id: str
    status: str  # open | submitted | expired | failed_validation
    line_items: List[LineItem]
    currency: str
    catalog_snapshot_ref: Optional[str]
    expires_at: datetime
    idempotency_key_last_submit: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class OrderLine:
    sku: str
    quantity: int
    display_price_ref: str


@dataclass
class Order:
    order_id: str
    tenant_id: str
    customer_id: str
    source_session_id: str
    status: str  # created | pending_payment | payment_initiated | payment_failed | completed | cancelled
    currency: str
    lines: List[OrderLine]
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CheckoutPaymentAttempt:
    attempt_id: str
    order_id: str
    request_id: str  # idempotency key
    attempt_no: int
    status: str  # requested | accepted | retryable_failure | terminal_failure
    error_code: Optional[str] = None
    retryable: Optional[bool] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

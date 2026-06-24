from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class BillingAccount:
    billing_account_id: str
    tenant_id: str
    customer_id: str
    billing_timezone: str
    currency: str
    status: str = "active"
    invoice_delivery_preferences: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class InvoiceLine:
    invoice_line_id: str
    invoice_id: str
    line_type: str  # subscription_fee | usage | one_time_item | tax | discount | adjustment
    source_ref: Optional[str]
    quantity: float
    unit_price: float
    amount: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Invoice:
    invoice_id: str
    invoice_number: str
    billing_account_id: str
    tenant_id: str
    invoice_type: str  # recurring | one_time | adjustment | credit_note
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    currency: str
    state: str  # draft | validated | issued | paid | overdue | voided
    lines: List[InvoiceLine] = field(default_factory=list)
    subtotal: float = 0.0
    tax_total: float = 0.0
    discount_total: float = 0.0
    grand_total: float = 0.0
    due_at: Optional[datetime] = None
    issued_at: Optional[datetime] = None
    voided_at: Optional[datetime] = None
    subscription_id: Optional[str] = None
    checkout_order_id: Optional[str] = None
    version: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class BillingRecord:
    record_id: str
    invoice_id: str
    tenant_id: str
    record_type: str
    recorded_at: datetime
    actor_type: str
    actor_id: str
    correlation_id: str
    payload_hash: str = ""


@dataclass
class AuditTrailEntry:
    audit_id: str
    entity_type: str
    entity_id: str
    action: str
    before: Dict[str, Any]
    after: Dict[str, Any]
    performed_by: str
    performed_at: datetime
    reason: str = ""
    request_id: str = ""

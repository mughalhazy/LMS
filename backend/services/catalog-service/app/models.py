from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class PricingModelRef:
    pricing_model_id: str
    pricing_type: str  # ONE_TIME | RECURRING | USAGE_BASED | TIERED | SEAT_BASED | HYBRID
    price_book_id: str
    billing_period_hint: Optional[str] = None


@dataclass
class Offer:
    offer_id: str
    product_id: str
    offer_code: str
    pricing_model_refs: List[PricingModelRef]
    default_pricing_model_ref: str
    discount_policy_refs: List[str] = field(default_factory=list)
    coupon_policy_ref: Optional[str] = None
    region_allowlist: List[str] = field(default_factory=list)
    currency_allowlist: List[str] = field(default_factory=list)
    min_seats: Optional[int] = None
    max_seats: Optional[int] = None
    new_customer_only: bool = False
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None


@dataclass
class Product:
    product_id: str
    tenant_id: str
    product_type: str  # COURSE | BUNDLE | SUBSCRIPTION
    sku: str
    status: str  # DRAFT | PUBLISHED | RETIRED
    display_name: str
    description: str
    version: int
    offer_ids: List[str] = field(default_factory=list)
    sellable_from: Optional[datetime] = None
    sellable_until: Optional[datetime] = None
    channel_targets: List[str] = field(default_factory=list)
    segment_targets: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    # type-specific details stored as dict
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TenantCatalogConfig:
    tenant_id: str
    default_currency: str
    supported_currencies: List[str]
    coupon_stackability_mode: str = "NONE"  # NONE | LIMITED | CONFIGURED
    publish_approval_required: bool = False
    segment_policy: Dict[str, Any] = field(default_factory=dict)
    channel_policy: Dict[str, Any] = field(default_factory=dict)
    regional_compliance_tags: List[str] = field(default_factory=list)


@dataclass
class CatalogSnapshot:
    snapshot_id: str
    tenant_id: str
    product_ids: List[str]
    offer_ids: List[str]
    created_at: datetime

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum


class ProductType(str, Enum):
    COURSE = "course"
    BUNDLE = "bundle"
    SUBSCRIPTION = "subscription"


class BundlePricingRule(str, Enum):
    FLAT = "flat"
    DISCOUNTED = "discounted"


@dataclass(frozen=True)
class Product:
    product_id: str
    tenant_id: str
    sku: str
    product_type: ProductType
    title: str
    capability_id: str
    price: Decimal
    currency: str
    published: bool = True
    metadata: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def normalized(self) -> "Product":
        normalized = Product(
            product_id=self.product_id.strip(),
            tenant_id=self.tenant_id.strip(),
            sku=self.sku.strip().upper(),
            product_type=ProductType(self.product_type),
            title=self.title.strip(),
            capability_id=self.capability_id.strip(),
            price=Decimal(self.price),
            currency=self.currency.strip().upper(),
            published=bool(self.published),
            metadata={str(k): str(v) for k, v in self.metadata.items()},
            created_at=self.created_at,
        )
        if not normalized.capability_id:
            raise ValueError("product capability_id is required")
        return normalized


@dataclass(frozen=True)
class Bundle:
    bundle_id: str
    tenant_id: str
    product_ids: tuple[str, ...]
    pricing_rule: BundlePricingRule
    bundle_price: Decimal | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def normalized(self) -> "Bundle":
        normalized = Bundle(
            bundle_id=self.bundle_id.strip(),
            tenant_id=self.tenant_id.strip(),
            product_ids=tuple(p.strip() for p in self.product_ids if p.strip()),
            pricing_rule=BundlePricingRule(self.pricing_rule),
            bundle_price=Decimal(self.bundle_price) if self.bundle_price is not None else None,
            created_at=self.created_at,
        )
        if not normalized.product_ids:
            raise ValueError("bundle must include at least one product")
        return normalized


@dataclass(frozen=True)
class CatalogItem:
    product: Product
    bundle_products: tuple[Product, ...] = ()
    effective_price: Decimal | None = None

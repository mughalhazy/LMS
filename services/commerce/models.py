from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum


class ProductType(str, Enum):
    COURSE = "course"
    BUNDLE = "bundle"
    SUBSCRIPTION = "subscription"


class BundlePricingRule(str, Enum):
    FLAT = "flat"
    SUM_OF_ITEMS = "sum_of_items"


class BillingCycle(str, Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


@dataclass(frozen=True)
class Product:
    product_id: str
    tenant_id: str
    type: ProductType
    title: str
    description: str
    price: Decimal
    currency: str
    capability_ids: list[str]
    metadata: dict[str, str] = field(default_factory=dict)
    sku: str | None = None
    published: bool = True

    @property
    def capability_id(self) -> str:
        return self.primary_capability_id

    @property
    def product_type(self) -> ProductType:
        return self.type

    @property
    def primary_capability_id(self) -> str:
        return self.capability_ids[0]

    def normalized(self) -> "Product":
        capability_ids = sorted(
            {
                capability_id.strip()
                for capability_id in self.capability_ids
                if capability_id and capability_id.strip()
            }
        )
        if not capability_ids:
            raise ValueError("product capability_ids are required")
        return Product(
            product_id=self.product_id.strip(),
            tenant_id=self.tenant_id.strip(),
            type=ProductType(self.type),
            title=self.title.strip(),
            description=self.description.strip(),
            price=Decimal(self.price),
            currency=self.currency.strip().upper(),
            capability_ids=capability_ids,
            metadata={str(k): str(v) for k, v in self.metadata.items()},
            sku=self.sku.strip() if self.sku else None,
            published=bool(self.published),
        )


@dataclass(frozen=True)
class Bundle:
    bundle_id: str
    tenant_id: str
    product_ids: tuple[str, ...]
    pricing_rule: str
    bundle_price: Decimal | None = None

    def normalized(self) -> "Bundle":
        product_ids = tuple(product_id.strip() for product_id in self.product_ids if product_id.strip())
        if not product_ids:
            raise ValueError("bundle product_ids are required")
        rule = BundlePricingRule(self.pricing_rule).value
        price = Decimal(self.bundle_price) if self.bundle_price is not None else None
        return Bundle(
            bundle_id=self.bundle_id.strip(),
            tenant_id=self.tenant_id.strip(),
            product_ids=product_ids,
            pricing_rule=rule,
            bundle_price=price,
        )


@dataclass(frozen=True)
class CatalogItem:
    product_id: str
    tenant_id: str
    type: ProductType
    title: str
    price: Decimal
    currency: str
    bundle_products: tuple[Product, ...] = ()


@dataclass(frozen=True)
class SubscriptionPlan:
    plan_id: str
    price: Decimal
    billing_cycle: BillingCycle | str = BillingCycle.MONTHLY
    capability_ids: tuple[str, ...] = ()

    def normalized(self) -> "SubscriptionPlan":
        return SubscriptionPlan(
            plan_id=self.plan_id.strip(),
            price=Decimal(self.price),
            billing_cycle=BillingCycle(self.billing_cycle),
            capability_ids=tuple(sorted({c.strip() for c in self.capability_ids if c.strip()})),
        )

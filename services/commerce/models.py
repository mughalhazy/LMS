from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum


class ProductType(str, Enum):
    COURSE = "course"
    BUNDLE = "bundle"
    SUBSCRIPTION = "subscription"


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
    published: bool = True

    @property
    def primary_capability_id(self) -> str:
        return self.capability_ids[0]

    def normalized(self) -> "Product":
        normalized = Product(
            product_id=self.product_id.strip(),
            tenant_id=self.tenant_id.strip(),
            type=ProductType(self.type),
            title=self.title.strip(),
            description=self.description.strip(),
            price=Decimal(self.price),
            currency=self.currency.strip().upper(),
            capability_ids=sorted({capability_id.strip() for capability_id in self.capability_ids if capability_id.strip()}),
            metadata={str(k): str(v) for k, v in self.metadata.items()},
            published=bool(self.published),
        )
        if not normalized.capability_ids:
            raise ValueError("product capability_ids are required")
        return normalized

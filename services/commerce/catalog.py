from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum


class ProductType(str, Enum):
    COURSE = "course"
    BUNDLE = "bundle"
    SUBSCRIPTION = "subscription"


@dataclass(frozen=True)
class CatalogProduct:
    product_id: str
    tenant_id: str
    sku: str
    product_type: ProductType
    title: str
    price: Decimal
    currency: str
    published: bool = True
    metadata: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def normalized(self) -> "CatalogProduct":
        return CatalogProduct(
            product_id=self.product_id.strip(),
            tenant_id=self.tenant_id.strip(),
            sku=self.sku.strip().upper(),
            product_type=ProductType(self.product_type),
            title=self.title.strip(),
            price=Decimal(self.price),
            currency=self.currency.strip().upper(),
            published=bool(self.published),
            metadata={str(k): str(v) for k, v in self.metadata.items()},
            created_at=self.created_at,
        )


class CatalogService:
    """Catalog owns sellable entities only; no checkout/billing state."""

    def __init__(self) -> None:
        self._products: dict[str, CatalogProduct] = {}

    def upsert_product(self, product: CatalogProduct) -> None:
        normalized = product.normalized()
        self._products[normalized.product_id] = normalized

    def get_product(self, product_id: str) -> CatalogProduct | None:
        return self._products.get(product_id.strip())

    def list_products(self, *, tenant_id: str, product_type: ProductType | None = None) -> list[CatalogProduct]:
        normalized_tenant = tenant_id.strip()
        products = [
            product
            for product in self._products.values()
            if product.tenant_id == normalized_tenant and product.published
        ]
        if product_type is None:
            return sorted(products, key=lambda p: p.sku)
        return sorted((p for p in products if p.product_type == product_type), key=lambda p: p.sku)

    def resolve_sellable_product(self, *, tenant_id: str, product_id: str) -> CatalogProduct:
        product = self.get_product(product_id)
        if product is None or product.tenant_id != tenant_id.strip() or not product.published:
            raise ValueError(f"product '{product_id}' is not sellable for tenant '{tenant_id}'")
        return product

from __future__ import annotations

from decimal import Decimal

from .models import Product, ProductType


class CatalogService:
    """Catalog owns sellable entities only; no checkout/billing state."""

    def __init__(self) -> None:
        self._products: dict[str, Product] = {}

    def create_product(
        self,
        *,
        product_id: str,
        tenant_id: str,
        type: ProductType,
        title: str,
        description: str,
        price: Decimal,
        currency: str,
        capability_ids: list[str],
        metadata: dict[str, str] | None = None,
    ) -> Product:
        product = Product(
            product_id=product_id,
            tenant_id=tenant_id,
            type=type,
            title=title,
            description=description,
            price=price,
            currency=currency,
            capability_ids=capability_ids,
            metadata=metadata or {},
        ).normalized()
        self._products[product.product_id] = product
        return product

    def update_product(self, product_id: str, **updates: object) -> Product:
        existing = self.get_product(product_id)
        if existing is None:
            raise ValueError(f"product '{product_id}' not found")

        payload = {**existing.__dict__, **updates}
        updated = Product(**payload).normalized()
        self._products[updated.product_id] = updated
        return updated

    def get_product(self, product_id: str) -> Product | None:
        return self._products.get(product_id.strip())

    def list_products(self, *, tenant_id: str, product_type: ProductType | None = None) -> list[Product]:
        normalized_tenant = tenant_id.strip()
        products = [
            product
            for product in self._products.values()
            if product.tenant_id == normalized_tenant and product.published
        ]
        if product_type is None:
            return sorted(products, key=lambda p: p.product_id)
        return sorted((p for p in products if p.type == product_type), key=lambda p: p.product_id)

    def resolve_sellable_product(self, *, tenant_id: str, product_id: str) -> Product:
        product = self.get_product(product_id)
        if product is None or product.tenant_id != tenant_id.strip() or not product.published:
            raise ValueError(f"product '{product_id}' is not sellable for tenant '{tenant_id}'")
        if not product.capability_ids:
            raise ValueError(f"product '{product_id}' is missing required capability mapping")
        if product.type in {ProductType.BUNDLE, ProductType.SUBSCRIPTION}:
            # Placeholder linkage. Extended composition/rules live in specialized modules.
            _ = product.metadata
        return product

from __future__ import annotations

from decimal import Decimal

from .models import Bundle, CatalogItem, Product, ProductType


# Backward-compatible alias while elevating Product as a first-class entity.
CatalogProduct = Product


class CatalogService:
    """Catalog owns sellable entities only; no checkout/billing state."""

    def __init__(self) -> None:
        self._products: dict[str, Product] = {}
        self._bundles: dict[str, Bundle] = {}

    def upsert_product(self, product: Product) -> None:
        normalized = product.normalized()
        self._products[normalized.product_id] = normalized

    def create_bundle(self, bundle: Bundle) -> Bundle:
        normalized = bundle.normalized()
        if normalized.bundle_id not in self._products:
            raise ValueError(f"bundle product '{normalized.bundle_id}' does not exist")

        bundle_product = self._products[normalized.bundle_id]
        if bundle_product.product_type != ProductType.BUNDLE:
            raise ValueError(f"product '{normalized.bundle_id}' is not a bundle product")

        for product_id in normalized.product_ids:
            product = self.get_product(product_id)
            if product is None or product.tenant_id != normalized.tenant_id or not product.published:
                raise ValueError(f"bundle '{normalized.bundle_id}' references unsellable product '{product_id}'")
        self._bundles[normalized.bundle_id] = normalized
        return normalized

    def resolve_bundle_products(self, *, bundle_id: str, tenant_id: str) -> list[Product]:
        normalized_bundle_id = bundle_id.strip()
        bundle = self._bundles.get(normalized_bundle_id)
        if bundle is None:
            raise ValueError(f"bundle '{bundle_id}' is not defined")
        if bundle.tenant_id != tenant_id.strip():
            raise ValueError(f"bundle '{bundle_id}' is not available for tenant '{tenant_id}'")

        products: list[Product] = []
        for product_id in bundle.product_ids:
            product = self.get_product(product_id)
            if product is None or not product.published or product.tenant_id != bundle.tenant_id:
                raise ValueError(f"bundle '{bundle_id}' references unsellable product '{product_id}'")
            products.append(product)
        return products

    def get_product(self, product_id: str) -> Product | None:
        return self._products.get(product_id.strip())

    def get_bundle(self, bundle_id: str) -> Bundle | None:
        return self._bundles.get(bundle_id.strip())

    def bundle_price(self, *, bundle_id: str, tenant_id: str) -> Decimal:
        bundle = self._bundles.get(bundle_id.strip())
        if bundle is None or bundle.tenant_id != tenant_id.strip():
            raise ValueError(f"bundle '{bundle_id}' is not available for tenant '{tenant_id}'")
        bundle_products = self.resolve_bundle_products(bundle_id=bundle_id, tenant_id=tenant_id)
        if bundle.bundle_price is not None:
            return bundle.bundle_price
        return sum((product.price for product in bundle_products), Decimal("0"))

    def list_products(self, *, tenant_id: str, product_type: ProductType | None = None) -> list[CatalogItem]:
        normalized_tenant = tenant_id.strip()
        products = [
            product
            for product in self._products.values()
            if product.tenant_id == normalized_tenant and product.published
        ]
        if product_type is not None:
            products = [p for p in products if p.product_type == product_type]

        items: list[CatalogItem] = []
        for product in sorted(products, key=lambda p: p.sku):
            if product.product_type != ProductType.BUNDLE:
                items.append(CatalogItem(product=product))
                continue

            bundle = self._bundles.get(product.product_id)
            if bundle is None:
                items.append(CatalogItem(product=product, effective_price=product.price))
                continue

            bundle_products = tuple(self.resolve_bundle_products(bundle_id=bundle.bundle_id, tenant_id=normalized_tenant))
            effective_price = bundle.bundle_price if bundle.bundle_price is not None else product.price
            items.append(
                CatalogItem(
                    product=product,
                    bundle_products=bundle_products,
                    effective_price=effective_price,
                )
            )
        return items

    def resolve_sellable_product(self, *, tenant_id: str, product_id: str) -> Product:
        product = self.get_product(product_id)
        if product is None or product.tenant_id != tenant_id.strip() or not product.published:
            raise ValueError(f"product '{product_id}' is not sellable for tenant '{tenant_id}'")
        return product

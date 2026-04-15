from __future__ import annotations

from decimal import Decimal

from .models import Bundle, CatalogItem, Product, ProductType


class CatalogService:
    """Catalog owns sellable entities only; no checkout/billing state."""

    def __init__(self) -> None:
        self._products: dict[str, Product] = {}
        self._bundles: dict[str, Bundle] = {}

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
        sku: str | None = None,
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
            sku=sku,
        ).normalized()
        self._products[product.product_id] = product
        return product

    def create_bundle(self, bundle: Bundle) -> Bundle:
        normalized = bundle.normalized()
        bundle_product = self._products.get(normalized.bundle_id)
        if bundle_product is None:
            raise ValueError(f"bundle product '{normalized.bundle_id}' does not exist")
        if bundle_product.type != ProductType.BUNDLE:
            raise ValueError(f"product '{normalized.bundle_id}' is not a bundle product")

        for product_id in normalized.product_ids:
            product = self.get_product(product_id)
            if product is None or product.tenant_id != normalized.tenant_id or not product.published:
                raise ValueError(f"bundle '{normalized.bundle_id}' references unsellable product '{product_id}'")

        self._bundles[normalized.bundle_id] = normalized
        return normalized

    def resolve_bundle_products(self, *, bundle_id: str, tenant_id: str) -> list[Product]:
        bundle = self._bundles.get(bundle_id.strip())
        if bundle is None or bundle.tenant_id != tenant_id.strip():
            raise ValueError(f"bundle '{bundle_id}' is not available for tenant '{tenant_id}'")
        return [self.resolve_sellable_product(tenant_id=tenant_id, product_id=pid) for pid in bundle.product_ids]

    def bundle_price(self, *, bundle_id: str, tenant_id: str) -> Decimal:
        bundle = self._bundles.get(bundle_id.strip())
        if bundle is None or bundle.tenant_id != tenant_id.strip():
            raise ValueError(f"bundle '{bundle_id}' is not available for tenant '{tenant_id}'")
        products = self.resolve_bundle_products(bundle_id=bundle_id, tenant_id=tenant_id)
        if bundle.bundle_price is not None:
            return bundle.bundle_price
        return sum((product.price for product in products), Decimal("0"))

    def resolve_sellable_product(self, *, tenant_id: str, product_id: str) -> Product:
        product = self.get_product(product_id)
        if product is None or product.tenant_id != tenant_id.strip() or not product.published:
            raise ValueError(f"product '{product_id}' is not sellable for tenant '{tenant_id}'")
        if not product.capability_ids:
            raise ValueError(f"product '{product_id}' is missing required capability mapping")
        return product

    def list_products(self, *, tenant_id: str, product_type: ProductType | None = None) -> list[CatalogItem]:
        items: list[CatalogItem] = []
        for product in sorted(self._products.values(), key=lambda p: p.product_id):
            if product.tenant_id != tenant_id.strip() or not product.published:
                continue
            if product_type and product.type != product_type:
                continue
            bundle_products: tuple[Product, ...] = ()
            if product.type == ProductType.BUNDLE and product.product_id in self._bundles:
                bundle_products = tuple(self.resolve_bundle_products(bundle_id=product.product_id, tenant_id=tenant_id))
            items.append(
                CatalogItem(
                    product_id=product.product_id,
                    tenant_id=product.tenant_id,
                    type=product.type,
                    title=product.title,
                    price=product.price,
                    currency=product.currency,
                    bundle_products=bundle_products,
                )
            )
        return items

    def get_product(self, product_id: str) -> Product | None:
        return self._products.get(product_id.strip())

    def get_bundle(self, bundle_id: str) -> Bundle | None:
        return self._bundles.get(bundle_id.strip())

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .models import CatalogSnapshot, Offer, Product, TenantCatalogConfig


class InMemoryCatalogStore:
    def __init__(self) -> None:
        self._products: Dict[str, Product] = {}
        self._offers: Dict[str, Offer] = {}
        self._configs: Dict[str, TenantCatalogConfig] = {}
        self._snapshots: Dict[str, CatalogSnapshot] = {}

    def save_product(self, product: Product) -> None:
        self._products[product.product_id] = product

    def get_product(self, product_id: str) -> Optional[Product]:
        return self._products.get(product_id)

    def list_products(self, tenant_id: str, status: Optional[str] = None,
                      segment: Optional[str] = None) -> List[Product]:
        results = [p for p in self._products.values() if p.tenant_id == tenant_id]
        if status:
            results = [p for p in results if p.status == status]
        if segment:
            results = [p for p in results if not p.segment_targets or segment in p.segment_targets]
        return results

    def save_offer(self, offer: Offer) -> None:
        self._offers[offer.offer_id] = offer

    def get_offer(self, offer_id: str) -> Optional[Offer]:
        return self._offers.get(offer_id)

    def list_offers_for_product(self, product_id: str) -> List[Offer]:
        return [o for o in self._offers.values() if o.product_id == product_id]

    def save_config(self, config: TenantCatalogConfig) -> None:
        self._configs[config.tenant_id] = config

    def get_config(self, tenant_id: str) -> Optional[TenantCatalogConfig]:
        return self._configs.get(tenant_id)

    def save_snapshot(self, snapshot: CatalogSnapshot) -> None:
        self._snapshots[snapshot.snapshot_id] = snapshot

    def get_snapshot(self, snapshot_id: str) -> Optional[CatalogSnapshot]:
        return self._snapshots.get(snapshot_id)

    def new_id(self, prefix: str = "") -> str:
        return f"{prefix}-{secrets.token_urlsafe(8)}" if prefix else secrets.token_urlsafe(10)

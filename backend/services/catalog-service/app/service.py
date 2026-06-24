from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .models import CatalogSnapshot, Offer, PricingModelRef, Product, TenantCatalogConfig
from .store import InMemoryCatalogStore

VALID_PRODUCT_TYPES = {"COURSE", "BUNDLE", "SUBSCRIPTION"}
VALID_STATUSES = {"DRAFT", "PUBLISHED", "RETIRED"}
VALID_PRICING_TYPES = {"ONE_TIME", "RECURRING", "USAGE_BASED", "TIERED", "SEAT_BASED", "HYBRID"}


class CatalogService:
    def __init__(self, store: InMemoryCatalogStore) -> None:
        self.store = store

    def create_product(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        product_type = body.get("product_type", "")
        if product_type not in VALID_PRODUCT_TYPES:
            return 400, {"error": "invalid_product_type", "valid": list(VALID_PRODUCT_TYPES)}

        tenant_id = body.get("tenant_id", "")
        sku = body.get("sku", "")
        existing = [p for p in self.store.list_products(tenant_id) if p.sku == sku]
        if existing:
            return 409, {"error": "sku_already_exists"}

        product = Product(
            product_id=self.store.new_id("prod"),
            tenant_id=tenant_id,
            product_type=product_type,
            sku=sku,
            status="DRAFT",
            display_name=body.get("display_name", ""),
            description=body.get("description", ""),
            version=1,
            channel_targets=body.get("channel_targets", []),
            segment_targets=body.get("segment_targets", []),
            details=body.get("details", {}),
        )
        self.store.save_product(product)
        return 201, self._serialize_product(product)

    def update_product(self, product_id: str, tenant_id: str, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        product = self.store.get_product(product_id)
        if not product or product.tenant_id != tenant_id:
            return 404, {"error": "product_not_found"}
        if product.status == "RETIRED":
            return 409, {"error": "retired_products_are_immutable"}

        for field in ("display_name", "description", "channel_targets", "segment_targets", "details"):
            if field in body:
                setattr(product, field, body[field])
        product.updated_at = datetime.now(timezone.utc)
        product.version += 1
        self.store.save_product(product)
        return 200, self._serialize_product(product)

    def publish_product(self, product_id: str, tenant_id: str) -> Tuple[int, Dict[str, Any]]:
        product = self.store.get_product(product_id)
        if not product or product.tenant_id != tenant_id:
            return 404, {"error": "product_not_found"}
        if product.status == "RETIRED":
            return 409, {"error": "cannot_publish_retired_product"}
        if not self.store.list_offers_for_product(product_id):
            return 422, {"error": "product_must_have_at_least_one_offer_before_publishing"}

        product.status = "PUBLISHED"
        product.version += 1
        product.updated_at = datetime.now(timezone.utc)
        self.store.save_product(product)
        return 200, self._serialize_product(product)

    def retire_product(self, product_id: str, tenant_id: str) -> Tuple[int, Dict[str, Any]]:
        product = self.store.get_product(product_id)
        if not product or product.tenant_id != tenant_id:
            return 404, {"error": "product_not_found"}
        product.status = "RETIRED"
        product.version += 1
        product.updated_at = datetime.now(timezone.utc)
        self.store.save_product(product)
        return 200, self._serialize_product(product)

    def get_product(self, product_id: str, tenant_id: str) -> Tuple[int, Dict[str, Any]]:
        product = self.store.get_product(product_id)
        if not product or product.tenant_id != tenant_id:
            return 404, {"error": "product_not_found"}
        return 200, self._serialize_product(product)

    def list_products(self, tenant_id: str, status: Optional[str] = None,
                      segment: Optional[str] = None) -> Tuple[int, Dict[str, Any]]:
        products = self.store.list_products(tenant_id, status, segment)
        return 200, {"products": [self._serialize_product(p) for p in products], "count": len(products)}

    def create_offer(self, product_id: str, tenant_id: str, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        product = self.store.get_product(product_id)
        if not product or product.tenant_id != tenant_id:
            return 404, {"error": "product_not_found"}

        pricing_refs = [
            PricingModelRef(
                pricing_model_id=r["pricing_model_id"],
                pricing_type=r.get("pricing_type", "ONE_TIME"),
                price_book_id=r["price_book_id"],
                billing_period_hint=r.get("billing_period_hint"),
            )
            for r in body.get("pricing_model_refs", [])
        ]
        offer = Offer(
            offer_id=self.store.new_id("offer"),
            product_id=product_id,
            offer_code=body.get("offer_code", ""),
            pricing_model_refs=pricing_refs,
            default_pricing_model_ref=body.get("default_pricing_model_ref", ""),
            discount_policy_refs=body.get("discount_policy_refs", []),
            coupon_policy_ref=body.get("coupon_policy_ref"),
            region_allowlist=body.get("region_allowlist", []),
            currency_allowlist=body.get("currency_allowlist", []),
            min_seats=body.get("min_seats"),
            max_seats=body.get("max_seats"),
            new_customer_only=body.get("new_customer_only", False),
        )
        self.store.save_offer(offer)
        product.offer_ids.append(offer.offer_id)
        product.updated_at = datetime.now(timezone.utc)
        self.store.save_product(product)
        return 201, self._serialize_offer(offer)

    def get_offer(self, offer_id: str) -> Tuple[int, Dict[str, Any]]:
        offer = self.store.get_offer(offer_id)
        if not offer:
            return 404, {"error": "offer_not_found"}
        return 200, self._serialize_offer(offer)

    def resolve_snapshot(self, tenant_id: str, product_ids: List[str]) -> Tuple[int, Dict[str, Any]]:
        products = [self.store.get_product(pid) for pid in product_ids]
        missing = [pid for pid, p in zip(product_ids, products) if not p or p.tenant_id != tenant_id]
        if missing:
            return 404, {"error": "products_not_found", "missing": missing}

        offer_ids = []
        for p in products:
            if p:
                offer_ids.extend(p.offer_ids)

        snapshot = CatalogSnapshot(
            snapshot_id=self.store.new_id("snap"),
            tenant_id=tenant_id,
            product_ids=product_ids,
            offer_ids=offer_ids,
            created_at=datetime.now(timezone.utc),
        )
        self.store.save_snapshot(snapshot)
        return 200, {
            "snapshot_id": snapshot.snapshot_id,
            "tenant_id": tenant_id,
            "product_ids": product_ids,
            "offer_ids": offer_ids,
            "created_at": snapshot.created_at.isoformat(),
        }

    def update_tenant_config(self, tenant_id: str, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        config = self.store.get_config(tenant_id) or TenantCatalogConfig(
            tenant_id=tenant_id,
            default_currency=body.get("default_currency", "USD"),
            supported_currencies=body.get("supported_currencies", ["USD"]),
        )
        for field in ("default_currency", "supported_currencies", "coupon_stackability_mode",
                      "publish_approval_required", "segment_policy", "channel_policy",
                      "regional_compliance_tags"):
            if field in body:
                setattr(config, field, body[field])
        self.store.save_config(config)
        return 200, {
            "tenant_id": config.tenant_id,
            "default_currency": config.default_currency,
            "supported_currencies": config.supported_currencies,
            "coupon_stackability_mode": config.coupon_stackability_mode,
            "publish_approval_required": config.publish_approval_required,
        }

    def _serialize_product(self, p: Product) -> Dict[str, Any]:
        return {
            "product_id": p.product_id, "tenant_id": p.tenant_id,
            "product_type": p.product_type, "sku": p.sku, "status": p.status,
            "display_name": p.display_name, "description": p.description,
            "version": p.version, "offer_ids": p.offer_ids,
            "channel_targets": p.channel_targets, "segment_targets": p.segment_targets,
            "details": p.details,
            "created_at": p.created_at.isoformat(), "updated_at": p.updated_at.isoformat(),
        }

    def _serialize_offer(self, o: Offer) -> Dict[str, Any]:
        return {
            "offer_id": o.offer_id, "product_id": o.product_id, "offer_code": o.offer_code,
            "pricing_model_refs": [
                {"pricing_model_id": r.pricing_model_id, "pricing_type": r.pricing_type,
                 "price_book_id": r.price_book_id, "billing_period_hint": r.billing_period_hint}
                for r in o.pricing_model_refs
            ],
            "default_pricing_model_ref": o.default_pricing_model_ref,
            "discount_policy_refs": o.discount_policy_refs,
            "new_customer_only": o.new_customer_only,
            "region_allowlist": o.region_allowlist,
            "currency_allowlist": o.currency_allowlist,
        }

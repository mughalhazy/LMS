from __future__ import annotations
import pytest
from app.service import CatalogService
from app.store import InMemoryCatalogStore


def _svc() -> CatalogService:
    return CatalogService(InMemoryCatalogStore())


def _product(svc: CatalogService, **kwargs) -> dict:
    body = {"tenant_id": "t1", "product_type": "COURSE", "sku": "SKU-001",
            "display_name": "Python Course", "description": "Intro Python", **kwargs}
    _, p = svc.create_product(body)
    return p


def _offer(svc: CatalogService, product_id: str) -> dict:
    body = {"tenant_id": "t1", "offer_code": "OFF-001",
            "pricing_model_refs": [{"pricing_model_id": "pm1", "pricing_type": "ONE_TIME", "price_book_id": "pb1"}],
            "default_pricing_model_ref": "pm1"}
    _, o = svc.create_offer(product_id, "t1", body)
    return o


def test_create_product():
    svc = _svc()
    status, body = svc.create_product({"tenant_id": "t1", "product_type": "COURSE", "sku": "SKU-1",
                                        "display_name": "A", "description": "B"})
    assert status == 201
    assert body["status"] == "DRAFT"


def test_duplicate_sku_rejected():
    svc = _svc()
    _product(svc)
    status, body = svc.create_product({"tenant_id": "t1", "product_type": "COURSE", "sku": "SKU-001",
                                        "display_name": "X", "description": "Y"})
    assert status == 409


def test_invalid_product_type():
    svc = _svc()
    status, _ = svc.create_product({"tenant_id": "t1", "product_type": "INVALID", "sku": "X",
                                    "display_name": "A", "description": "B"})
    assert status == 400


def test_publish_requires_offer():
    svc = _svc()
    p = _product(svc)
    status, body = svc.publish_product(p["product_id"], "t1")
    assert status == 422


def test_publish_with_offer():
    svc = _svc()
    p = _product(svc)
    _offer(svc, p["product_id"])
    status, body = svc.publish_product(p["product_id"], "t1")
    assert status == 200
    assert body["status"] == "PUBLISHED"


def test_retire_product():
    svc = _svc()
    p = _product(svc)
    status, body = svc.retire_product(p["product_id"], "t1")
    assert status == 200
    assert body["status"] == "RETIRED"


def test_retired_product_immutable():
    svc = _svc()
    p = _product(svc)
    svc.retire_product(p["product_id"], "t1")
    status, _ = svc.update_product(p["product_id"], "t1", {"display_name": "New"})
    assert status == 409


def test_list_products_filter_status():
    svc = _svc()
    p = _product(svc)
    _offer(svc, p["product_id"])
    svc.publish_product(p["product_id"], "t1")
    _product(svc, sku="SKU-002")
    status, body = svc.list_products("t1", status="PUBLISHED")
    assert status == 200
    assert body["count"] == 1


def test_resolve_snapshot():
    svc = _svc()
    p = _product(svc)
    _offer(svc, p["product_id"])
    status, body = svc.resolve_snapshot("t1", [p["product_id"]])
    assert status == 200
    assert "snapshot_id" in body
    assert p["product_id"] in body["product_ids"]


def test_tenant_config():
    svc = _svc()
    status, body = svc.update_tenant_config("t1", {"default_currency": "PKR",
                                                     "supported_currencies": ["PKR", "USD"]})
    assert status == 200
    assert body["default_currency"] == "PKR"

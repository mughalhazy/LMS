from decimal import Decimal
from pathlib import Path
import sys

import pytest

SERVICE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
for path in (SERVICE_ROOT, REPO_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from app.catalog import ProductCatalog
from app.models import ProductCatalogEntry

from backend.services.shared.models.product import Product, ProductType


def _product(product_id: str, kind: ProductType = ProductType.COURSE) -> Product:
    return Product(
        product_id=product_id,
        name=f"Product {product_id}",
        type=kind,
        price=Decimal("49.99"),
        currency="USD",
    )


def test_products_are_linked_to_courses_without_duplication() -> None:
    catalog = ProductCatalog()

    entry = ProductCatalogEntry(product=_product("prod-course-1"), course_ids=["course-2", "course-1", "course-1"])
    saved = catalog.upsert(entry)

    assert saved.course_ids == ["course-1", "course-2"]
    assert catalog.get("prod-course-1") is not None


def test_course_cannot_be_linked_to_two_products() -> None:
    catalog = ProductCatalog()
    catalog.upsert(ProductCatalogEntry(product=_product("prod-course-1"), course_ids=["course-1"]))

    with pytest.raises(ValueError, match="already linked"):
        catalog.upsert(ProductCatalogEntry(product=_product("prod-course-2"), course_ids=["course-1"]))


def test_existing_product_relink_releases_old_course_link() -> None:
    catalog = ProductCatalog()
    catalog.upsert(ProductCatalogEntry(product=_product("prod-course-1"), course_ids=["course-1"]))
    catalog.upsert(ProductCatalogEntry(product=_product("prod-course-1"), course_ids=["course-2"]))

    catalog.upsert(ProductCatalogEntry(product=_product("prod-course-2"), course_ids=["course-1"]))
    assert catalog.get("prod-course-2") is not None

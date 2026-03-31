from __future__ import annotations

from dataclasses import replace

from .models import ProductCatalogEntry


class ProductCatalog:
    """In-memory product catalog with one-to-one course product linking."""

    def __init__(self) -> None:
        self._by_product_id: dict[str, ProductCatalogEntry] = {}
        self._course_to_product: dict[str, str] = {}

    def upsert(self, entry: ProductCatalogEntry) -> ProductCatalogEntry:
        existing = self._by_product_id.get(entry.product.product_id)
        if existing is not None:
            for course_id in existing.course_ids:
                self._course_to_product.pop(course_id, None)

        self._assert_no_course_duplication(entry)

        normalized = replace(entry, course_ids=sorted(set(entry.course_ids)))
        self._by_product_id[entry.product.product_id] = normalized

        for course_id in normalized.course_ids:
            self._course_to_product[course_id] = normalized.product.product_id

        return normalized

    def get(self, product_id: str) -> ProductCatalogEntry | None:
        return self._by_product_id.get(product_id)

    def list_all(self) -> list[ProductCatalogEntry]:
        return list(self._by_product_id.values())

    def _assert_no_course_duplication(self, entry: ProductCatalogEntry) -> None:
        for course_id in entry.course_ids:
            linked = self._course_to_product.get(course_id)
            if linked is None:
                continue
            if linked != entry.product.product_id:
                raise ValueError(
                    f"course_id '{course_id}' is already linked to product '{linked}'"
                )

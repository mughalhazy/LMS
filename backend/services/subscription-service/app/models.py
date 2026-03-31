from __future__ import annotations

from dataclasses import dataclass, field

from backend.services.shared.models.product import Product


@dataclass(frozen=True)
class ProductCatalogEntry:
    product: Product
    course_ids: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        normalized = sorted(set(self.course_ids))
        object.__setattr__(self, "course_ids", normalized)

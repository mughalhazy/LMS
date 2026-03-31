from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class ProductType(str, Enum):
    COURSE = "course"
    BUNDLE = "bundle"
    FEATURE = "feature"


@dataclass(frozen=True)
class Product:
    product_id: str
    name: str
    type: ProductType
    price: Decimal
    currency: str

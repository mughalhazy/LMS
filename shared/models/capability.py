from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Capability:
    capability_id: str
    name: str
    description: str
    category: str
    default_enabled: bool = False

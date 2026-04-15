from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ObservabilityHooks:
    counters: dict[str, int] = field(default_factory=dict)

    def increment(self, metric: str, count: int = 1) -> None:
        self.counters[metric] = self.counters.get(metric, 0) + count

    def snapshot(self) -> dict[str, int]:
        return dict(self.counters)

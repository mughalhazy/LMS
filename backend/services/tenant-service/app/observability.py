from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field


@dataclass
class MetricsRegistry:
    counters: dict[str, int] = field(default_factory=dict)
    latencies_ms: dict[str, list[float]] = field(default_factory=dict)

    def inc(self, metric: str, by: int = 1) -> None:
        self.counters[metric] = self.counters.get(metric, 0) + by

    @contextmanager
    def timer(self, metric: str):
        start = time.perf_counter()
        yield
        elapsed = (time.perf_counter() - start) * 1000
        self.latencies_ms.setdefault(metric, []).append(elapsed)

    def export(self) -> dict[str, float | int]:
        output: dict[str, float | int] = dict(self.counters)
        for metric, values in self.latencies_ms.items():
            if values:
                output[f"{metric}.count"] = len(values)
                output[f"{metric}.p95_ms"] = sorted(values)[max(int(len(values) * 0.95) - 1, 0)]
        return output

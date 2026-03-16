from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from time import perf_counter
from typing import Dict


@dataclass
class MetricsSnapshot:
    counters: Dict[str, int]


class MetricsRecorder:
    def __init__(self) -> None:
        self._counters: Dict[str, int] = defaultdict(int)

    def increment(self, metric: str, value: int = 1) -> None:
        self._counters[metric] += value

    def observe_duration_ms(self, metric: str, duration_ms: int) -> None:
        self._counters[f"{metric}_last_ms"] = duration_ms

    def snapshot(self) -> MetricsSnapshot:
        return MetricsSnapshot(counters=dict(self._counters))


class Timer:
    def __init__(self) -> None:
        self._start = perf_counter()

    def elapsed_ms(self) -> int:
        return int((perf_counter() - self._start) * 1000)

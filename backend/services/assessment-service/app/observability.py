from __future__ import annotations


class ServiceMetrics:
    def __init__(self) -> None:
        self.counters: dict[str, int] = {
            "assessments_created": 0,
            "assessments_updated": 0,
            "attempts_started": 0,
            "submissions_recorded": 0,
            "attempts_graded": 0,
        }

    def inc(self, key: str) -> None:
        self.counters[key] = self.counters.get(key, 0) + 1

    def snapshot(self) -> dict[str, int]:
        return dict(self.counters)

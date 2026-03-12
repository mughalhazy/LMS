"""Queue integration contracts for media processing jobs."""

from __future__ import annotations

from collections import deque
from typing import Deque, Optional, Protocol

from .models import ProcessingJob


class ProcessingQueue(Protocol):
    def enqueue(self, job: ProcessingJob) -> None:
        ...

    def dequeue(self) -> Optional[ProcessingJob]:
        ...


class InMemoryProcessingQueue:
    """Simple in-memory queue adapter for orchestration and tests."""

    def __init__(self) -> None:
        self._jobs: Deque[ProcessingJob] = deque()

    def enqueue(self, job: ProcessingJob) -> None:
        self._jobs.append(job)

    def dequeue(self) -> Optional[ProcessingJob]:
        if not self._jobs:
            return None
        return self._jobs.popleft()

    def __len__(self) -> int:
        return len(self._jobs)

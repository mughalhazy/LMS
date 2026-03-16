from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from .models import EventFamily, ForwardResult, NormalizedEvent


class EventForwarder(ABC):
    @property
    @abstractmethod
    def target(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def should_forward(self, event: NormalizedEvent) -> bool:
        raise NotImplementedError

    @abstractmethod
    def forward(self, event: NormalizedEvent) -> ForwardResult:
        raise NotImplementedError


class AnalyticsForwarder(EventForwarder):
    @property
    def target(self) -> str:
        return "analytics"

    def should_forward(self, event: NormalizedEvent) -> bool:
        return True

    def forward(self, event: NormalizedEvent) -> ForwardResult:
        return ForwardResult(target=self.target, accepted=True)


class AIForwarder(EventForwarder):
    _eligible = {
        EventFamily.USER,
        EventFamily.COURSE,
        EventFamily.LESSON,
        EventFamily.PROGRESS,
        EventFamily.ASSESSMENT,
        EventFamily.CERTIFICATE,
        EventFamily.AI,
    }

    @property
    def target(self) -> str:
        return "ai"

    def should_forward(self, event: NormalizedEvent) -> bool:
        return event.family in self._eligible

    def forward(self, event: NormalizedEvent) -> ForwardResult:
        if not self.should_forward(event):
            return ForwardResult(target=self.target, accepted=False, reason="family_not_enabled")
        return ForwardResult(target=self.target, accepted=True)


class ForwardingPipeline:
    def __init__(self, forwarders: List[EventForwarder]):
        self._forwarders = forwarders

    def publish(self, event: NormalizedEvent) -> List[ForwardResult]:
        return [forwarder.forward(event) for forwarder in self._forwarders]

    def health(self) -> bool:
        return True

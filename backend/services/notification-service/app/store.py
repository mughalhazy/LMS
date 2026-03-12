from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from itertools import count

from .models import NotificationEvent, NotificationMessage, NotificationPreference


@dataclass
class EventRoute:
    route_id: str
    tenant_id: str
    event_type: str
    category: str
    channels: list[str]
    subject_template: str
    body_template: str


class InMemoryNotificationStore:
    def __init__(self) -> None:
        self._counter = count(1)
        self.preferences: dict[tuple[str, str, str], NotificationPreference] = {}
        self.routes: dict[tuple[str, str], EventRoute] = {}
        self.events: dict[str, NotificationEvent] = {}
        self.messages: dict[str, NotificationMessage] = {}
        self.queue: deque[str] = deque()

    def new_id(self, prefix: str) -> str:
        return f"{prefix}_{next(self._counter)}"

    def upsert_preference(self, preference: NotificationPreference) -> None:
        self.preferences[(preference.tenant_id, preference.user_id, preference.category)] = preference

    def get_preference(self, tenant_id: str, user_id: str, category: str) -> NotificationPreference | None:
        return self.preferences.get((tenant_id, user_id, category))

    def list_preferences(self, tenant_id: str, user_id: str) -> list[NotificationPreference]:
        return [
            pref
            for pref in self.preferences.values()
            if pref.tenant_id == tenant_id and pref.user_id == user_id
        ]

    def upsert_route(self, route: EventRoute) -> None:
        self.routes[(route.tenant_id, route.event_type)] = route

    def get_route(self, tenant_id: str, event_type: str) -> EventRoute | None:
        return self.routes.get((tenant_id, event_type))

    def save_event(self, event: NotificationEvent) -> None:
        self.events[event.event_id] = event

    def save_message(self, message: NotificationMessage) -> None:
        self.messages[message.message_id] = message
        self.queue.append(message.message_id)

    def next_message(self) -> NotificationMessage | None:
        if not self.queue:
            return None
        message_id = self.queue.popleft()
        return self.messages[message_id]

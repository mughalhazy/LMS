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


class DatabaseUnavailableError(RuntimeError):
    """Domain-specific exception."""


class ServiceUnavailableError(RuntimeError):
    """Domain-specific exception."""


class InMemoryNotificationStore:
    def __init__(self) -> None:
        self._counter = count(1)
        self.preferences: dict[tuple[str, str, str], NotificationPreference] = {}
        self.routes: dict[tuple[str, str], EventRoute] = {}
        self.events: dict[str, NotificationEvent] = {}
        self.messages: dict[str, NotificationMessage] = {}
        self.phone_bindings: dict[tuple[str, str], str] = {}
        self.queue: deque[str] = deque()
        self.service_running = True
        self.database_available = True
        self.event_bus_available = True
        self.gateway_available = True
        self.queue_delay_cycles = 0

    def crash_service(self) -> None:
        self.service_running = False

    def restart_service(self) -> None:
        self.service_running = True

    def set_database_availability(self, available: bool) -> None:
        self.database_available = available

    def set_event_bus_availability(self, available: bool) -> None:
        self.event_bus_available = available

    def set_gateway_availability(self, available: bool) -> None:
        self.gateway_available = available

    def set_queue_delay_cycles(self, cycles: int) -> None:
        self.queue_delay_cycles = max(cycles, 0)

    def assert_service_running(self) -> None:
        if not self.service_running:
            raise ServiceUnavailableError("notification service is restarting")

    def assert_database_available(self) -> None:
        if not self.database_available:
            raise DatabaseUnavailableError("database connection unavailable")

    def new_id(self, prefix: str) -> str:
        return f"{prefix}_{next(self._counter)}"

    def upsert_preference(self, preference: NotificationPreference) -> None:
        self.assert_database_available()
        self.preferences[(preference.tenant_id, preference.user_id, preference.category)] = preference

    def get_preference(self, tenant_id: str, user_id: str, category: str) -> NotificationPreference | None:
        self.assert_database_available()
        return self.preferences.get((tenant_id, user_id, category))

    def list_preferences(self, tenant_id: str, user_id: str) -> list[NotificationPreference]:
        self.assert_database_available()
        return [
            pref
            for pref in self.preferences.values()
            if pref.tenant_id == tenant_id and pref.user_id == user_id
        ]

    def upsert_route(self, route: EventRoute) -> None:
        self.assert_database_available()
        self.routes[(route.tenant_id, route.event_type)] = route

    def get_route(self, tenant_id: str, event_type: str) -> EventRoute | None:
        self.assert_database_available()
        return self.routes.get((tenant_id, event_type))

    def save_event(self, event: NotificationEvent) -> None:
        self.assert_database_available()
        self.events[event.event_id] = event

    def save_message(self, message: NotificationMessage) -> None:
        self.assert_database_available()
        self.messages[message.message_id] = message
        self.queue.append(message.message_id)

    def upsert_phone_binding(self, *, tenant_id: str, phone_hash: str, user_id: str) -> None:
        self.assert_database_available()
        self.phone_bindings[(tenant_id, phone_hash)] = user_id

    def get_user_by_phone_hash(self, *, tenant_id: str, phone_hash: str) -> str | None:
        self.assert_database_available()
        return self.phone_bindings.get((tenant_id, phone_hash))

    def consume_delay_cycle(self) -> bool:
        if self.queue_delay_cycles <= 0:
            return False
        self.queue_delay_cycles -= 1
        return True

    def next_message(self) -> NotificationMessage | None:
        if not self.queue:
            return None
        message_id = self.queue.popleft()
        return self.messages[message_id]

from __future__ import annotations

from typing import Protocol

from .models import AutomationDispatch, AutomationHook, HelpdeskTicket


class HelpdeskStore(Protocol):
    def save_ticket(self, ticket: HelpdeskTicket) -> HelpdeskTicket: ...

    def get_ticket(self, ticket_id: str) -> HelpdeskTicket | None: ...

    def list_tickets(self, tenant_id: str) -> list[HelpdeskTicket]: ...

    def save_hook(self, hook: AutomationHook) -> AutomationHook: ...

    def list_hooks(self, tenant_id: str) -> list[AutomationHook]: ...

    def save_dispatch(self, dispatch: AutomationDispatch) -> AutomationDispatch: ...

    def list_dispatches(self, tenant_id: str) -> list[AutomationDispatch]: ...


class InMemoryHelpdeskStore:
    def __init__(self) -> None:
        self._tickets: dict[str, HelpdeskTicket] = {}
        self._hooks: dict[str, AutomationHook] = {}
        self._dispatches: dict[str, AutomationDispatch] = {}

    def save_ticket(self, ticket: HelpdeskTicket) -> HelpdeskTicket:
        self._tickets[ticket.ticket_id] = ticket
        return ticket

    def get_ticket(self, ticket_id: str) -> HelpdeskTicket | None:
        return self._tickets.get(ticket_id)

    def list_tickets(self, tenant_id: str) -> list[HelpdeskTicket]:
        return [ticket for ticket in self._tickets.values() if ticket.tenant_id == tenant_id]

    def save_hook(self, hook: AutomationHook) -> AutomationHook:
        self._hooks[hook.hook_id] = hook
        return hook

    def list_hooks(self, tenant_id: str) -> list[AutomationHook]:
        return [hook for hook in self._hooks.values() if hook.tenant_id == tenant_id]

    def save_dispatch(self, dispatch: AutomationDispatch) -> AutomationDispatch:
        self._dispatches[dispatch.dispatch_id] = dispatch
        return dispatch

    def list_dispatches(self, tenant_id: str) -> list[AutomationDispatch]:
        return [dispatch for dispatch in self._dispatches.values() if dispatch.tenant_id == tenant_id]

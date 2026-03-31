from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from .base_adapter import CommunicationAdapter, CommunicationUser

WhatsAppOperationType = Literal["attendance", "reminder", "update"]


@dataclass(frozen=True)
class WhatsAppInteractiveReply:
    user_id: str
    workflow_id: str
    action: str
    operation: WhatsAppOperationType
    payload: dict[str, Any]
    received_at: datetime


class WhatsAppAdapter(CommunicationAdapter):
    provider_key = "whatsapp"

    def __init__(self, disabled_recipients: set[str] | None = None) -> None:
        self.disabled_recipients = disabled_recipients or set()

    def send_message(self, user: CommunicationUser, message: str) -> bool:
        if not user.user_id:
            return False
        if user.user_id in self.disabled_recipients:
            return False
        return message.strip() != ""

    def build_workflow_message(
        self,
        *,
        operation: WhatsAppOperationType,
        workflow_id: str,
        message: str,
        choices: list[str] | None = None,
    ) -> str:
        """Encode an operation-aware payload for WhatsApp interactive flows."""

        choice_str = "|".join(choices or ["ACK"])
        return f"[{operation.upper()}|{workflow_id}|{choice_str}] {message.strip()}"

    def parse_interactive_reply(self, *, user_id: str, reply: str) -> WhatsAppInteractiveReply | None:
        """Parse compact reply protocol: WF:<workflow_id>|OP:<operation>|ACTION:<value>|k=v."""

        raw = reply.strip()
        if not raw.startswith("WF:"):
            return None

        parts = [part.strip() for part in raw.split("|") if part.strip()]
        tokens: dict[str, str] = {}
        extra_payload: dict[str, Any] = {}

        for part in parts:
            if ":" in part:
                key, value = part.split(":", 1)
                tokens[key.strip().lower()] = value.strip()
            elif "=" in part:
                key, value = part.split("=", 1)
                extra_payload[key.strip()] = value.strip()

        workflow_id = tokens.get("wf")
        operation = tokens.get("op", "update").lower()
        action = tokens.get("action", "ack").lower()

        if not workflow_id or operation not in {"attendance", "reminder", "update"}:
            return None

        return WhatsAppInteractiveReply(
            user_id=user_id,
            workflow_id=workflow_id,
            action=action,
            operation=operation,  # type: ignore[arg-type]
            payload=extra_payload,
            received_at=datetime.utcnow(),
        )

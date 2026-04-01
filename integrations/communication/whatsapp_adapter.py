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

    def render_template_message(self, *, template_name: str, context: dict[str, Any]) -> str:
        """Render WhatsApp-safe workflow templates for academy notifications."""

        templates = {
            "attendance_notification": (
                "Attendance update: {student_name} is marked {attendance_status} "
                "for {session_date}."
            ),
            "fee_reminder": (
                "Fee reminder: invoice {invoice_id} of {amount} {currency} "
                "is due on {due_date}."
            ),
            "fee_overdue_escalation": (
                "Overdue alert: invoice {invoice_id} of {amount} {currency} "
                "was due on {due_date}. Please pay immediately."
            ),
            "progress_update": (
                "Progress update: {student_name} completed {progress_percent}% "
                "in {course_name}."
            ),
        }
        template = templates.get(template_name, "{message}")
        safe_context = {
            "student_name": str(context.get("student_name", "Student")),
            "attendance_status": str(context.get("attendance_status", "present")),
            "session_date": str(context.get("session_date", "today")),
            "invoice_id": str(context.get("invoice_id", "invoice")),
            "amount": str(context.get("amount", "0")),
            "currency": str(context.get("currency", "USD")),
            "due_date": str(context.get("due_date", "soon")),
            "progress_percent": str(context.get("progress_percent", "0")),
            "course_name": str(context.get("course_name", "course")),
            "message": str(context.get("message", "Workflow update.")),
        }
        return template.format(**safe_context).strip()

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
        if operation == "fee":
            operation = "reminder"
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

    def classify_free_text_reply(self, *, user_id: str, reply: str) -> WhatsAppInteractiveReply | None:
        """Classify plain-text replies when interactive tokens are unavailable."""

        normalized = " ".join(reply.lower().strip().split())
        if not normalized:
            return None

        if normalized in {"present", "yes", "confirm", "confirmed", "attending"}:
            operation = "attendance"
            action = "confirm"
        elif normalized in {"absent", "no", "decline"}:
            operation = "attendance"
            action = "decline"
        elif normalized in {"ack", "ok", "okay", "received", "seen"}:
            operation = "reminder"
            action = "ack"
        elif normalized.startswith("what") or normalized.startswith("how") or "?" in normalized:
            operation = "update"
            action = "query"
        else:
            return None

        return WhatsAppInteractiveReply(
            user_id=user_id,
            workflow_id="ad-hoc",
            action=action,
            operation=operation,  # type: ignore[arg-type]
            payload={"raw_reply": reply.strip()},
            received_at=datetime.utcnow(),
        )

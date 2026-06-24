from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .models import (
    MANDATORY_MESSAGE_TYPES, PERSONA_COMMANDS,
    ConversationSession, OutboundMessage,
)

# Action classification — BC-INT-01
ACTION_HANDLERS = {
    "PAY": "commerce.initiate_payment",
    "WAIVE": "ledger.waive_fee",
    "ENROLL": "enrollment.confirm",
    "INFO": "course.get_details",
    "APPROVE": "workflow.approve",
    "REJECT": "workflow.reject",
    "JOIN": "enrollment.reserve_seat",
    "CONTACT": "notification.contact_learner",
    "1": "attendance.mark_present",
    "2": "attendance.mark_absent",
    "3": "attendance.mark_late",
}


class InteractionLayerService:
    def __init__(self) -> None:
        self._sessions: Dict[str, ConversationSession] = {}
        self._dispatched_actions: Dict[str, str] = {}  # action_id → handled (idempotency)

    def get_or_create_session(self, user_id: str, tenant_id: str, persona: str) -> Tuple[int, Dict[str, Any]]:
        session_key = f"{tenant_id}:{user_id}"
        session = self._sessions.get(session_key)
        if not session:
            session = ConversationSession(
                session_id=f"sess-{secrets.token_urlsafe(8)}",
                user_id=user_id, tenant_id=tenant_id, persona=persona,
            )
            self._sessions[session_key] = session
        return 200, self._serialize_session(session)

    def build_action_message(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        message_type = body.get("message_type", "")
        if message_type not in MANDATORY_MESSAGE_TYPES:
            return 400, {"error": "unknown_message_type",
                         "valid_types": list(MANDATORY_MESSAGE_TYPES.keys())}

        actions = MANDATORY_MESSAGE_TYPES[message_type]
        content = self._build_content(message_type, body.get("context", {}))

        # BC-INT-01: every message must embed executable actions
        message = OutboundMessage(
            message_id=f"msg-{secrets.token_urlsafe(8)}",
            user_id=body.get("user_id", ""),
            tenant_id=body.get("tenant_id", ""),
            message_type=message_type,
            content=content,
            action_options=[{"key": a.split(":")[0], "label": a.split(":")[1] if ":" in a else a}
                             for a in actions],
            channel=body.get("channel", "whatsapp"),
        )
        return 200, {
            "message_id": message.message_id,
            "content": message.content,
            "action_options": message.action_options,
            "channel": message.channel,
        }

    def handle_reply(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        reply = body.get("reply", "").strip().upper()
        action_id = body.get("action_id", secrets.token_urlsafe(8))
        user_id = body.get("user_id", "")
        tenant_id = body.get("tenant_id", "")

        # BC-INT-01: duplicate replies must not trigger duplicate actions
        if action_id in self._dispatched_actions:
            return 200, {"status": "already_handled", "action_id": action_id,
                         "dispatched_to": self._dispatched_actions[action_id]}

        handler = ACTION_HANDLERS.get(reply)
        if not handler:
            return 422, {"error": "unrecognised_reply", "reply": reply,
                          "hint": "Send a valid action keyword from the message options"}

        self._dispatched_actions[action_id] = handler
        self._update_session_history(user_id, tenant_id, reply, handler)

        return 200, {
            "action_id": action_id, "reply": reply,
            "dispatched_to": handler, "status": "dispatched",
        }

    def send_onboarding_message(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        """BC-INT-02: send role-specific onboarding message explaining available commands."""
        user_id = body.get("user_id", "")
        tenant_id = body.get("tenant_id", "")
        persona = body.get("persona", "learner")
        channel = body.get("channel", "whatsapp")

        commands = PERSONA_COMMANDS.get(persona)
        if not commands:
            return 400, {"error": "unknown_persona", "valid": list(PERSONA_COMMANDS.keys())}

        command_list = ", ".join(commands)
        content = (
            f"Welcome! You are registered as *{persona}*. "
            f"Here are your available commands: {command_list}. "
            f"Reply with any command to get started, or type HELP for assistance."
        )
        message = OutboundMessage(
            message_id=f"msg-{secrets.token_urlsafe(8)}",
            user_id=user_id,
            tenant_id=tenant_id,
            message_type="onboarding",
            content=content,
            action_options=[{"key": cmd, "label": cmd} for cmd in commands],
            channel=channel,
        )
        return 200, {
            "message_id": message.message_id,
            "persona": persona,
            "content": message.content,
            "action_options": message.action_options,
            "channel": channel,
            "onboarding": True,
        }

    def get_persona_commands(self, persona: str) -> Tuple[int, Dict[str, Any]]:
        commands = PERSONA_COMMANDS.get(persona)
        if not commands:
            return 404, {"error": "unknown_persona", "valid": list(PERSONA_COMMANDS.keys())}
        return 200, {"persona": persona, "commands": commands,
                     "onboarding_hint": f"Available commands for {persona}: {', '.join(commands)}"}

    def _build_content(self, message_type: str, context: Dict[str, Any]) -> str:
        templates = {
            "fee_overdue": "Your fee of {amount} is overdue. Reply PAY to initiate payment or WAIVE with reason.",
            "attendance_alert": "Attendance session open for {batch}. Reply 1=Present, 2=Absent, 3=Late.",
            "enrollment_invitation": "You are invited to enroll in {course}. Reply ENROLL to confirm or INFO for details.",
            "at_risk_learner": "Learner {learner} is at risk. Reply CONTACT to send them a message.",
            "pending_approval": "Pending approval: {item}. Reply APPROVE or REJECT.",
            "new_batch_open": "New batch {batch} is open. Reply JOIN to reserve a seat.",
        }
        template = templates.get(message_type, f"{message_type} — please reply with an action.")
        try:
            return template.format(**context)
        except KeyError:
            return template

    def _update_session_history(self, user_id: str, tenant_id: str, reply: str, handler: str) -> None:
        session_key = f"{tenant_id}:{user_id}"
        session = self._sessions.get(session_key)
        if session:
            session.history.append({"reply": reply, "handler": handler,
                                     "at": datetime.now(timezone.utc).isoformat()})
            session.updated_at = datetime.now(timezone.utc)

    def _serialize_session(self, s: ConversationSession) -> Dict[str, Any]:
        return {"session_id": s.session_id, "user_id": s.user_id, "persona": s.persona,
                "flow_step": s.flow_step, "history_count": len(s.history)}

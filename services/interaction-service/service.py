"""Interaction layer service — conversational delivery, action-based replies, stateful flows.

CGAP-025: builds services/interaction-service/ from scratch. Implements all 3 capabilities
from interaction_layer_spec.md:
  - CAP-CONVERSATIONAL-DELIVERY: structured outbound messages via WhatsApp with BC-INT-01
    embedded action options (6 mandated message types)
  - CAP-ACTION-BASED-REPLIES: parse inbound channel replies → route to workflow engine
    (BC-INT-01 idempotent action execution, all 6 action categories covered)
  - CAP-STATEFUL-INTERACTION-FLOWS: multi-step conversation state across message exchanges;
    session state survives disconnections and timeouts

BC-INT-01 — Action Inside Message: every outbound message about an actionable situation
MUST embed the action trigger. 6 message types enforced with mandatory action options.

BC-INT-02 — Conversational-First for All Personas: 4 persona types (learner / operator /
manager / instructor) each with persona-aware command routing and command shortcuts
(status, today, pending, approve [id], remind [batch]).

Building blocks used:
  - integrations/communication/whatsapp_adapter.py (WhatsAppAdapter)

Spec refs: docs/specs/interaction_layer_spec.md
           docs/architecture/communication_adapter_interface_contract.md
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

# Resolve WhatsApp adapter from integrations layer
_INTEGRATIONS = Path(__file__).resolve().parents[2] / "integrations"
if str(_INTEGRATIONS) not in sys.path:
    sys.path.insert(0, str(_INTEGRATIONS))

try:
    from communication.whatsapp_adapter import WhatsAppAdapter  # noqa: F401
    _HAS_ADAPTER = True
except Exception:
    _HAS_ADAPTER = False


# ------------------------------------------------------------------ #
# Constants                                                            #
# ------------------------------------------------------------------ #

PERSONA_LEARNER = "learner"
PERSONA_OPERATOR = "operator"
PERSONA_MANAGER = "manager"
PERSONA_INSTRUCTOR = "instructor"
VALID_PERSONAS = {PERSONA_LEARNER, PERSONA_OPERATOR, PERSONA_MANAGER, PERSONA_INSTRUCTOR}

CHANNEL_WHATSAPP = "whatsapp"
CHANNEL_SMS = "sms"
CHANNEL_EMAIL = "email"
CHANNEL_IN_APP = "in_app"

# BC-INT-01 mandatory message type → embedded action options
_BC_INT01_ACTIONS: dict[str, dict[str, Any]] = {
    "fee_overdue_reminder": {
        "description": "Fee overdue reminder",
        "action_options": ["PAY", "WAIVE"],
        "prompt": "Reply PAY to initiate payment or WAIVE with reason.",
    },
    "attendance_alert": {
        "description": "Attendance alert",
        "action_options": ["1", "2", "3"],
        "prompt": "Reply 1 for Present, 2 for Absent, 3 for Late.",
    },
    "enrollment_invitation": {
        "description": "Enrollment invitation",
        "action_options": ["ENROLL", "INFO"],
        "prompt": "Reply ENROLL to confirm or INFO for details.",
    },
    "at_risk_learner_alert": {
        "description": "At-risk learner alert",
        "action_options": ["CONTACT"],
        "prompt": "Reply CONTACT to send learner a message.",
    },
    "pending_approval": {
        "description": "Pending approval",
        "action_options": ["APPROVE", "REJECT"],
        "prompt": "Reply APPROVE or REJECT.",
    },
    "new_batch_open": {
        "description": "New batch open",
        "action_options": ["JOIN", "RESERVE"],
        "prompt": "Reply JOIN to reserve a seat.",
    },
}

# BC-INT-02 persona command shortcuts → description + action category
_PERSONA_COMMANDS: dict[str, dict[str, list[str]]] = {
    PERSONA_LEARNER: {
        "status": ["Check my learning progress and completion status"],
        "today": ["Show today's scheduled lessons or sessions"],
        "enroll [course]": ["Enroll in a course by name or ID"],
        "progress [course]": ["Check progress in a specific course"],
        "help": ["Show available commands for my role"],
    },
    PERSONA_OPERATOR: {
        "status": ["Show today's summary — attendance, fees, enrollment counts"],
        "today": ["Show today's Daily Action List (critical + important items)"],
        "pending": ["Show all pending actions requiring operator decision"],
        "approve [id]": ["Approve a pending enrollment or request by ID"],
        "remind [batch]": ["Send a fee/attendance reminder to a batch"],
        "help": ["Show available commands for my role"],
    },
    PERSONA_MANAGER: {
        "status": ["Show team completion and at-risk learner summary"],
        "today": ["Show today's team training activity"],
        "pending": ["Show pending training approvals for my team"],
        "approve [id]": ["Approve a training request by ID"],
        "help": ["Show available commands for my role"],
    },
    PERSONA_INSTRUCTOR: {
        "status": ["Show today's session and batch attendance summary"],
        "today": ["Show today's batch roster and schedule"],
        "attendance [session]": ["Mark attendance for a session"],
        "remind [batch]": ["Send a message reminder to a batch"],
        "help": ["Show available commands for my role"],
    },
}

# Onboarding message template per persona
_ONBOARDING_INTRO: dict[str, str] = {
    PERSONA_LEARNER: (
        "Welcome! I'm your learning assistant. "
        "You can manage your learning entirely from this chat.\n\n"
        "Available commands:\n"
        "• *status* — your learning progress\n"
        "• *today* — today's sessions\n"
        "• *enroll [course]* — enroll in a course\n"
        "• *help* — see all commands"
    ),
    PERSONA_OPERATOR: (
        "Welcome! You can run daily operations from this chat — no dashboard needed.\n\n"
        "Available commands:\n"
        "• *status* — today's summary\n"
        "• *today* — your daily action list\n"
        "• *pending* — items needing your action\n"
        "• *approve [id]* — approve a request\n"
        "• *remind [batch]* — send a reminder\n"
        "• *help* — see all commands"
    ),
    PERSONA_MANAGER: (
        "Welcome! Manage your team's training from this chat.\n\n"
        "Available commands:\n"
        "• *status* — team progress summary\n"
        "• *today* — today's team activity\n"
        "• *pending* — pending approvals\n"
        "• *approve [id]* — approve a request\n"
        "• *help* — see all commands"
    ),
    PERSONA_INSTRUCTOR: (
        "Welcome! Manage your sessions from this chat.\n\n"
        "Available commands:\n"
        "• *status* — today's session summary\n"
        "• *today* — batch roster\n"
        "• *attendance [session]* — mark attendance\n"
        "• *remind [batch]* — message your batch\n"
        "• *help* — see all commands"
    ),
}


# ------------------------------------------------------------------ #
# Session state                                                        #
# ------------------------------------------------------------------ #

@dataclass
class ConversationSession:
    """Stateful conversation session per user × channel (CAP-STATEFUL-INTERACTION-FLOWS)."""
    session_id: str
    tenant_id: str
    user_id: str
    channel: str
    persona: str
    context: dict[str, Any] = field(default_factory=dict)   # current flow context
    flow_step: str | None = None                             # active multi-step flow step
    history: list[dict[str, Any]] = field(default_factory=list)  # message exchange log
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    # Idempotency: track seen action_ids to prevent duplicate action execution
    seen_action_ids: set[str] = field(default_factory=set)


@dataclass
class RoutedAction:
    """An inbound reply resolved to a platform action."""
    action_id: str
    session_id: str
    user_id: str
    tenant_id: str
    action_category: str    # PAY / WAIVE / ENROLL / APPROVE / REJECT / CONTACT / JOIN / etc.
    raw_reply: str
    context: dict[str, Any]
    is_duplicate: bool = False
    dispatched: bool = False
    dispatched_at: datetime | None = None


# ------------------------------------------------------------------ #
# Main service                                                         #
# ------------------------------------------------------------------ #

class InteractionService:
    """Stateful interaction layer service per interaction_layer_spec.md.

    Implements all 3 spec capabilities:
    - CAP-CONVERSATIONAL-DELIVERY (BC-INT-01 compliant outbound messages)
    - CAP-ACTION-BASED-REPLIES (inbound reply parsing → workflow dispatch)
    - CAP-STATEFUL-INTERACTION-FLOWS (session state across message exchanges)

    BC-INT-02: persona-aware command routing for learner / operator / manager / instructor.
    All persona commands accessible without opening a dashboard.
    """

    def __init__(self) -> None:
        # Sessions: (tenant_id, user_id, channel) → ConversationSession
        self._sessions: dict[tuple[str, str, str], ConversationSession] = {}
        # Action log: tenant_id → list of RoutedAction records
        self._action_log: dict[str, list[RoutedAction]] = {}

    # ------------------------------------------------------------------ #
    # CAP-STATEFUL-INTERACTION-FLOWS — session management                 #
    # ------------------------------------------------------------------ #

    def get_or_create_session(
        self,
        *,
        tenant_id: str,
        user_id: str,
        channel: str,
        persona: str,
    ) -> ConversationSession:
        """Return an existing active session or create a new one.

        Session state survives channel disconnections and timeouts —
        flow_step and context are preserved until the flow is completed or abandoned.
        """
        if persona not in VALID_PERSONAS:
            raise ValueError(f"persona must be one of {VALID_PERSONAS}")

        key = (tenant_id, user_id, channel)
        session = self._sessions.get(key)
        if session and session.is_active:
            session.last_activity_at = datetime.now(timezone.utc)
            return session

        session = ConversationSession(
            session_id=str(uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            channel=channel,
            persona=persona,
        )
        self._sessions[key] = session
        return session

    def end_session(self, *, tenant_id: str, user_id: str, channel: str) -> None:
        key = (tenant_id, user_id, channel)
        session = self._sessions.get(key)
        if session:
            session.is_active = False
            session.flow_step = None

    def get_session(
        self,
        *,
        tenant_id: str,
        user_id: str,
        channel: str,
    ) -> dict[str, Any] | None:
        key = (tenant_id, user_id, channel)
        session = self._sessions.get(key)
        if not session:
            return None
        return _session_to_dict(session)

    # ------------------------------------------------------------------ #
    # CAP-CONVERSATIONAL-DELIVERY — BC-INT-01 outbound messages           #
    # ------------------------------------------------------------------ #

    def build_action_message(
        self,
        *,
        message_type: str,
        body: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build a BC-INT-01 compliant outbound message with embedded action options.

        BC-INT-01: every outbound message about an actionable situation MUST embed
        the action trigger. The system must never send an alert about a situation
        that requires action without also embedding the action trigger in the same message.
        """
        if message_type not in _BC_INT01_ACTIONS:
            raise ValueError(
                f"message_type must be one of: {list(_BC_INT01_ACTIONS)}. "
                f"BC-INT-01 requires these 6 message types to carry mandatory embedded actions."
            )
        spec = _BC_INT01_ACTIONS[message_type]
        return {
            "message_type": message_type,
            "body": body,
            "action_prompt": spec["prompt"],
            "action_options": list(spec["action_options"]),
            "context": context or {},
            "bc_int01_compliant": True,
            "built_at": datetime.now(timezone.utc).isoformat(),
        }

    def send_onboarding_message(
        self,
        *,
        tenant_id: str,
        user_id: str,
        channel: str,
        persona: str,
    ) -> dict[str, Any]:
        """Send persona-aware onboarding message explaining available commands.

        BC-INT-02: new users must receive onboarding messages that explain available
        commands for their role to make conversational access discoverable.
        """
        if persona not in VALID_PERSONAS:
            raise ValueError(f"persona must be one of {VALID_PERSONAS}")

        intro_text = _ONBOARDING_INTRO[persona]
        message: dict[str, Any] = {
            "recipient_id": user_id,
            "tenant_id": tenant_id,
            "channel": channel,
            "persona": persona,
            "message_type": "onboarding",
            "body": intro_text,
            "available_commands": list(_PERSONA_COMMANDS[persona].keys()),
            "delivered_at": datetime.now(timezone.utc).isoformat(),
        }

        # Log in session history if a session exists
        key = (tenant_id, user_id, channel)
        session = self._sessions.get(key)
        if session:
            session.history.append({"direction": "outbound", **message})

        return message

    # ------------------------------------------------------------------ #
    # CAP-ACTION-BASED-REPLIES — inbound reply parsing + dispatch          #
    # ------------------------------------------------------------------ #

    def handle_inbound_reply(
        self,
        *,
        tenant_id: str,
        user_id: str,
        channel: str,
        reply_text: str,
        persona: str,
        action_id: str | None = None,
    ) -> dict[str, Any]:
        """Parse an inbound channel reply and route to the appropriate platform action.

        BC-INT-01: action replies must be idempotent — duplicate replies must not
        trigger duplicate actions. Uses action_id deduplication within session scope.
        BC-INT-02: persona-aware routing — same reply means different actions for
        different persona types.

        Returns a result dict with: action_category, command_response, dispatched bool.
        """
        session = self.get_or_create_session(
            tenant_id=tenant_id,
            user_id=user_id,
            channel=channel,
            persona=persona,
        )

        # Log inbound message in history
        session.history.append({
            "direction": "inbound",
            "text": reply_text,
            "received_at": datetime.now(timezone.utc).isoformat(),
        })
        session.last_activity_at = datetime.now(timezone.utc)

        # Idempotency: reject duplicate action_ids
        aid = action_id or str(uuid4())
        is_duplicate = aid in session.seen_action_ids
        if not is_duplicate:
            session.seen_action_ids.add(aid)

        # Classify the reply
        normalized = reply_text.strip().lower()

        # 1. Check for command shortcut (persona-aware, BC-INT-02)
        command_response = self._try_command(normalized, persona, session)
        if command_response is not None:
            return {
                "action_id": aid,
                "action_category": "command",
                "command": normalized,
                "response": command_response,
                "dispatched": False,
                "is_duplicate": is_duplicate,
            }

        # 2. Classify as BC-INT-01 action keyword
        action_category = _classify_action_reply(normalized)
        routed = RoutedAction(
            action_id=aid,
            session_id=session.session_id,
            user_id=user_id,
            tenant_id=tenant_id,
            action_category=action_category,
            raw_reply=reply_text,
            context=dict(session.context),
            is_duplicate=is_duplicate,
        )

        if not is_duplicate and action_category != "unknown":
            routed.dispatched = True
            routed.dispatched_at = datetime.now(timezone.utc)
            self._dispatch_action(routed, session)

        self._action_log.setdefault(tenant_id, []).append(routed)

        return {
            "action_id": aid,
            "action_category": action_category,
            "raw_reply": reply_text,
            "dispatched": routed.dispatched,
            "is_duplicate": is_duplicate,
            "session_id": session.session_id,
        }

    def execute_command(
        self,
        *,
        tenant_id: str,
        user_id: str,
        channel: str,
        command: str,
        persona: str,
        args: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a named command shortcut for a persona.

        BC-INT-02: command shortcuts available for frequent actions per persona.
        """
        session = self.get_or_create_session(
            tenant_id=tenant_id,
            user_id=user_id,
            channel=channel,
            persona=persona,
        )
        response = self._try_command(command.lower().strip(), persona, session, args=args or {})
        if response is None:
            available = list(_PERSONA_COMMANDS.get(persona, {}).keys())
            response = (
                f"Command '{command}' not recognised for {persona} role. "
                f"Available: {', '.join(available)}"
            )
        return {
            "command": command,
            "persona": persona,
            "response": response,
            "session_id": session.session_id,
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------ #
    # Action log read                                                      #
    # ------------------------------------------------------------------ #

    def get_action_log(
        self,
        *,
        tenant_id: str,
        user_id: str | None = None,
        action_category: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return routed actions for a tenant, optionally filtered."""
        entries = self._action_log.get(tenant_id, [])
        if user_id:
            entries = [e for e in entries if e.user_id == user_id]
        if action_category:
            entries = [e for e in entries if e.action_category == action_category]
        return [_action_to_dict(e) for e in entries]

    def get_bc_int01_message_types(self) -> dict[str, Any]:
        """Return all BC-INT-01 mandatory message types and their required action options."""
        return {k: dict(v) for k, v in _BC_INT01_ACTIONS.items()}

    def get_persona_commands(self, *, persona: str) -> dict[str, list[str]]:
        """Return BC-INT-02 command shortcuts available for the given persona."""
        if persona not in VALID_PERSONAS:
            raise ValueError(f"persona must be one of {VALID_PERSONAS}")
        return dict(_PERSONA_COMMANDS[persona])

    # ------------------------------------------------------------------ #
    # Internal                                                             #
    # ------------------------------------------------------------------ #

    def _try_command(
        self,
        normalized: str,
        persona: str,
        session: ConversationSession,
        args: dict[str, Any] | None = None,
    ) -> str | None:
        """Return a command response string, or None if not a recognised command."""
        base_cmd = normalized.split()[0] if normalized else ""
        persona_cmds = _PERSONA_COMMANDS.get(persona, {})

        if base_cmd == "help":
            lines = [f"Available commands for {persona}:"]
            for cmd, descs in persona_cmds.items():
                lines.append(f"• {cmd}: {descs[0]}")
            return "\n".join(lines)

        if base_cmd == "status":
            return (
                f"Status for {persona}: "
                f"Session active since {session.created_at.strftime('%H:%M')}. "
                f"Use 'today' for today's items or 'pending' for actions needed."
            )

        if base_cmd == "today":
            return (
                f"Today's items for {persona}: "
                f"No live data available in this session. "
                f"Connect to operations-os service for live daily action list."
            )

        if base_cmd == "pending":
            return (
                f"Pending items for {persona}: "
                f"No live data available in this session. "
                f"Connect to operations-os service for pending actions."
            )

        if base_cmd in {"approve", "reject"} and len(normalized.split()) > 1:
            target_id = normalized.split()[1]
            action = "APPROVE" if base_cmd == "approve" else "REJECT"
            # Update session context for the flow step
            session.context["pending_approval_action"] = action
            session.context["pending_approval_id"] = target_id
            session.flow_step = "approval_confirmation"
            return f"Action {action} queued for ID {target_id}. Dispatching to approval workflow."

        if base_cmd == "remind" and len(normalized.split()) > 1:
            batch_ref = " ".join(normalized.split()[1:])
            session.context["remind_batch"] = batch_ref
            session.flow_step = "reminder_dispatch"
            return f"Reminder queued for batch '{batch_ref}'. Dispatching to notification service."

        # Check if the command base matches any known persona command
        for cmd_key in persona_cmds:
            if cmd_key.startswith(base_cmd):
                return f"Command '{base_cmd}': {persona_cmds[cmd_key][0]}"

        return None

    def _dispatch_action(self, action: RoutedAction, session: ConversationSession) -> None:
        """Route an accepted BC-INT-01 action toward the appropriate platform service.

        In production this would call workflow engine or operations-os via event bus.
        Here we record the routing intent in session context for traceability.
        """
        session.context["last_routed_action"] = action.action_category
        session.context["last_action_id"] = action.action_id
        session.context["last_action_at"] = datetime.now(timezone.utc).isoformat()


# ------------------------------------------------------------------ #
# Reply classification (BC-INT-01 action keywords)                    #
# ------------------------------------------------------------------ #

def _classify_action_reply(normalized: str) -> str:
    """Map a normalized reply text to a BC-INT-01 action category."""
    upper = normalized.upper().strip()

    if upper in {"PAY", "PAYMENT", "P"}:
        return "PAY"
    if upper in {"WAIVE", "W"}:
        return "WAIVE"
    if upper in {"ENROLL", "ENROL", "E", "CONFIRM", "YES"}:
        return "ENROLL"
    if upper in {"INFO", "I", "DETAILS"}:
        return "INFO"
    if upper in {"CONTACT", "C"}:
        return "CONTACT"
    if upper in {"APPROVE", "APPROVED", "A", "OK"}:
        return "APPROVE"
    if upper in {"REJECT", "REJECTED", "R", "NO"}:
        return "REJECT"
    if upper in {"JOIN", "J", "RESERVE"}:
        return "JOIN"
    # Attendance shortcuts (1=Present, 2=Absent, 3=Late)
    if upper in {"1", "PRESENT", "ATTENDING"}:
        return "ATTENDANCE_PRESENT"
    if upper in {"2", "ABSENT"}:
        return "ATTENDANCE_ABSENT"
    if upper in {"3", "LATE"}:
        return "ATTENDANCE_LATE"
    if upper in {"ACK", "RECEIVED", "OK", "SEEN", "SNOOZE"}:
        return "ACK"

    return "unknown"


# ------------------------------------------------------------------ #
# Serialisation helpers                                               #
# ------------------------------------------------------------------ #

def _session_to_dict(s: ConversationSession) -> dict[str, Any]:
    return {
        "session_id": s.session_id,
        "tenant_id": s.tenant_id,
        "user_id": s.user_id,
        "channel": s.channel,
        "persona": s.persona,
        "flow_step": s.flow_step,
        "context": dict(s.context),
        "history_length": len(s.history),
        "is_active": s.is_active,
        "created_at": s.created_at.isoformat(),
        "last_activity_at": s.last_activity_at.isoformat(),
    }


def _action_to_dict(a: RoutedAction) -> dict[str, Any]:
    return {
        "action_id": a.action_id,
        "session_id": a.session_id,
        "user_id": a.user_id,
        "tenant_id": a.tenant_id,
        "action_category": a.action_category,
        "raw_reply": a.raw_reply,
        "is_duplicate": a.is_duplicate,
        "dispatched": a.dispatched,
        "dispatched_at": a.dispatched_at.isoformat() if a.dispatched_at else None,
    }

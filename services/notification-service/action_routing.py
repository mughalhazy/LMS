from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from integrations.communication import WhatsAppInteractiveReply

# BC-COMMS-01: channel-normalised action keyword vocabulary (same set regardless of channel)
_ACTION_KEYWORDS: dict[str, str] = {
    # attendance
    "1": "confirm_attendance", "present": "confirm_attendance",
    "2": "decline_attendance", "absent": "decline_attendance",
    # fees
    "pay": "initiate_payment", "payment": "initiate_payment",
    "waive": "waive_payment", "dispute": "waive_payment",
    # enrollment
    "enroll": "confirm_enrollment", "register": "confirm_enrollment",
    "info": "enrollment_info_request", "details": "enrollment_info_request",
    # at-risk
    "contact": "contact_learner", "message": "contact_learner",
    # approval
    "approve": "approve_request", "accept": "approve_request",
    "reject": "reject_request", "deny": "reject_request",
    # seat
    "join": "reserve_seat", "reserve": "reserve_seat",
    # ack
    "ack": "acknowledge_reminder", "ok": "acknowledge_reminder",
    "snooze": "snooze_reminder",
    # status / queries
    "status": "query_status", "today": "query_today",
    "pending": "query_pending", "help": "query_help",
}


@dataclass(frozen=True)
class RoutedAction:
    action_type: str
    status: str
    detail: dict[str, Any]


class WhatsAppActionRouter:
    """Maps parsed inbound WhatsApp replies to workflow-safe actions."""

    def route(self, reply: WhatsAppInteractiveReply) -> RoutedAction:
        op = reply.operation
        action = reply.action.lower().strip()

        if op == "attendance":
            if action in {"confirm", "present", "yes", "attend"}:
                return RoutedAction(
                    action_type="confirm_attendance",
                    status="accepted",
                    detail={"workflow_id": reply.workflow_id, "user_id": reply.user_id},
                )
            if action in {"decline", "absent", "no"}:
                return RoutedAction(
                    action_type="decline_attendance",
                    status="accepted",
                    detail={"workflow_id": reply.workflow_id, "user_id": reply.user_id},
                )

        if op == "reminder":
            if action in {"ack", "ok", "confirm", "received", "seen"}:
                return RoutedAction(
                    action_type="acknowledge_reminder",
                    status="accepted",
                    detail={"workflow_id": reply.workflow_id, "user_id": reply.user_id},
                )
            if action == "snooze":
                return RoutedAction(
                    action_type="snooze_reminder",
                    status="accepted",
                    detail={"workflow_id": reply.workflow_id, "user_id": reply.user_id},
                )

        if action in {"query", "help", "question"}:
            query = str(reply.payload.get("q") or reply.payload.get("raw_reply") or "").strip()
            return RoutedAction(
                action_type="basic_query_response",
                status="accepted",
                detail={
                    "workflow_id": reply.workflow_id,
                    "user_id": reply.user_id,
                    "response": self._basic_query_response(query=query),
                },
            )

        if op == "update" and action in {"ack", "ok", "confirm"}:
            return RoutedAction(
                action_type="acknowledge_update",
                status="accepted",
                detail={"workflow_id": reply.workflow_id, "user_id": reply.user_id},
            )

        # CGAP-021: BC-INT-01 — 5 missing action categories added below.

        # Fee payment: PAY / WAIVE
        if action in {"pay", "payment", "1"} and op == "reminder":
            return RoutedAction(
                action_type="initiate_payment",
                status="accepted",
                detail={"workflow_id": reply.workflow_id, "user_id": reply.user_id},
            )
        if action in {"waive", "waiver", "dispute"} and op == "reminder":
            return RoutedAction(
                action_type="waive_payment",
                status="accepted",
                detail={
                    "workflow_id": reply.workflow_id,
                    "user_id": reply.user_id,
                    "waiver_reason": str(reply.payload.get("raw_reply") or ""),
                },
            )

        # Enrollment confirmation: ENROLL / INFO
        if action in {"enroll", "yes", "confirm", "1"} and op == "attendance":
            # Disambiguate: attendance confirm already handled above; ENROLL is for enrollment op
            pass  # attendance handled by first block — fall through handled below
        if action in {"enroll", "join", "register"} and op not in {"attendance"}:
            return RoutedAction(
                action_type="confirm_enrollment",
                status="accepted",
                detail={"workflow_id": reply.workflow_id, "user_id": reply.user_id},
            )
        if action in {"info", "details", "more"}:
            return RoutedAction(
                action_type="enrollment_info_request",
                status="accepted",
                detail={"workflow_id": reply.workflow_id, "user_id": reply.user_id},
            )

        # At-risk learner contact: CONTACT
        if action in {"contact", "message", "reach"}:
            return RoutedAction(
                action_type="contact_learner",
                status="accepted",
                detail={"workflow_id": reply.workflow_id, "user_id": reply.user_id},
            )

        # Approval: APPROVE / REJECT
        if action in {"approve", "approved", "yes", "accept"}:
            return RoutedAction(
                action_type="approve_request",
                status="accepted",
                detail={"workflow_id": reply.workflow_id, "user_id": reply.user_id},
            )
        if action in {"reject", "rejected", "no", "deny", "decline"}:
            return RoutedAction(
                action_type="reject_request",
                status="accepted",
                detail={
                    "workflow_id": reply.workflow_id,
                    "user_id": reply.user_id,
                    "rejection_reason": str(reply.payload.get("raw_reply") or ""),
                },
            )

        # Seat reservation: JOIN
        if action in {"join", "reserve", "seat"}:
            return RoutedAction(
                action_type="reserve_seat",
                status="accepted",
                detail={"workflow_id": reply.workflow_id, "user_id": reply.user_id},
            )

        return RoutedAction(
            action_type="unsupported_action",
            status="ignored",
            detail={"workflow_id": reply.workflow_id, "user_id": reply.user_id},
        )

    def _basic_query_response(self, *, query: str) -> str:
        normalized = query.lower()
        if "schedule" in normalized or "time" in normalized:
            return "Please check the LMS schedule tab for your next session time."
        if "attendance" in normalized:
            return "Attendance is updated after each session confirmation."
        return "Thanks! A coordinator will follow up shortly."


class ChannelActionRouter:
    """BC-COMMS-01: channel-agnostic reply-to-action mapping.

    Any action available via WhatsApp must be available via SMS, email, and in-app.
    This router accepts a raw reply string from any channel and returns the same
    RoutedAction vocabulary as WhatsAppActionRouter — callers are channel-blind.
    """

    # Channels that support rich interactive replies (keyword matching sufficient)
    _KEYWORD_CHANNELS: frozenset[str] = frozenset({"whatsapp", "sms", "in_app", "push"})
    # Email fallback: replies may be prefixed tokens like "[PAY]" or "Action: PAY"
    _EMAIL_TOKEN_PREFIXES: tuple[str, ...] = ("action:", "[", "reply:")

    def route_reply(
        self,
        *,
        channel: str,
        reply_text: str,
        workflow_id: str,
        user_id: str,
        context: dict[str, Any] | None = None,
    ) -> RoutedAction:
        """Map a raw channel reply to a RoutedAction.

        Normalises channel-specific syntax (WhatsApp numbered replies, SMS keywords,
        email token prefixes) to the common action vocabulary. BC-COMMS-01 compliant.
        """
        ctx = context or {}
        normalised = self._normalise_reply(channel=channel, raw=reply_text)

        # Check for approve/reject with embedded action_id: "approve abc123"
        parts = normalised.split(None, 1)
        verb = parts[0] if parts else ""
        arg = parts[1].strip() if len(parts) > 1 else ""

        # Approval with explicit action_id
        if verb in {"approve", "accept"} and arg:
            return RoutedAction(
                action_type="approve_request",
                status="accepted",
                detail={"workflow_id": workflow_id, "user_id": user_id, "action_id": arg, "channel": channel},
            )
        if verb in {"reject", "deny"} and arg:
            return RoutedAction(
                action_type="reject_request",
                status="accepted",
                detail={"workflow_id": workflow_id, "user_id": user_id, "action_id": arg, "rejection_reason": arg, "channel": channel},
            )

        # Lookup full normalised text in keyword map
        action_type = _ACTION_KEYWORDS.get(normalised)
        if action_type:
            return RoutedAction(
                action_type=action_type,
                status="accepted",
                detail={"workflow_id": workflow_id, "user_id": user_id, "channel": channel, **ctx},
            )

        # Channels that cannot support interactive replies embed a deep-link fallback
        if channel == "email" and not action_type:
            return RoutedAction(
                action_type="email_fallback_link_required",
                status="accepted",
                detail={
                    "workflow_id": workflow_id,
                    "user_id": user_id,
                    "channel": channel,
                    "raw_reply": reply_text,
                    "fallback_url": ctx.get("action_url", ""),
                },
            )

        return RoutedAction(
            action_type="unsupported_action",
            status="ignored",
            detail={"workflow_id": workflow_id, "user_id": user_id, "channel": channel, "raw_reply": reply_text},
        )

    @staticmethod
    def _normalise_reply(*, channel: str, raw: str) -> str:
        """Strip channel-specific prefixes and normalise to lowercase keyword."""
        text = raw.strip().lower()
        if channel == "email":
            # Strip "[PAY]" → "pay", "Action: PAY" → "pay", "Reply: PAY" → "pay"
            for prefix in ChannelActionRouter._EMAIL_TOKEN_PREFIXES:
                if text.startswith(prefix):
                    text = text[len(prefix):].strip(" ]:")
                    break
        return text

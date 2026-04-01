from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from integrations.communication import WhatsAppInteractiveReply


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

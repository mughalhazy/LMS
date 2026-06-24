from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


# BC-INT-01: mandatory message types with embedded actions
MANDATORY_MESSAGE_TYPES = {
    "fee_overdue": ["PAY", "WAIVE"],
    "attendance_alert": ["1:Present", "2:Absent", "3:Late"],
    "enrollment_invitation": ["ENROLL", "INFO"],
    "at_risk_learner": ["CONTACT"],
    "pending_approval": ["APPROVE", "REJECT"],
    "new_batch_open": ["JOIN"],
}

# BC-INT-02: persona command shortcuts
PERSONA_COMMANDS = {
    "learner": ["status", "progress", "enroll", "quiz", "help"],
    "operator": ["status", "today", "pending", "remind", "fees"],
    "manager": ["team", "assign", "alerts", "approve", "reports"],
    "instructor": ["roster", "attendance", "message", "today", "grades"],
}


@dataclass
class ConversationSession:
    session_id: str
    user_id: str
    tenant_id: str
    persona: str                # learner | operator | manager | instructor
    flow_step: str = "idle"
    context: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class OutboundMessage:
    message_id: str
    user_id: str
    tenant_id: str
    message_type: str
    content: str
    action_options: List[Dict[str, str]]  # [{"key": "PAY", "label": "Initiate payment"}]
    channel: str = "whatsapp"
    created_at: datetime = field(default_factory=datetime.utcnow)

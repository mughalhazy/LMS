from __future__ import annotations

from .base_adapter import CommunicationAdapter, CommunicationUser


class SMSAdapter(CommunicationAdapter):
    provider_key = "sms"

    def __init__(self, disabled_recipients: set[str] | None = None) -> None:
        self.disabled_recipients = disabled_recipients or set()

    def send_message(self, user: CommunicationUser, message: str) -> bool:
        if not user.user_id:
            return False
        if user.user_id in self.disabled_recipients:
            return False
        return len(message.strip()) > 0

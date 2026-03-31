from __future__ import annotations

from .base_adapter import CommunicationAdapter, CommunicationUser


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

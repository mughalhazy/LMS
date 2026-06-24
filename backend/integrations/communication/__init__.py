"""Communication adapter package — channel-agnostic transport adapters.

B05-005: communication-adapter-contract.md — WhatsAppAdapter + SmsAdapter +
CommunicationAdapterRegistry as required by BC-COMMS-01 / MS-ADAPTER-01.
"""
from .base import AdapterResult, CommunicationAdapter, CommunicationAdapterRegistry, DeliveryState
from .sms_adapter import SmsAdapter
from .whatsapp_adapter import WhatsAppAdapter

__all__ = [
    "AdapterResult",
    "CommunicationAdapter",
    "CommunicationAdapterRegistry",
    "DeliveryState",
    "SmsAdapter",
    "WhatsAppAdapter",
]

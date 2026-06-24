# Communication Adapters

Channel-agnostic communication adapter package implementing `docs/contracts/communication-adapter-contract.md` (BC-COMMS-01 / MS-ADAPTER-01).

Created 2026-05-31 (B05-005).

## Purpose

Provides a single `CommunicationAdapter` interface that all channel implementations must satisfy. Callers pass a `channel` string; the `CommunicationAdapterRegistry` resolves the concrete adapter. No service outside this package may contain channel-specific dispatch logic or provider SDK imports.

## Adapters

| Adapter | Channel | File | Status |
|---|---|---|---|
| `WhatsAppAdapter` | `"whatsapp"` | `whatsapp_adapter.py` | Stub — logs calls; provider SDK injection pending |
| `SmsAdapter` | `"sms"` | `sms_adapter.py` | Stub — logs calls; provider SDK injection pending |

## Interface (`base.py`)

- `CommunicationAdapter` — ABC with `send_message()`, `schedule_message()`, `broadcast()`
- `CommunicationAdapterRegistry` — `register(adapter)`, `resolve(channel)`, `list()`
- `AdapterResult` — `operation_id`, `channel`, `state`, `accepted_at`, `provider_ref`, `error_code`, `error_message`
- `DeliveryState` — `accepted | scheduled | queued | sent | delivered | failed | cancelled`

## Usage

```python
from backend.integrations.communication import CommunicationAdapterRegistry, WhatsAppAdapter, SmsAdapter

registry = CommunicationAdapterRegistry()
registry.register(WhatsAppAdapter())
registry.register(SmsAdapter())

adapter = registry.resolve("whatsapp")
result = adapter.send_message(
    channel="whatsapp",
    recipient_id="user_123",
    recipient_address="+923001234567",
    body="Your course starts in 30 minutes.",
    tenant_id="tenant_abc",
)
```

## Extension

Add new channels by implementing `CommunicationAdapter` and calling `registry.register(NewAdapter())`. Callers never need to change — they always call `registry.resolve(channel)`.

## Design reference

`docs/contracts/communication-adapter-contract.md`

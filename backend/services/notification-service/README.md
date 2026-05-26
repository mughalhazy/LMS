# Notification Service

Provides tenant-scoped notification orchestration for LMS workflows.

## Capabilities

- Event-based notification generation
- Notification preference management
- Delivery queue processing
- Multi-channel notification dispatch

## Events Consumed
- course_completed
- enrollment_created
- certificate_issued
- assessment_passed

## Delivery Channels
- email
- push notifications
- in-app notifications
- WhatsApp
- SMS

> **Note:** WhatsApp is a first-class delivery surface per the platform behavioral spec. The WhatsApp adapter exists at `integrations/communication/whatsapp_adapter.py`. SMS is supported as a secondary channel. Both channels require wiring into the notification dispatch pipeline.

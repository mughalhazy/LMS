# Push Service — Spec

**Service:** `push-service` | **Gateway:** `/api/v1/push` | **Port:** varies

## Purpose

Manages push notification subscriptions and notification delivery for mobile (FCM device token) and web (Web Push API) channels. Queue-based delivery with drain API.

## Responsibilities

- Push subscription management per user per channel
- Notification creation and per-subscription queuing
- Queue drain (simulated provider dispatch)
- Subscription enable/disable without deletion

## Out of scope

- Email delivery (owned by `email-service`)
- In-app notification rendering (owned by `notification-service`)
- Actual FCM/APNs/Web Push SDK calls (provider wiring is external to this service)

## Data model

| Entity | Fields |
|---|---|
| `PushSubscription` | subscription_id, tenant_id, user_id, channel, endpoint, auth_key, p256dh_key, device_token, platform, enabled, created_at, updated_at |
| `PushNotification` | notification_id, tenant_id, user_id, title, body, data{}, channels[], created_at |
| `QueueMessage` | queue_message_id, notification_id, subscription_id, tenant_id, channel, endpoint, payload{}, status, attempts, last_error, created_at, updated_at |

## Channels

`mobile` | `web`

- `mobile`: requires `device_token`
- `web`: requires `auth_key` + `p256dh_key`

## API

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/push/subscriptions` | Register push subscription |
| GET | `/api/v1/push/subscriptions` | List subscriptions for user |
| PATCH | `/api/v1/push/subscriptions/{subscriptionId}` | Enable or disable subscription |
| POST | `/api/v1/push/send` | Send notification (queues per active subscription) |
| POST | `/api/v1/push/queue/drain` | Process queued messages (max_messages param) |

## Behavioral rules

- Send returns 202 with `queued: 0` if user has no active subscriptions for requested channels
- Channels default to `["mobile", "web"]` if not specified in send request
- One QueueMessage created per active matching subscription
- Queue drain marks delivered unless endpoint contains "invalid" (simulated failure)
- Disabled subscriptions are skipped at send time — not deleted

## Delivery status

`queued → delivered | failed`

# Push Service

Push Service delivers LMS notifications to **mobile** and **web** channels using subscription-aware queueing.

## Capabilities

- Mobile push notifications (device token based)
- Web push notifications (endpoint + VAPID keys)
- Notification subscriptions per tenant/user
- Push delivery queue with drain worker behavior

## API Endpoints

- `POST /api/v1/push/subscriptions`
- `GET /api/v1/push/subscriptions?tenant_id={tenant_id}&user_id={user_id}`
- `PATCH /api/v1/push/subscriptions/{subscription_id}`
- `POST /api/v1/push/notifications`
- `POST /api/v1/push/queue/drain`

## Run

```bash
python -m app.main
```

## Test

```bash
PYTHONPATH=. pytest -q
```

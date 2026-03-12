# Email Delivery Service

FastAPI-based service implementing:
- transactional email delivery
- email templates
- notification email triggers
- email queue processing

## Supported templates
- `welcome_email`
- `password_reset`
- `course_enrollment`
- `deadline_reminder`

## Integrations
- SMTP
- SendGrid
- AWS SES

## Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8090
```

## Test

```bash
pytest
```

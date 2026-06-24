# EXTERNAL DEPENDENCY REGISTER — PROJECT MEMORY LAYER

Status: Active
Date: 2026-06-24
Phase: Project Memory Layer (post Phase 3.25)
Owner: Human

---

## Purpose

Contains every item requiring external provisioning, vendor accounts, credentials, or registrations that cannot be automated by the development team. These items are NOT software gaps — they are onboarding, provisioning, and compliance tasks. They do not block engineering unless the feature they enable is on the critical path to launch.

Classification rule: EXTERNAL-DEPENDENCY only if the item requires credentials, onboarding, registration, vendor approval, or external ownership that cannot be derived from the repository.

---

## PM-ED-001: JazzCash Merchant Account and API Credentials

| Field | Value |
|---|---|
| **Item ID** | PM-ED-001 |
| **Original ID** | ED-001 |
| **Title** | JazzCash merchant account + production API credentials |
| **Classification** | EXTERNAL-DEPENDENCY |
| **Current Status** | PENDING — development uses test/sandbox mode presumed |
| **Original Source** | integrations/payments/reconciliation.py; PRODUCT_WORKFLOWS.md WF-005 |
| **Evidence Source** | integrations/payments/ directory exists with JazzCash integration code. .pyc files indicate active development/compilation. reconciliation.py tests payments. |
| **Resolution Source** | Requires JazzCash merchant onboarding |
| **Resolution Date** | PENDING |
| **Resolved By** | Human (business owner — merchant account registration) |
| **Decision Summary** | Register as a JazzCash merchant to receive production API credentials. Configure JAZZCASH_MERCHANT_ID, JAZZCASH_PASSWORD, JAZZCASH_INTEGRITY_SALT in checkout-service/payment-service environment. |
| **Detailed Explanation** | JazzCash is Pakistan's primary mobile payment network operated by Jazz (Mobilink). Merchant accounts require registration with JazzCash and approval of the business. Sandbox/test credentials are available for development. Production credentials require a merchant agreement. The integration code exists and is complete; only the credentials are missing. |
| **Affected Components** | integrations/payments/, checkout-service, payment-service |
| **Affected Routes** | /api/v1/checkout/sessions/{id}/initiate-payment; JazzCash webhook receiver |
| **Affected APIs** | JazzCash payment initiation and callback APIs |
| **Affected Workflows** | WF-005 (JazzCash checkout) |
| **Affected Roles** | Learner (payment), Admin (reconciliation) |
| **Owner Required** | YES — merchant onboarding requires business owner |
| **External Dependency** | YES — JazzCash partner relationship |
| **Future Impact** | CRITICAL — production payments require this; dev continues with test credentials |
| **Reopen Criteria** | N/A — resolved when credentials are provisioned |
| **Steps to Resolve** | 1. Register at jazzcash.com.pk merchant portal 2. Complete merchant KYC and agreement 3. Receive MERCHANT_ID, PASSWORD, INTEGRITY_SALT 4. Set as env vars in production deployment |
| **Related Documents** | integrations/payments/reconciliation.py; docs/00_authority/PRODUCT_WORKFLOWS.md WF-005 |
| **Related Register Entries** | PM-ED-002 (EasyPaisa); PM-AC-042 (JazzCash reconciliation confirmed) |

---

## PM-ED-002: EasyPaisa Merchant Account and API Credentials

| Field | Value |
|---|---|
| **Item ID** | PM-ED-002 |
| **Original ID** | ED-002 |
| **Title** | EasyPaisa merchant account + production API credentials |
| **Classification** | EXTERNAL-DEPENDENCY |
| **Current Status** | PENDING |
| **Original Source** | integrations/payments/ (EasyPaisa alongside JazzCash) |
| **Evidence Source** | integrations/payments/ directory — EasyPaisa referenced alongside JazzCash in payment integration layer |
| **Resolution Date** | PENDING |
| **Resolved By** | Human (business owner) |
| **Decision Summary** | Register as EasyPaisa merchant (Telenor/Mobilink joint venture). Obtain production credentials. Configure in checkout-service environment. |
| **Detailed Explanation** | EasyPaisa is Pakistan's second major mobile payment network (operated via Telenor). Merchant onboarding is similar to JazzCash. Both payment methods are standard for Pakistan-first SaaS. Running without EasyPaisa reduces payment coverage to ~50% of Pakistan mobile wallet users. |
| **Affected Components** | integrations/payments/, checkout-service, payment-service |
| **Affected Routes** | Payment initiation + EasyPaisa callback |
| **Affected APIs** | EasyPaisa payment APIs |
| **Affected Workflows** | WF-005 (checkout) |
| **Affected Roles** | Learner (payment) |
| **Owner Required** | YES |
| **External Dependency** | YES |
| **Future Impact** | HIGH — payment coverage |
| **Reopen Criteria** | N/A |
| **Related Register Entries** | PM-ED-001 (JazzCash) |

---

## PM-ED-003: SMTP Email Service Provider Credentials

| Field | Value |
|---|---|
| **Item ID** | PM-ED-003 |
| **Original ID** | ED-003 |
| **Title** | SMTP / email delivery service credentials for notification-service |
| **Classification** | EXTERNAL-DEPENDENCY |
| **Current Status** | PENDING — development uses no-op or console logging |
| **Original Source** | notification-service (email delivery); WF-001 (welcome email); WF-005 (payment receipt) |
| **Evidence Source** | notification-service handles WorkflowAction email delivery; domain entities: Notification, NotificationTemplate |
| **Resolution Date** | PENDING |
| **Resolved By** | Human (choose provider; provision credentials) |
| **Decision Summary** | Choose email delivery provider (AWS SES, SendGrid, Postmark, or SMTP relay). Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS (or provider SDK key) in notification-service environment. |
| **Detailed Explanation** | notification-service sends transactional emails: welcome on tenant onboarding, payment receipts, enrollment confirmations, certificate issue notifications. In development, emails are likely logged or silently dropped (no credentials set). In production, a real delivery service is required. Pakistan SaaS: AWS SES is cost-effective and has Pakistan region support; SendGrid is a common alternative. |
| **Affected Components** | notification-service (backend/services/notification-service/) |
| **Affected Routes** | Notifications are outbound — no frontend route |
| **Affected APIs** | Internal — triggered by workflow events |
| **Affected Workflows** | WF-001 (onboarding welcome email), WF-003 (enrollment confirmation), WF-004 (certificate email), WF-005 (payment receipt), WF-009 (notification workflows) |
| **Affected Roles** | All roles (email recipients) |
| **Owner Required** | YES — provider selection and account creation |
| **External Dependency** | YES — email provider account + domain verification |
| **Future Impact** | HIGH — all transactional emails fail silently without this |
| **Reopen Criteria** | N/A |
| **Steps to Resolve** | 1. Choose provider (AWS SES recommended for Pakistan cost efficiency) 2. Verify sending domain (requires DNS TXT record — see PM-ED-004) 3. Obtain API key or SMTP credentials 4. Set credentials in notification-service environment |
| **Related Register Entries** | PM-ED-004 (domain — required for email verification) |

---

## PM-ED-004: Domain Name and DNS Configuration

| Field | Value |
|---|---|
| **Item ID** | PM-ED-004 |
| **Original ID** | ED-004 |
| **Title** | Domain name registration + DNS configuration for production |
| **Classification** | EXTERNAL-DEPENDENCY |
| **Current Status** | PENDING — localhost/dev only |
| **Original Source** | Production deployment requirement |
| **Evidence Source** | No domain found in any config file. infrastructure/deployment/ uses localhost references. |
| **Resolution Date** | PENDING |
| **Resolved By** | Human (owner — domain purchase) |
| **Decision Summary** | Register production domain (e.g., lms.example.com or branded SaaS domain). Configure DNS: A record to cloud server IP, CNAME for subdomains, TXT records for email verification. |
| **Detailed Explanation** | A production LMS requires a stable domain. Pakistan-first SaaS: consider .pk domain (registry: PKNIC) or international .com. The domain affects: SSL certificate issuance, email deliverability (SPF/DKIM/DMARC), multi-tenant subdomain strategy (tenant-slug.lms.domain for tenant isolation). The multi-tenant architecture supports subdomain routing — domain choice should account for wildcard SSL (*.lms.domain) if subdomains are used. |
| **Affected Components** | All HTTP-accessible services; notification-service (email domain); auth-service (CORS/redirect) |
| **Affected Routes** | All public routes |
| **Affected APIs** | All APIs |
| **Affected Workflows** | All workflows (domain needed for email links in notifications) |
| **Affected Roles** | All roles |
| **Owner Required** | YES |
| **External Dependency** | YES — domain registrar (Namecheap, GoDaddy, AWS Route 53, PKNIC) |
| **Future Impact** | CRITICAL — no production access without a domain |
| **Reopen Criteria** | N/A |
| **Related Register Entries** | PM-ED-003 (email — needs domain for SPF/DKIM); PM-ED-005 (SSL — needs domain) |

---

## PM-ED-005: SSL/TLS Certificate Provisioning

| Field | Value |
|---|---|
| **Item ID** | PM-ED-005 |
| **Original ID** | ED-005 |
| **Title** | SSL/TLS certificate for HTTPS in production |
| **Classification** | EXTERNAL-DEPENDENCY |
| **Current Status** | PENDING — dev uses HTTP only |
| **Original Source** | Production deployment requirement |
| **Evidence Source** | Docker Compose config uses HTTP. No SSL config found in infrastructure/. |
| **Resolution Date** | PENDING |
| **Resolved By** | Human (setup during deployment) |
| **Decision Summary** | Provision SSL via Let's Encrypt (free, auto-renewing) via Certbot + nginx, or cloud provider's managed certificate (AWS ACM, GCP Certificate Manager). Configure reverse proxy (nginx) to handle TLS termination. |
| **Detailed Explanation** | All production traffic must be HTTPS. JWT tokens and session data transmitted over HTTP are exposed. Let's Encrypt is the standard free option; wildcard cert (*.lms.domain) requires DNS-01 challenge. Cloud-managed certs are simpler but cloud-specific. TLS termination at nginx layer; backend services communicate over internal HTTP. |
| **Affected Components** | nginx/reverse proxy; all backend services (indirectly) |
| **Affected Routes** | All public routes |
| **Affected APIs** | All APIs |
| **Affected Workflows** | All |
| **Affected Roles** | All |
| **Owner Required** | YES (domain required first) |
| **External Dependency** | YES — Let's Encrypt CA or cloud provider |
| **Future Impact** | CRITICAL — no secure production without HTTPS |
| **Reopen Criteria** | At cert renewal (Let's Encrypt: 90 days) |
| **Related Register Entries** | PM-ED-004 (domain — required first) |

---

## PM-ED-006: Cloud Provider Account

| Field | Value |
|---|---|
| **Item ID** | PM-ED-006 |
| **Original ID** | ED-006 |
| **Title** | Cloud provider account selection and setup |
| **Classification** | EXTERNAL-DEPENDENCY |
| **Current Status** | PENDING — Docker Compose for dev; cloud deferred (PM-SD-002) |
| **Original Source** | SAFE-DEFAULT PM-SD-002 (cloud deployment target) |
| **Evidence Source** | No cloud SDK, no cloud IAM config in repository |
| **Resolution Date** | PENDING (non-blocking — deferred to production launch sprint) |
| **Resolved By** | Human (owner decides provider) |
| **Decision Summary** | Owner selects cloud provider when production deployment is scheduled. Recommended for Pakistan: AWS (ap-southeast-1 Singapore, lowest latency to Pakistan) or DigitalOcean (cost-effective for startups). |
| **Detailed Explanation** | Current default: Docker Compose + GitHub Actions (PM-SD-002). Cloud provider account is needed when production deployment begins. All code is cloud-agnostic (Docker images, standard ports). Provider selection affects: datacenter latency to Pakistan users, compliance (data residency), cost, managed services availability (Kafka, PostgreSQL, Redis). |
| **Affected Components** | infrastructure/deployment/, infrastructure/ci-cd/ |
| **Affected Routes** | All (production only) |
| **Affected APIs** | All |
| **Affected Workflows** | Deployment workflows |
| **Affected Roles** | DevOps (owner) |
| **Owner Required** | YES — cloud account creation requires business owner |
| **External Dependency** | YES — cloud provider relationship |
| **Future Impact** | HIGH — required for production; non-blocking for development |
| **Reopen Criteria** | Production launch is scheduled |
| **Related Register Entries** | PM-SD-002 (cloud deployment default) |

---

## PM-ED-007: FBR E-Commerce Tax Registration

| Field | Value |
|---|---|
| **Item ID** | PM-ED-007 |
| **Original ID** | ED-007 |
| **Title** | FBR (Federal Board of Revenue) e-commerce registration — Pakistan tax compliance |
| **Classification** | EXTERNAL-DEPENDENCY |
| **Current Status** | PENDING — regulatory requirement for revenue-generating SaaS in Pakistan |
| **Original Source** | Pakistan SaaS compliance requirement (country_code = PK in tenant model) |
| **Evidence Source** | tenant model includes country_code field; services/commerce/ handles payment flows; PRODUCT_WORKFLOWS WF-005 processes payments |
| **Resolution Date** | PENDING |
| **Resolved By** | Human (business owner — legal and tax compliance) |
| **Decision Summary** | Register with FBR IRIS system as an e-commerce business. Implement tax registration number (NTN/STRN) in invoices. Configure applicable tax rates in commerce services. |
| **Detailed Explanation** | Pakistan's FBR requires e-commerce businesses to register and collect Sales Tax on Services (STS) or General Sales Tax (GST) depending on province and service type. Educational software SaaS may have specific tax treatment. Legal counsel recommended for final determination. Integration: invoice-billing-service should include NTN/STRN in generated invoices. |
| **Affected Components** | services/commerce/, invoice-billing-service |
| **Affected Routes** | Invoice generation, payment receipts |
| **Affected APIs** | Invoice APIs |
| **Affected Workflows** | WF-005 (checkout/payment) |
| **Affected Roles** | Admin (accounting), Learner (invoice recipient) |
| **Owner Required** | YES — requires legal entity and business owner |
| **External Dependency** | YES — FBR IRIS system registration |
| **Future Impact** | HIGH — regulatory risk if revenue is collected without registration; required before public launch |
| **Reopen Criteria** | Annual tax filing and renewal |
| **Related Register Entries** | PM-ED-001 (JazzCash — payment flows where tax applies) |

---

## PM-ED-008: SMS Gateway Credentials

| Field | Value |
|---|---|
| **Item ID** | PM-ED-008 |
| **Original ID** | ED-008 |
| **Title** | SMS gateway credentials for OTP and SMS notifications |
| **Classification** | EXTERNAL-DEPENDENCY |
| **Current Status** | PENDING — email fallback available; SMS enhances delivery |
| **Original Source** | notification-service (multi-channel delivery); Pakistan-first: SMS is primary communication channel |
| **Evidence Source** | notification-service handles multiple notification channels; Pakistan context — SMS reach is higher than email for non-corporate learners |
| **Resolution Date** | PENDING |
| **Resolved By** | Human (choose SMS provider; provision account) |
| **Decision Summary** | Integrate SMS gateway for Pakistan. Options: Telenor Bulk SMS, Jazz SMS API, or Pakistan-specific providers (Wavetec, Inbox.pk). Set SMS_API_KEY in notification-service environment. |
| **Detailed Explanation** | Pakistan-first LMS: many learners and teachers in Tier 2/3 cities use mobile phones primarily for SMS rather than email. SMS delivery for enrollment confirmation, OTP (if added), and batch reminders improves engagement. This is not a hard blocker (email-only works for initial launch) but is important for the target market. |
| **Affected Components** | notification-service |
| **Affected Routes** | Internal — triggered by workflow events |
| **Affected APIs** | SMS provider API |
| **Affected Workflows** | WF-001 (onboarding SMS), WF-003 (enrollment confirmation SMS), WF-009 (notification) |
| **Affected Roles** | All roles with phone numbers |
| **Owner Required** | YES |
| **External Dependency** | YES — SMS provider commercial agreement |
| **Future Impact** | MEDIUM — email fallback covers launch; SMS adds reach in target market |
| **Reopen Criteria** | Never (one-time setup) |
| **Related Register Entries** | PM-ED-003 (SMTP email) |

---

## Dependency Status Summary

| PM ID | Dependency | Blocks Production? | Priority |
|---|---|---|---|
| PM-ED-001 | JazzCash credentials | YES (payment) | P1 — before go-live |
| PM-ED-002 | EasyPaisa credentials | YES (payment coverage) | P1 — before go-live |
| PM-ED-003 | SMTP email | YES (transactional email) | P1 — before go-live |
| PM-ED-004 | Domain + DNS | YES (public access) | P0 — before any production test |
| PM-ED-005 | SSL/TLS certificate | YES (HTTPS) | P0 — before any production test |
| PM-ED-006 | Cloud provider account | YES (deployment) | P1 — when production sprint begins |
| PM-ED-007 | FBR tax registration | Regulatory | P2 — before revenue generation |
| PM-ED-008 | SMS gateway | PARTIAL (email fallback) | P3 — post-launch enhancement |

**None of PM-ED items block frontend development, backend development, or staging testing.**

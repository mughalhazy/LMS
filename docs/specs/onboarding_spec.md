# Onboarding Spec

**Type:** Specification | **Date:** 2026-04-04 | **MS§:** §5.17 | **Service:** `services/onboarding/`

---

## Capability Domain: §5.17 Onboarding Capabilities

Covers: instant setup | automated configuration | guided flows

---

## Scope

Onboarding capabilities define how a new tenant is set up on the platform — from account creation through capability activation to first operational use. Per Master Spec §8 UX principle: "minimal setup, automation-first."

---

## Capabilities Defined

### CAP-INSTANT-SETUP
- A new tenant can be operational within minutes of account creation
- Automated steps: tenant record creation, baseline config bootstrapping, default capability bundle activation (per segment_type + plan_type), admin user provisioning
- Owner: `services/onboarding/`
- Model: `shared/models/onboarding.py`

### CAP-AUTOMATED-CONFIGURATION
- Config service is pre-populated with defaults matching the tenant's use-case profile (segment_type)
- Entitlement service is seeded with the tenant's plan_type capability bundle
- Notification service is configured with default templates
- No manual config setup required for baseline operation
- Integrates with: `services/config-service/`, `services/entitlement-service/`, `services/notification-service/`

### CAP-GUIDED-FLOWS
- Step-by-step onboarding wizard for non-technical operators
- Covers: branding setup, first course creation, first batch setup, first learner invite
- Progress tracked in onboarding service — wizard state is resumable
- Owner: `services/onboarding/`

---

## Onboarding Sequence

```
1. Account creation → tenant record created (tenant-service)
2. Profile detection → segment_type + plan_type determined from signup
3. Config bootstrap → config service seeded with profile defaults (B2P01)
4. Capability activation → entitlement service seeded with plan bundle (B2P02)
5. Admin provisioned → first admin user created (auth-service)
6. Guided flow started → onboarding wizard launched (onboarding-service)
7. First capability activated → tenant is operational
```

---

## Service Files

- `services/onboarding/service.py` — onboarding orchestration
- `services/onboarding/models.py` — onboarding state models
- `shared/models/onboarding.py` — shared onboarding models
- `services/onboarding/test_onboarding_service.py` — test coverage

---

## References

- Master Spec §5.17, §8 (minimal setup, automation-first)
- `docs/architecture/B2P06_tenant_extension_model.md`
- `docs/architecture/B2P01_config_service_design.md`
- `docs/architecture/B2P02_entitlement_service_design.md`

---

## Behavioral Contract (BOS Overlay — 2026-04-04)

### BC-ONBOARD-01 — Smart Defaults for the Full Customisation Surface (BOS§12.2 / GAP-010)

**Rule:** Every configurable option across the entire platform customisation surface MUST have a pre-filled sensible default so that a new tenant can operate without ANY manual configuration.

**Specification:**
The current spec covers CAP-AUTOMATED-CONFIGURATION for the capability bundle (step 3–4 in the onboarding sequence). This contract extends the smart defaults requirement to the FULL customisation surface defined in `docs/architecture/tenant_customization.md`:

| Customisation Area | Smart Default Source | Default Behaviour |
|---|---|---|
| Branding (logo, colours) | Platform default theme | Platform brand until tenant uploads their own |
| Language / locale | Tenant signup `country_code` | Locale inferred from country; switchable |
| Feature flags | Segment_type + plan_type bundle | All defaults from capability registry |
| Notification templates | Platform default templates | Pre-written for all standard triggers |
| Automation workflows | Platform default workflow bundle | All default-on (see BC-WF-01) |
| Fee reminders schedule | Default: 7-day overdue trigger | Active without manual setup |
| Attendance rules | Default: 3 consecutive absences = alert | Active without manual setup |
| Compliance settings | Segment_type defaults from config | Region/segment-appropriate defaults |
| Report schedule | Default: weekly summary on Monday 08:00 | Active without manual setup |

**Requirements:**
- For every customisable option, the config service MUST return a non-null default value — empty/null values for tenant config are not acceptable at tenant launch.
- Defaults must be derivable from `segment_type + plan_type + country_code` alone — no other input is required from the tenant admin to achieve a fully operational default state.
- Defaults must be presented to the tenant admin as their starting configuration with clear "customise" options — not as blank forms to be filled in.
- The onboarding wizard (CAP-GUIDED-FLOWS) must confirm each default to the admin and offer a single-click customisation path, not require active input to proceed.

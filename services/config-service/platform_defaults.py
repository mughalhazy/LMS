from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from shared.models.config import ConfigLevel, ConfigOverride, ConfigScope

# MS-CONFIG-01 (MS§3.2): platform-level country and segment defaults.
# Services must NOT branch on raw country_code/segment_id in business logic.
# All behavioral variation flows from config resolution output — these tables
# seed the COUNTRY and SEGMENT config layers so that resolution returns
# meaningful values for every supported locale and segment key.

_COUNTRY_LOCALE_DEFAULTS: dict[str, dict[str, object]] = {
    "PK": {"currency": "PKR", "whatsapp_primary": True,  "gdpr_consent_required": False},
    "US": {"currency": "USD", "whatsapp_primary": False, "gdpr_consent_required": False},
    "GB": {"currency": "GBP", "whatsapp_primary": False, "gdpr_consent_required": True},
    "IN": {"currency": "INR", "whatsapp_primary": True,  "gdpr_consent_required": False},
    "AE": {"currency": "AED", "whatsapp_primary": True,  "gdpr_consent_required": False},
    "SA": {"currency": "SAR", "whatsapp_primary": True,  "gdpr_consent_required": False},
    "NG": {"currency": "NGN", "whatsapp_primary": True,  "gdpr_consent_required": False},
    "KE": {"currency": "KES", "whatsapp_primary": True,  "gdpr_consent_required": False},
    "EG": {"currency": "EGP", "whatsapp_primary": True,  "gdpr_consent_required": False},
    "BD": {"currency": "BDT", "whatsapp_primary": True,  "gdpr_consent_required": False},
    "ID": {"currency": "IDR", "whatsapp_primary": True,  "gdpr_consent_required": False},
    "MY": {"currency": "MYR", "whatsapp_primary": True,  "gdpr_consent_required": False},
    "DE": {"currency": "EUR", "whatsapp_primary": False, "gdpr_consent_required": True},
    "FR": {"currency": "EUR", "whatsapp_primary": False, "gdpr_consent_required": True},
    "NL": {"currency": "EUR", "whatsapp_primary": False, "gdpr_consent_required": True},
    "SE": {"currency": "SEK", "whatsapp_primary": False, "gdpr_consent_required": True},
    "IE": {"currency": "EUR", "whatsapp_primary": False, "gdpr_consent_required": True},
}

_SEGMENT_COMPLIANCE_DEFAULTS: dict[str, dict[str, object]] = {
    "enterprise": {"mandatory_training_enabled": True},
    "university":  {"mandatory_training_enabled": True},
    "academy":     {"mandatory_training_enabled": False},
    "school":      {"mandatory_training_enabled": False},
    "default":     {"mandatory_training_enabled": False},
}

_SEGMENT_CAPABILITY_DEFAULTS: dict[str, dict[str, bool]] = {
    "academy": {
        "attendance_tracking": True,
        "fees_management": True,
        "fee_tracking": True,
        "notifications": True,
        "whatsapp_primary_interface": True,
        "cohort_management": True,
        "teacher_assignment": True,
        "timetable_scheduling": True,
        "parent_notifications": True,
        "student_lifecycle_management": True,
        "operations_dashboard": True,
    },
    "school": {
        "attendance_tracking": True,
        "fees_management": True,
        "fee_tracking": True,
        "notifications": True,
        "cohort_management": True,
        "parent_notifications": True,
        "timetable_scheduling": True,
        "teacher_assignment": True,
        "student_lifecycle_management": True,
        "operations_dashboard": True,
    },
    "enterprise": {
        "notifications": True,
        "cohort_management": True,
        "course_write": True,
        "learning_analytics": True,
        "compliance_reporting": True,
        "operations_dashboard": True,
        "teacher_assignment": True,
    },
    "university": {
        "notifications": True,
        "cohort_management": True,
        "course_write": True,
        "learning_analytics": True,
        "compliance_reporting": True,
        "operations_dashboard": True,
        "teacher_assignment": True,
        "student_lifecycle_management": True,
    },
    # MO-037 / Phase E: vocational segment capability defaults.
    # Activates the 6 capabilities defined in vocational_training_domain_spec.md.
    # Triggered when segment_type = "vocational" is passed at onboarding.
    "vocational": {
        "notifications": True,
        "attendance_tracking": True,
        "fees_management": True,
        "fee_tracking": True,
        "whatsapp_primary_interface": True,
        "cohort_management": True,
        "teacher_assignment": True,
        "student_lifecycle_management": True,
        "operations_dashboard": True,
        # Vocational-specific capabilities (defined in vocational_training_domain_spec.md)
        "CAP-VOCATIONAL-CERT-TRACKING": True,
        "CAP-VOCATIONAL-PLACEMENT-TRACKING": True,
        "CAP-VOCATIONAL-STRUCTURED-PATHWAY": True,
        "CAP-VOCATIONAL-PRACTICAL-ASSESSMENT": True,
        "CAP-VOCATIONAL-COMPLIANCE-CERT": True,
        "CAP-VOCATIONAL-OUTCOMES-DASHBOARD": True,
    },
    "default": {
        "notifications": True,
        "attendance_tracking": True,
    },
}

# MO-038 / Phase E: Pakistan-specific fee and payment behavior defaults.
# Source: pakistan_market_pricing_guide.md (MO-018).
# Applied at COUNTRY layer for PK — no inline country branching in service logic.
_COUNTRY_FEE_DEFAULTS: dict[str, dict[str, object]] = {
    "PK": {
        "grace_period_days": 5,
        "overdue_trigger_days": 5,
        "reminder_cadence_days": 2,
        "fee_reminders_enabled": True,
        "installment_support_enabled": True,
        "payment_methods_priority": ["jazzcash", "easypaisa", "bank_transfer", "cash"],
        "late_fee_enabled": False,
        "currency": "PKR",
    },
}


def seed_platform_defaults(config_service: object) -> None:
    """Seed country-layer and segment-layer defaults into the config service.

    MS-CONFIG-01 (MS§3.2): country locale (currency, whatsapp_primary, gdpr) and
    segment compliance/capability defaults live in the config resolution chain —
    not as inline conditionals in service logic.

    Idempotent: tenant overrides are higher precedence and are not affected.
    Called at OnboardingService.__init__ so defaults are present before any
    resolution call during tenant bootstrapping.
    """
    for country_code, locale in _COUNTRY_LOCALE_DEFAULTS.items():
        fee_defaults = _COUNTRY_FEE_DEFAULTS.get(country_code, {})
        config_service.upsert_override(ConfigOverride(
            scope=ConfigScope(level=ConfigLevel.COUNTRY, scope_id=country_code),
            behavior_tuning={
                "locale": {"currency": locale["currency"]},
                "communication": {"whatsapp_primary": locale["whatsapp_primary"]},
                "compliance": {"gdpr_consent_required": locale["gdpr_consent_required"]},
                # MO-038: country-specific fee/payment behavior
                **({"fees": fee_defaults} if fee_defaults else {}),
            },
        ))

    for segment_id, compliance in _SEGMENT_COMPLIANCE_DEFAULTS.items():
        cap_defaults = _SEGMENT_CAPABILITY_DEFAULTS.get(segment_id, _SEGMENT_CAPABILITY_DEFAULTS["default"])
        config_service.upsert_override(ConfigOverride(
            scope=ConfigScope(level=ConfigLevel.SEGMENT, scope_id=segment_id),
            behavior_tuning={"compliance": compliance},
            capability_enabled=cap_defaults,
        ))

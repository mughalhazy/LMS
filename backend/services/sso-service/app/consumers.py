"""Event consumers for sso-service (FA-024, G-24).

sso-spec.md defines no event consumer obligations for sso-service — it is an internal
delegation target called by auth-service, not an event-driven service. B02-005: removed
off-spec auth.login.succeeded.v1 subscription.
"""
from __future__ import annotations

import logging

logger = logging.getLogger("sso-service.consumers")


def register_consumers() -> None:
    """sso-service has no event consumer obligations per sso-spec.md."""
    logger.info("sso-service: no event consumers to register (sso-spec defines none)")

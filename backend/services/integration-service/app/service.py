"""Platform integration service — stateless capability decision orchestration.

CGAP-078: backend integration service — no Python code existed (only openapi.yaml).
Implements the B2P08 PlatformIntegrationAPI pattern: a stateless DecisionOrchestrator
that enforces the canonical 6-step evaluation pipeline per B2P08 spec:

  1. Capability Registry Resolve  — capability exists + active
  2. Config Resolution Fetch      — effective config snapshot for this capability
  3. Entitlement Check            — allow / deny / scope decision
  4. Feature Flag Evaluation      — rollout / treatment gate (only if entitlement allows)
  5. Final Decision Compose       — deterministic precedence matrix → ALLOW/DENY/CONDITIONAL
  6. Usage Metering Emit          — async side-effect; never mutates access decision

Returns a standard decision envelope with decision, reason_codes[], evaluation_trace_id.

Spec refs: docs/architecture/B2P08_platform_integration_layer_design.md
           docs/specs/integration_service_spec.md
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


# ------------------------------------------------------------------ #
# Decision constants                                                   #
# ------------------------------------------------------------------ #

class Decision:
    ALLOW = "ALLOW"
    DENY = "DENY"
    CONDITIONAL = "CONDITIONAL"


class DenyReason:
    CAPABILITY_UNAVAILABLE = "CAPABILITY_UNAVAILABLE"
    CONFIG_UNAVAILABLE = "CONFIG_UNAVAILABLE"
    ENTITLEMENT_DENIED = "ENTITLEMENT_DENIED"
    FLAG_DISABLED = "FLAG_DISABLED"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"


# ------------------------------------------------------------------ #
# In-memory connector registries (represent platform service state)   #
# ------------------------------------------------------------------ #

@dataclass
class CapabilityRecord:
    capability_key: str
    version: str
    is_active: bool
    requires_strict_config: bool = False


@dataclass
class EntitlementRecord:
    tenant_id: str
    capability_key: str
    decision: str  # "allow" | "deny" | "conditional"
    scope: dict[str, Any] = field(default_factory=dict)
    deny_reason: str | None = None


@dataclass
class FeatureFlagRecord:
    capability_key: str
    enabled: bool
    rollout_pct: float = 100.0  # 0–100


# ------------------------------------------------------------------ #
# Decision envelope                                                    #
# ------------------------------------------------------------------ #

def _make_envelope(
    *,
    trace_id: str,
    decision: str,
    capability_key: str,
    capability_version: str | None,
    reason_codes: list[str],
    entitlement_outcome: str | None,
    feature_flag_outcome: bool | None,
    config_snapshot: dict[str, Any],
    metering_event_ref: str | None,
    evaluated_at: str,
) -> dict[str, Any]:
    return {
        "evaluation_trace_id": trace_id,
        "decision": decision,
        "capability_key": capability_key,
        "effective_capability_version": capability_version,
        "reason_codes": reason_codes,
        "entitlement_outcome": entitlement_outcome,
        "feature_flag_outcome": feature_flag_outcome,
        "evaluated_config_snapshot": config_snapshot,
        "metering_event_ref": metering_event_ref,
        "evaluated_at": evaluated_at,
    }


# ------------------------------------------------------------------ #
# Main service                                                         #
# ------------------------------------------------------------------ #

class PlatformIntegrationService:
    """Stateless capability access decision orchestrator per B2P08.

    Enforces the canonical 6-step B2P08 evaluation pipeline for every
    evaluate_capability() call. All connector state is in-memory; in production
    these connectors would be thin HTTP clients to platform services.

    Precedence matrix (B2P08 §Minimal Decision Precedence Matrix):
      capability inactive/missing → DENY (CAPABILITY_UNAVAILABLE)
      capability active + entitlement deny → DENY (ENTITLEMENT_DENIED)
      capability active + entitlement allow + flag off → DENY (FLAG_DISABLED)
      capability active + entitlement allow + flag on → ALLOW
      capability active + entitlement conditional + flag on → CONDITIONAL
    """

    def __init__(self) -> None:
        # Connector registries (in-memory; represent reads from platform services)
        self._capabilities: dict[str, CapabilityRecord] = {}
        self._entitlements: dict[tuple[str, str], EntitlementRecord] = {}
        self._feature_flags: dict[str, FeatureFlagRecord] = {}
        self._config_store: dict[tuple[str, str], dict[str, Any]] = {}
        # Metering event log
        self._metering_log: list[dict[str, Any]] = []

    # ------------------------------------------------------------------ #
    # Connector registration (populate platform service state)            #
    # ------------------------------------------------------------------ #

    def register_capability(
        self,
        *,
        capability_key: str,
        version: str,
        is_active: bool = True,
        requires_strict_config: bool = False,
    ) -> None:
        """Register a capability in the in-memory capability registry connector."""
        self._capabilities[capability_key] = CapabilityRecord(
            capability_key=capability_key,
            version=version,
            is_active=is_active,
            requires_strict_config=requires_strict_config,
        )

    def set_entitlement(
        self,
        *,
        tenant_id: str,
        capability_key: str,
        decision: str,
        scope: dict[str, Any] | None = None,
        deny_reason: str | None = None,
    ) -> None:
        """Set entitlement outcome for a tenant × capability pair."""
        self._entitlements[(tenant_id, capability_key)] = EntitlementRecord(
            tenant_id=tenant_id,
            capability_key=capability_key,
            decision=decision,
            scope=scope or {},
            deny_reason=deny_reason,
        )

    def set_feature_flag(
        self,
        *,
        capability_key: str,
        enabled: bool,
        rollout_pct: float = 100.0,
    ) -> None:
        """Set feature flag state for a capability."""
        self._feature_flags[capability_key] = FeatureFlagRecord(
            capability_key=capability_key,
            enabled=enabled,
            rollout_pct=rollout_pct,
        )

    def set_config(
        self,
        *,
        tenant_id: str,
        capability_key: str,
        config: dict[str, Any],
    ) -> None:
        """Store an effective config snapshot for a tenant × capability."""
        self._config_store[(tenant_id, capability_key)] = config

    # ------------------------------------------------------------------ #
    # Core: evaluate_capability — the 6-step B2P08 pipeline               #
    # ------------------------------------------------------------------ #

    def evaluate_capability(
        self,
        *,
        tenant_id: str,
        actor_id: str,
        capability_key: str,
        resource_context: dict[str, Any] | None = None,
        request_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Evaluate capability access for a tenant × actor per B2P08 evaluation order.

        Returns a decision envelope: decision (ALLOW/DENY/CONDITIONAL),
        reason_codes[], evaluation_trace_id, and all intermediate outcomes.

        B2P08 evaluation order is immutable:
          1. Capability Registry Resolve
          2. Config Resolution Fetch
          3. Entitlement Check
          4. Feature Flag Evaluation
          5. Final Decision Compose
          6. Usage Metering Emit (post-decision, async, non-mutating)
        """
        trace_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        reason_codes: list[str] = []

        # ---- Step 1: Capability Registry Resolve ---- #
        cap = self._capabilities.get(capability_key)
        if cap is None or not cap.is_active:
            reason_codes.append(DenyReason.CAPABILITY_UNAVAILABLE)
            return _make_envelope(
                trace_id=trace_id,
                decision=Decision.DENY,
                capability_key=capability_key,
                capability_version=cap.version if cap else None,
                reason_codes=reason_codes,
                entitlement_outcome=None,
                feature_flag_outcome=None,
                config_snapshot={},
                metering_event_ref=None,
                evaluated_at=now,
            )

        # ---- Step 2: Config Resolution Fetch ---- #
        config_snapshot = self._config_store.get((tenant_id, capability_key), {})
        if cap.requires_strict_config and not config_snapshot:
            reason_codes.append(DenyReason.CONFIG_UNAVAILABLE)
            return _make_envelope(
                trace_id=trace_id,
                decision=Decision.DENY,
                capability_key=capability_key,
                capability_version=cap.version,
                reason_codes=reason_codes,
                entitlement_outcome=None,
                feature_flag_outcome=None,
                config_snapshot={},
                metering_event_ref=None,
                evaluated_at=now,
            )

        # ---- Step 3: Entitlement Check ---- #
        entitlement = self._entitlements.get((tenant_id, capability_key))
        # Default: deny if not explicitly granted (fail-closed per B2P08 §Degraded handling)
        ent_decision = entitlement.decision if entitlement else "deny"
        ent_deny_reason = entitlement.deny_reason if entitlement else DenyReason.ENTITLEMENT_DENIED

        if ent_decision == "deny":
            reason_codes.append(ent_deny_reason or DenyReason.ENTITLEMENT_DENIED)
            return _make_envelope(
                trace_id=trace_id,
                decision=Decision.DENY,
                capability_key=capability_key,
                capability_version=cap.version,
                reason_codes=reason_codes,
                entitlement_outcome=ent_decision,
                feature_flag_outcome=None,
                config_snapshot=config_snapshot,
                metering_event_ref=None,
                evaluated_at=now,
            )

        # ---- Step 4: Feature Flag Evaluation (only after entitlement allow) ---- #
        flag = self._feature_flags.get(capability_key)
        # Default: flag on if not explicitly registered (permissive default for unregistered flags)
        flag_on = flag.enabled if flag is not None else True

        if not flag_on:
            reason_codes.append(DenyReason.FLAG_DISABLED)
            return _make_envelope(
                trace_id=trace_id,
                decision=Decision.DENY,
                capability_key=capability_key,
                capability_version=cap.version,
                reason_codes=reason_codes,
                entitlement_outcome=ent_decision,
                feature_flag_outcome=False,
                config_snapshot=config_snapshot,
                metering_event_ref=None,
                evaluated_at=now,
            )

        # ---- Step 5: Final Decision Compose ---- #
        if ent_decision == "conditional":
            final_decision = Decision.CONDITIONAL
            reason_codes.append("CONDITIONAL_ENTITLEMENT")
        else:
            final_decision = Decision.ALLOW

        # ---- Step 6: Usage Metering Emit (post-decision side effect) ---- #
        metering_ref = self._emit_metering(
            tenant_id=tenant_id,
            actor_id=actor_id,
            capability_key=capability_key,
            decision=final_decision,
            trace_id=trace_id,
        )

        return _make_envelope(
            trace_id=trace_id,
            decision=final_decision,
            capability_key=capability_key,
            capability_version=cap.version,
            reason_codes=reason_codes,
            entitlement_outcome=ent_decision,
            feature_flag_outcome=flag_on,
            config_snapshot=config_snapshot,
            metering_event_ref=metering_ref,
            evaluated_at=now,
        )

    # ------------------------------------------------------------------ #
    # Batch evaluation                                                     #
    # ------------------------------------------------------------------ #

    def evaluate_capabilities(
        self,
        *,
        tenant_id: str,
        actor_id: str,
        capability_keys: list[str],
        resource_context: dict[str, Any] | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Evaluate multiple capabilities in one call. Returns {capability_key → envelope}."""
        return {
            key: self.evaluate_capability(
                tenant_id=tenant_id,
                actor_id=actor_id,
                capability_key=key,
                resource_context=resource_context,
            )
            for key in capability_keys
        }

    # ------------------------------------------------------------------ #
    # Metering log read                                                    #
    # ------------------------------------------------------------------ #

    def get_metering_log(
        self,
        *,
        tenant_id: str | None = None,
        capability_key: str | None = None,
    ) -> list[dict[str, Any]]:
        entries = list(self._metering_log)
        if tenant_id:
            entries = [e for e in entries if e["tenant_id"] == tenant_id]
        if capability_key:
            entries = [e for e in entries if e["capability_key"] == capability_key]
        return entries

    # ------------------------------------------------------------------ #
    # Internal                                                             #
    # ------------------------------------------------------------------ #

    def _emit_metering(
        self,
        *,
        tenant_id: str,
        actor_id: str,
        capability_key: str,
        decision: str,
        trace_id: str,
    ) -> str:
        """Record metering event. B2P08: metering failure must never mutate access decision."""
        ref = str(uuid4())
        try:
            self._metering_log.append({
                "metering_event_id": ref,
                "event_type": "usage.decision.evaluated",
                "tenant_id": tenant_id,
                "actor_id": actor_id,
                "capability_key": capability_key,
                "decision": decision,
                "evaluation_trace_id": trace_id,
                "emitted_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception:
            pass  # metering failure must not propagate per B2P08 §Flow B
        return ref

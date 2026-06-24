from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .models import FlagDecision, FlagDefinition
from .store import InMemoryFlagStore


def _deterministic_bucket(experiment_id: str, subject_key: str, total: int = 100) -> int:
    h = hashlib.md5(f"{experiment_id}:{subject_key}".encode()).hexdigest()
    return int(h[:8], 16) % total


_SPEC_FLAGS: List[Dict[str, Any]] = [
    # B07-006: feature-flags-spec.md — 8 canonical flag definitions seeded on startup
    {"feature_key": "tenant.feature.ai_recommendations", "default_state": False,
     "description": "AI recommendations — default OFF; tenant_admin only; tenant-scoped"},
    {"feature_key": "tenant.feature.custom_branding", "default_state": True,
     "description": "Custom branding — default ON for enterprise plan; read-only for non-entitled"},
    {"feature_key": "tenant.feature.advanced_analytics", "default_state": False,
     "description": "Advanced analytics — tenant+role scope; blocked for learners"},
    {"feature_key": "tenant.beta.new_dashboard", "default_state": False,
     "description": "New dashboard beta — beta_cohort tenants only; auto-disables on beta end date"},
    {"feature_key": "tenant.beta.ai_course_builder", "default_state": False,
     "description": "AI course builder beta — approved regions only; DPN acknowledgement required"},
    {"feature_key": "platform.rollout.mobile_nav_v2", "default_state": False,
     "description": "Mobile nav v2 — progressive rollout 1→5→25→50→100%; kill switch + tenant_override"},
    {"feature_key": "platform.rollout.search_index_v3", "default_state": False,
     "description": "Search index v3 — per-environment rollout; auto-rollback on SLO breach"},
    {"feature_key": "platform.rollout.assessment_grading_engine_v2", "default_state": False,
     "description": "Assessment grading engine v2 — non-compliance courses first; attempt pinning"},
]


class FeatureFlagService:
    def __init__(self, store: InMemoryFlagStore) -> None:
        self.store = store
        self._seed_spec_flags()

    def _seed_spec_flags(self) -> None:
        """Seed the 8 canonical flag definitions from feature-flags-spec.md (B07-006)."""
        for flag_data in _SPEC_FLAGS:
            if not self.store.get_flag(flag_data["feature_key"]):
                flag = FlagDefinition(
                    feature_key=flag_data["feature_key"],
                    default_state=flag_data["default_state"],
                    description=flag_data["description"],
                )
                self.store.save_flag(flag)

    def upsert_flag(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        feature_key = body.get("feature_key", "")
        if not feature_key:
            return 400, {"error": "feature_key_required"}

        from .models import ExperimentConfig
        exp_data = body.get("experiment")
        experiment = ExperimentConfig(**exp_data) if exp_data else None

        flag = FlagDefinition(
            feature_key=feature_key,
            default_state=bool(body.get("default_state", False)),
            kill_switch=bool(body.get("kill_switch", False)),
            segment_rules=body.get("segment_rules", {}),
            tenant_overrides=body.get("tenant_overrides", {}),
            experiment=experiment,
            description=body.get("description", ""),
        )
        self.store.save_flag(flag)
        return 200, self._serialize(flag)

    def get_flag(self, feature_key: str) -> Tuple[int, Dict[str, Any]]:
        flag = self.store.get_flag(feature_key)
        if not flag:
            return 404, {"error": "flag_not_found"}
        return 200, self._serialize(flag)

    def is_enabled(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        feature_key = body.get("feature_key", "")
        decision = self._evaluate(feature_key, body)
        return 200, {
            "feature_key": feature_key,
            "enabled": decision.state,
            "reason": decision.reason,
            "snapshot_version": decision.snapshot_version,
            "experiment_variant": decision.experiment_variant,
            "evaluated_at": decision.evaluated_at.isoformat(),
        }

    def resolve_many(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        feature_keys = body.get("feature_keys", [])
        results = {}
        for key in feature_keys:
            d = self._evaluate(key, body)
            results[key] = {"enabled": d.state, "reason": d.reason, "experiment_variant": d.experiment_variant}
        return 200, {"decisions": results, "snapshot_version": self.store.snapshot_version()}

    def _evaluate(self, feature_key: str, context: Dict[str, Any]) -> FlagDecision:
        now = datetime.now(timezone.utc)
        snap_ver = self.store.snapshot_version()
        flag = self.store.get_flag(feature_key)

        if flag is None:
            return FlagDecision(feature_key, False, "flag_not_found", None, snap_ver, None, now)

        # 1. Kill-switch — highest precedence
        if flag.kill_switch:
            return FlagDecision(feature_key, False, "kill_switch", "kill_switch", snap_ver, None, now)

        # 2. Entitlement guard — if caller passes entitlement_denied=True
        if context.get("entitlement_denied"):
            return FlagDecision(feature_key, False, "entitlement_denied", None, snap_ver, None, now)

        tenant_id = context.get("tenant_id", "")
        segment = context.get("segment", "")
        user_id = context.get("user_id", "")

        state = flag.default_state
        reason = "default"
        rule_id = None
        variant = None

        # 3. Segment rule
        if segment in flag.segment_rules:
            state = flag.segment_rules[segment]
            reason = "segment_rule"
            rule_id = f"segment:{segment}"

        # 4. Tenant override — supersedes segment
        if tenant_id in flag.tenant_overrides:
            state = flag.tenant_overrides[tenant_id]
            reason = "tenant_override"
            rule_id = f"tenant:{tenant_id}"

        # 5. Experiment allocation
        if flag.experiment:
            exp = flag.experiment
            subject_key = f"{tenant_id}:{user_id}" if user_id else tenant_id
            bucket = _deterministic_bucket(exp.experiment_id, subject_key)
            cumulative = 0
            for v in exp.variants:
                cumulative += v.get("weight", 0)
                if bucket < cumulative:
                    variant = v["name"]
                    state = v.get("state", state)
                    reason = "experiment"
                    rule_id = f"experiment:{exp.experiment_id}:{variant}"
                    break

        return FlagDecision(feature_key, state, reason, rule_id, snap_ver, variant, now)

    def _serialize(self, flag: FlagDefinition) -> Dict[str, Any]:
        return {
            "feature_key": flag.feature_key,
            "default_state": flag.default_state,
            "kill_switch": flag.kill_switch,
            "segment_rules": flag.segment_rules,
            "tenant_overrides": flag.tenant_overrides,
            "description": flag.description,
            "snapshot_version": flag.snapshot_version,
            "experiment": {
                "experiment_id": flag.experiment.experiment_id,
                "variants": flag.experiment.variants,
            } if flag.experiment else None,
        }

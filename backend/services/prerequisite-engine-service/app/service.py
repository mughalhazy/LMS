"""Prerequisite engine service — course enrollment gating and learning path progression validation.

CGAP-079: replaces NotImplementedError stub. Wires the existing validator modules
(CoursePrerequisiteValidator, LearningPathProgressionValidator) into a stateful service
that stores rules, learner eligibility, override history, and evaluation audit per
prerequisite_engine_spec.md.

Spec refs: docs/specs/prerequisite_engine_spec.md
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

_MODULES = Path(__file__).resolve().parents[1] / "modules" / "validation"
if str(_MODULES) not in sys.path:
    sys.path.insert(0, str(_MODULES))

from course_prerequisite_validator import CoursePrerequisiteValidator  # noqa: E402
from learning_path_progression_validator import LearningPathProgressionValidator  # noqa: E402
from models import (  # noqa: E402
    CoursePrerequisiteRule,
    DependencyType,
    EnrollmentDecision,
    EquivalencyMapping,
    LearningPathEdge,
    LearningPathNode,
    LearningPathProgressionResult,
    NodeProgress,
    PrerequisiteEvaluationResult,
    PrerequisiteNode,
    TranscriptRecord,
)


class PrerequisiteNotFoundError(Exception):
    """Raised when a rule or override is not found."""


class PrerequisiteEngineService:
    """Tenant-scoped prerequisite enforcement engine per prerequisite_engine_spec.md.

    Implements:
    - course_prerequisite: enrollment gating with AND/OR nodes, equivalencies, grade/validity windows
    - learning_path_dependency: DAG unlock state with strict/advisory dependencies
    - Policy override: instructor/admin override with reason code — fully audit-logged
    - Evaluation audit: every decision persisted with inputs, result, timestamp
    """

    def __init__(self) -> None:
        # Rules storage: tenant_id → {course_id → CoursePrerequisiteRule}
        self._rules: dict[str, dict[str, CoursePrerequisiteRule]] = {}
        # Equivalencies: tenant_id → list[EquivalencyMapping]
        self._equivalencies: dict[str, list[EquivalencyMapping]] = {}
        # Evaluation audit: tenant_id → list of audit dicts
        self._evaluation_audit: dict[str, list[dict[str, Any]]] = {}
        # Override log: tenant_id → list of override dicts
        self._override_log: dict[str, list[dict[str, Any]]] = {}

    # ------------------------------------------------------------------ #
    # Rule management                                                      #
    # ------------------------------------------------------------------ #

    def upsert_course_rule(
        self,
        *,
        tenant_id: str,
        target_course_id: str,
        prerequisite_nodes: list[dict[str, Any]],
    ) -> CoursePrerequisiteRule:
        """Store or replace a prerequisite rule for a course."""
        nodes = [
            PrerequisiteNode(
                node_id=n.get("node_id", str(uuid4())),
                required_course_ids=list(n["required_course_ids"]),
                operator=str(n.get("operator", "AND")).upper(),
                minimum_grade=n.get("minimum_grade"),
                valid_for_days=n.get("valid_for_days"),
                bridge_recommendations=list(n.get("bridge_recommendations", [])),
            )
            for n in prerequisite_nodes
        ]
        rule = CoursePrerequisiteRule(
            target_course_id=target_course_id,
            prerequisite_nodes=nodes,
        )
        self._rules.setdefault(tenant_id, {})[target_course_id] = rule
        return rule

    def get_course_rule(self, *, tenant_id: str, target_course_id: str) -> CoursePrerequisiteRule:
        rule = self._rules.get(tenant_id, {}).get(target_course_id)
        if not rule:
            raise PrerequisiteNotFoundError(f"No prerequisite rule for course '{target_course_id}'")
        return rule

    def add_equivalency(
        self,
        *,
        tenant_id: str,
        source_course_id: str,
        equivalent_course_ids: list[str],
    ) -> EquivalencyMapping:
        mapping = EquivalencyMapping(
            source_course_id=source_course_id,
            equivalent_course_ids=tuple(equivalent_course_ids),
        )
        self._equivalencies.setdefault(tenant_id, []).append(mapping)
        return mapping

    # ------------------------------------------------------------------ #
    # Enrollment prerequisite evaluation (course_prerequisite spec)       #
    # ------------------------------------------------------------------ #

    def evaluate_enrollment(
        self,
        *,
        tenant_id: str,
        target_course_id: str,
        learner_id: str,
        transcript: list[dict[str, Any]],
        now: datetime | None = None,
    ) -> PrerequisiteEvaluationResult:
        """Evaluate whether learner meets prerequisites for enrollment.

        Returns APPROVED or BLOCKED with unmet prerequisites and remedial recommendations.
        Audit-logs the evaluation per spec.
        """
        rule = self.get_course_rule(tenant_id=tenant_id, target_course_id=target_course_id)
        transcript_records = [
            TranscriptRecord(
                course_id=t["course_id"],
                completion_status=t.get("completion_status", "not_started"),
                score=t.get("score"),
                completed_at=datetime.fromisoformat(t["completed_at"]) if t.get("completed_at") else None,
            )
            for t in transcript
        ]
        equivalencies = self._equivalencies.get(tenant_id, [])
        result = CoursePrerequisiteValidator.validate_enrollment_prerequisites(
            rule=rule,
            transcript=transcript_records,
            equivalencies=equivalencies,
            now=now,
        )
        self._audit(
            tenant_id=tenant_id,
            event_type="enrollment.prerequisite.evaluated",
            learner_id=learner_id,
            target_course_id=target_course_id,
            decision=result.enrollment_decision.value,
            unmet=list(result.unmet_prerequisites),
        )
        return result

    # ------------------------------------------------------------------ #
    # Admin / instructor override (policy override per spec)              #
    # ------------------------------------------------------------------ #

    def override_enrollment(
        self,
        *,
        tenant_id: str,
        target_course_id: str,
        learner_id: str,
        override_by: str,
        reason_code: str,
        notes: str = "",
    ) -> dict[str, Any]:
        """Allow enrollment regardless of prerequisite state.

        prerequisite_engine_spec: "support policy override path: instructor/admin override
        requires reason code and is fully audit-logged."
        """
        if not reason_code.strip():
            raise ValueError("reason_code is required for prerequisite override")

        record: dict[str, Any] = {
            "override_id": str(uuid4()),
            "tenant_id": tenant_id,
            "target_course_id": target_course_id,
            "learner_id": learner_id,
            "override_by": override_by,
            "reason_code": reason_code.strip(),
            "notes": notes.strip(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "decision": EnrollmentDecision.APPROVED.value,
        }
        self._override_log.setdefault(tenant_id, []).append(record)
        self._audit(
            tenant_id=tenant_id,
            event_type="enrollment.prerequisite.override",
            learner_id=learner_id,
            target_course_id=target_course_id,
            override_by=override_by,
            reason_code=reason_code,
        )
        return record

    def get_override_log(self, *, tenant_id: str, learner_id: str | None = None) -> list[dict[str, Any]]:
        logs = self._override_log.get(tenant_id, [])
        if learner_id:
            logs = [entry for entry in logs if entry["learner_id"] == learner_id]
        return logs

    # ------------------------------------------------------------------ #
    # Learning path progression (learning_path_dependency spec)           #
    # ------------------------------------------------------------------ #

    def evaluate_path_progression(
        self,
        *,
        tenant_id: str,
        learner_id: str,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        progress: list[dict[str, Any]],
    ) -> LearningPathProgressionResult:
        """Compute unlock/lock state for a learning path DAG.

        prerequisite_engine_spec: strict lock vs advisory warning, acyclicity enforcement,
        lock/unlock transition recording.
        """
        path_nodes = [
            LearningPathNode(
                node_id=n["node_id"],
                strict_dependency=DependencyType(n.get("strict_dependency", "strict")),
                minimum_score=n.get("minimum_score"),
            )
            for n in nodes
        ]
        path_edges = [
            LearningPathEdge(
                from_node_id=e["from_node_id"],
                to_node_id=e["to_node_id"],
                dependency_type=DependencyType(e.get("dependency_type", "strict")),
            )
            for e in edges
        ]
        node_progress = [
            NodeProgress(
                node_id=p["node_id"],
                completion_status=p.get("completion_status", "not_started"),
                score=p.get("score"),
            )
            for p in progress
        ]
        result = LearningPathProgressionValidator.validate_progression_requirements(
            nodes=path_nodes,
            edges=path_edges,
            progress=node_progress,
        )
        self._audit(
            tenant_id=tenant_id,
            event_type="learning_path.progression.evaluated",
            learner_id=learner_id,
            unlocked=list(result.unlocked_nodes),
            locked=list(result.locked_nodes),
            violations=list(result.violations),
        )
        return result

    # ------------------------------------------------------------------ #
    # Eligibility check (learner prerequisite gate)                       #
    # ------------------------------------------------------------------ #

    def check_learner_eligibility(
        self,
        *,
        tenant_id: str,
        learner_id: str,
        target_course_id: str,
        transcript: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Quick eligibility check — returns eligible bool + details."""
        try:
            rule = self.get_course_rule(tenant_id=tenant_id, target_course_id=target_course_id)
        except PrerequisiteNotFoundError:
            # No rule configured → open enrollment
            return {"eligible": True, "reason": "no_prerequisites_configured", "unmet": []}

        result = self.evaluate_enrollment(
            tenant_id=tenant_id,
            target_course_id=target_course_id,
            learner_id=learner_id,
            transcript=transcript,
        )
        return {
            "eligible": result.enrollment_decision == EnrollmentDecision.APPROVED,
            "reason": result.enrollment_decision.value,
            "unmet": list(result.unmet_prerequisites),
            "recommendations": list(result.remedial_recommendations),
        }

    # ------------------------------------------------------------------ #
    # Audit                                                                #
    # ------------------------------------------------------------------ #

    def get_evaluation_audit(self, *, tenant_id: str, learner_id: str | None = None) -> list[dict[str, Any]]:
        logs = self._evaluation_audit.get(tenant_id, [])
        if learner_id:
            logs = [entry for entry in logs if entry.get("learner_id") == learner_id]
        return logs

    def _audit(self, *, tenant_id: str, event_type: str, **kwargs: Any) -> None:
        self._evaluation_audit.setdefault(tenant_id, []).append({
            "audit_id": str(uuid4()),
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **kwargs,
        })

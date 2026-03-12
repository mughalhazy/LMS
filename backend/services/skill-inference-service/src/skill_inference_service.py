from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from .entities import (
    CourseSkillMapping,
    LearnerSkillEvidence,
    LearnerSkillState,
    SkillEdge,
    SkillInferenceResult,
    SkillNode,
)


class SkillInferenceService:
    """Infers tenant-scoped learner skill levels from weighted, time-decayed evidence."""

    _MASTERY_BANDS: List[Tuple[float, str]] = [
        (0.85, "expert"),
        (0.70, "proficient"),
        (0.45, "developing"),
        (0.0, "novice"),
    ]

    def __init__(self) -> None:
        self._skills: Dict[str, SkillNode] = {}
        self._skill_edges: List[SkillEdge] = []
        self._course_skill_mappings: List[CourseSkillMapping] = []
        self._evidence_store: Dict[str, Dict[str, Dict[str, List[LearnerSkillEvidence]]]] = {}
        self._learner_skill_states: Dict[str, Dict[str, Dict[str, LearnerSkillState]]] = {}

    def upsert_skill(self, skill: SkillNode) -> None:
        self._skills[skill.skill_id] = skill

    def add_skill_relation(self, edge: SkillEdge) -> None:
        self._skill_edges.append(edge)

    def map_course_to_skill(self, mapping: CourseSkillMapping) -> None:
        self._course_skill_mappings.append(mapping)

    def ingest_evidence(self, evidence: LearnerSkillEvidence) -> None:
        tenant_bucket = self._evidence_store.setdefault(evidence.tenant_id, {})
        learner_bucket = tenant_bucket.setdefault(evidence.learner_id, {})
        learner_bucket.setdefault(evidence.skill_id, []).append(evidence)

    def infer_learner_skills(self, tenant_id: str, learner_id: str, as_of: datetime | None = None) -> SkillInferenceResult:
        inference_time = as_of or datetime.utcnow()
        tenant_bucket = self._evidence_store.get(tenant_id, {})
        learner_evidence = tenant_bucket.get(learner_id, {})

        updated_skills: Dict[str, LearnerSkillState] = {}
        for skill_id, evidence_list in learner_evidence.items():
            mastery_score, confidence = self._compute_mastery_score(evidence_list, inference_time)
            predicted_band = self._predict_mastery_band(mastery_score)
            new_level = self._score_to_level(mastery_score)

            state = LearnerSkillState(
                tenant_id=tenant_id,
                learner_id=learner_id,
                skill_id=skill_id,
                current_level=new_level,
                confidence=confidence,
                mastery_score=mastery_score,
                predicted_mastery_band=predicted_band,
                evidence_count=len(evidence_list),
                last_assessed_at=max(item.occurred_at for item in evidence_list),
            )
            self._upsert_learner_skill_state(state)
            updated_skills[skill_id] = state

        self._apply_graph_propagation(tenant_id=tenant_id, learner_id=learner_id, inferred_at=inference_time)

        return SkillInferenceResult(
            tenant_id=tenant_id,
            learner_id=learner_id,
            inferred_at=inference_time,
            updated_skills=self._learner_skill_states.get(tenant_id, {}).get(learner_id, {}),
        )

    def _upsert_learner_skill_state(self, state: LearnerSkillState) -> None:
        tenant_bucket = self._learner_skill_states.setdefault(state.tenant_id, {})
        learner_bucket = tenant_bucket.setdefault(state.learner_id, {})
        learner_bucket[state.skill_id] = state

    def _compute_mastery_score(
        self,
        evidence_list: List[LearnerSkillEvidence],
        inference_time: datetime,
    ) -> Tuple[float, float]:
        weighted_total = 0.0
        weight_sum = 0.0

        for ev in evidence_list:
            recency_days = max((inference_time - ev.occurred_at).days, 0)
            recency_weight = max(0.25, 1 - (recency_days / 180))
            verification_boost = 1.1 if ev.verified else 1.0
            signal_weight = ev.confidence_weight * recency_weight * verification_boost

            weighted_total += ev.normalized_score * signal_weight
            weight_sum += signal_weight

        if weight_sum == 0:
            return 0.0, 0.0

        mastery_score = max(0.0, min(1.0, weighted_total / weight_sum))
        confidence = min(1.0, weight_sum / max(len(evidence_list), 1))
        return round(mastery_score, 4), round(confidence, 4)

    def _predict_mastery_band(self, mastery_score: float) -> str:
        for threshold, band in self._MASTERY_BANDS:
            if mastery_score >= threshold:
                return band
        return "novice"

    def _score_to_level(self, mastery_score: float) -> int:
        return min(5, max(0, int(round(mastery_score * 5))))

    def _apply_graph_propagation(self, tenant_id: str, learner_id: str, inferred_at: datetime) -> None:
        learner_states = self._learner_skill_states.get(tenant_id, {}).get(learner_id, {})
        if not learner_states:
            return

        prerequisite_edges = [edge for edge in self._skill_edges if edge.relation_type == "PREREQUISITE_OF"]
        related_edges = [edge for edge in self._skill_edges if edge.relation_type == "RELATED_TO"]

        for edge in prerequisite_edges:
            source = learner_states.get(edge.source_skill_id)
            target = learner_states.get(edge.target_skill_id)
            if not source or not target:
                continue

            max_allowed = min(source.current_level + 1, 5)
            if target.current_level > max_allowed:
                target.current_level = max_allowed
                target.mastery_score = round(max_allowed / 5, 4)
                target.predicted_mastery_band = self._predict_mastery_band(target.mastery_score)
                target.last_assessed_at = inferred_at

        for edge in related_edges:
            source = learner_states.get(edge.source_skill_id)
            target = learner_states.get(edge.target_skill_id)
            if not source or not target:
                continue

            propagated = source.mastery_score * 0.1 * edge.relation_weight
            if propagated <= 0:
                continue
            target.mastery_score = round(min(1.0, target.mastery_score + propagated), 4)
            target.current_level = self._score_to_level(target.mastery_score)
            target.predicted_mastery_band = self._predict_mastery_band(target.mastery_score)
            target.last_assessed_at = inferred_at

    def get_learner_skill_profile(self, tenant_id: str, learner_id: str) -> Dict[str, Dict[str, object]]:
        learner_states = self._learner_skill_states.get(tenant_id, {}).get(learner_id, {})
        return {skill_id: asdict(state) for skill_id, state in learner_states.items()}

    def get_skill_graph(self) -> Dict[str, object]:
        return {
            "skills": [asdict(skill) for skill in self._skills.values()],
            "relations": [asdict(edge) for edge in self._skill_edges],
            "course_skill_mappings": [asdict(mapping) for mapping in self._course_skill_mappings],
        }

    def update_skill_graph(self, *, add_edges: List[SkillEdge] | None = None, remove_edges: List[SkillEdge] | None = None) -> None:
        add_edges = add_edges or []
        remove_edges = remove_edges or []

        if remove_edges:
            removal_keys = {
                (edge.source_skill_id, edge.target_skill_id, edge.relation_type)
                for edge in remove_edges
            }
            self._skill_edges = [
                edge
                for edge in self._skill_edges
                if (edge.source_skill_id, edge.target_skill_id, edge.relation_type) not in removal_keys
            ]

        self._skill_edges.extend(add_edges)

    def infer_skills_from_course_completion(
        self,
        *,
        tenant_id: str,
        learner_id: str,
        course_id: str,
        completion_score: float,
        occurred_at: datetime | None = None,
    ) -> SkillInferenceResult:
        occurred = occurred_at or datetime.utcnow()
        mappings = [m for m in self._course_skill_mappings if m.course_id == course_id]

        for mapping in mappings:
            normalized = max(0.0, min(1.0, completion_score * mapping.evidence_weight))
            self.ingest_evidence(
                LearnerSkillEvidence(
                    tenant_id=tenant_id,
                    learner_id=learner_id,
                    skill_id=mapping.skill_id,
                    evidence_id=f"{course_id}:{mapping.skill_id}:{int(occurred.timestamp())}",
                    evidence_type="course_completion",
                    normalized_score=normalized,
                    confidence_weight=max(0.1, mapping.skill_gain_expected),
                    occurred_at=occurred,
                    verified=True,
                    metadata={"course_id": course_id, "coverage_level": mapping.coverage_level},
                )
            )

        return self.infer_learner_skills(tenant_id=tenant_id, learner_id=learner_id, as_of=occurred + timedelta(seconds=1))

from __future__ import annotations

from datetime import datetime

from src.entities import LearnerSkillEvidence, SkillEdge, SkillNode
from src.skill_inference_service import SkillInferenceService

from .models import AnalyticsSignal, SkillGraphEdge, SkillGraphNode
from .store import SkillInferenceStore


class SkillInferenceApplicationService:
    """Application service integrating analytics inputs and knowledge graph with inference."""

    def __init__(self, store: SkillInferenceStore | None = None, engine: SkillInferenceService | None = None) -> None:
        self.store = store or SkillInferenceStore()
        self.engine = engine or SkillInferenceService()
        self._progression_snapshots: dict[str, dict[str, list[dict[str, object]]]] = {}

    def ingest_analytics_signals(self, *, tenant_id: str, learner_id: str, signals: list[AnalyticsSignal]) -> dict[str, object]:
        tenant_signals = [s for s in signals if s.tenant_id == tenant_id and s.learner_id == learner_id]
        self.store.add_analytics_signals(tenant_signals)

        for signal in tenant_signals:
            self.engine.ingest_evidence(
                LearnerSkillEvidence(
                    tenant_id=signal.tenant_id,
                    learner_id=signal.learner_id,
                    skill_id=signal.skill_id,
                    evidence_id=signal.signal_id,
                    evidence_type=signal.signal_type,
                    normalized_score=max(0.0, min(1.0, signal.score)),
                    confidence_weight=max(0.1, signal.confidence),
                    timestamp=signal.timestamp,
                    verified=signal.verified,
                    metadata=signal.metadata,
                )
            )

        return {
            "tenant_id": tenant_id,
            "learner_id": learner_id,
            "ingested_signals": len(tenant_signals),
        }

    def upsert_knowledge_graph(self, *, nodes: list[SkillGraphNode], edges: list[SkillGraphEdge]) -> dict[str, int]:
        self.store.upsert_skill_nodes(nodes)
        self.store.append_skill_edges(edges)

        for node in nodes:
            self.engine.upsert_skill(
                SkillNode(
                    skill_id=node.skill_id,
                    name=node.name,
                    category_id=node.category_id,
                    difficulty_base=node.difficulty_base,
                )
            )
        for edge in edges:
            self.engine.add_skill_relation(
                SkillEdge(
                    source_skill_id=edge.source_skill_id,
                    target_skill_id=edge.target_skill_id,
                    relation_type=edge.relation_type,
                    relation_weight=edge.relation_weight,
                )
            )

        return {"skills_upserted": len(nodes), "edges_upserted": len(edges)}

    def run_inference(self, *, tenant_id: str, learner_id: str, as_of: datetime | None = None) -> dict[str, object]:
        result = self.engine.infer_learner_skills(tenant_id=tenant_id, learner_id=learner_id, as_of=as_of)
        profile = self.engine.get_learner_skill_profile(tenant_id=tenant_id, learner_id=learner_id)

        learner_progression = self._progression_snapshots.setdefault(tenant_id, {}).setdefault(learner_id, [])
        learner_progression.append(
            {
                "inferred_at": result.inferred_at.isoformat(),
                "skills": {
                    skill_id: {
                        "current_level": state["current_level"],
                        "mastery_score": state["mastery_score"],
                        "predicted_mastery_band": state["predicted_mastery_band"],
                        "confidence": state["confidence"],
                    }
                    for skill_id, state in profile.items()
                },
            }
        )

        return {
            "tenant_id": tenant_id,
            "learner_id": learner_id,
            "inferred_at": result.inferred_at.isoformat(),
            "skill_levels": profile,
            "skill_progression_count": len(learner_progression),
        }

    def get_skill_progression(self, *, tenant_id: str, learner_id: str) -> dict[str, object]:
        snapshots = self._progression_snapshots.get(tenant_id, {}).get(learner_id, [])
        latest = snapshots[-1]["skills"] if snapshots else {}

        per_skill_timeline: dict[str, list[dict[str, object]]] = {}
        for snapshot in snapshots:
            inferred_at = snapshot["inferred_at"]
            for skill_id, state in snapshot["skills"].items():
                per_skill_timeline.setdefault(skill_id, []).append(
                    {
                        "inferred_at": inferred_at,
                        "current_level": state["current_level"],
                        "mastery_score": state["mastery_score"],
                        "predicted_mastery_band": state["predicted_mastery_band"],
                    }
                )

        return {
            "tenant_id": tenant_id,
            "learner_id": learner_id,
            "latest_skill_levels": latest,
            "skill_progression": per_skill_timeline,
        }

    def get_skill_graph(self) -> dict[str, object]:
        graph = self.engine.get_skill_graph()
        return {
            "skills": graph["skills"],
            "relations": graph["relations"],
            "course_skill_mappings": graph["course_skill_mappings"],
        }

"""Service entrypoint."""

from __future__ import annotations

from fastapi import FastAPI

from .models import AnalyticsSignal, SkillGraphEdge, SkillGraphNode
from .schemas import InferenceRequest, IngestAnalyticsRequest, KnowledgeGraphUpsertRequest, ProgressionQuery
from .service import SkillInferenceApplicationService

app = FastAPI()
service = SkillInferenceApplicationService()


class SkillInferenceAPI:
    def __init__(self, application_service: SkillInferenceApplicationService | None = None) -> None:
        self.service = application_service or SkillInferenceApplicationService()

    def ingest_analytics(self, payload: IngestAnalyticsRequest) -> dict[str, object]:
        signals = [
            AnalyticsSignal(
                tenant_id=payload.tenant_id,
                learner_id=payload.learner_id,
                skill_id=item.skill_id,
                signal_id=item.signal_id,
                signal_type=item.signal_type,
                score=item.score,
                confidence=item.confidence,
                occurred_at=item.occurred_at,
                verified=item.verified,
                metadata=item.metadata,
            )
            for item in payload.signals
        ]
        return self.service.ingest_analytics_signals(
            tenant_id=payload.tenant_id,
            learner_id=payload.learner_id,
            signals=signals,
        )

    def upsert_knowledge_graph(self, payload: KnowledgeGraphUpsertRequest) -> dict[str, int]:
        return self.service.upsert_knowledge_graph(
            nodes=[
                SkillGraphNode(
                    skill_id=node.skill_id,
                    name=node.name,
                    category_id=node.category_id,
                    difficulty_base=node.difficulty_base,
                )
                for node in payload.skills
            ],
            edges=[
                SkillGraphEdge(
                    source_skill_id=edge.source_skill_id,
                    target_skill_id=edge.target_skill_id,
                    relation_type=edge.relation_type,
                    relation_weight=edge.relation_weight,
                )
                for edge in payload.edges
            ],
        )

    def infer(self, payload: InferenceRequest) -> dict[str, object]:
        return self.service.run_inference(tenant_id=payload.tenant_id, learner_id=payload.learner_id, as_of=payload.as_of)

    def get_progression(self, payload: ProgressionQuery) -> dict[str, object]:
        return self.service.get_skill_progression(tenant_id=payload.tenant_id, learner_id=payload.learner_id)


api = SkillInferenceAPI(service)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "skill-inference-service"}


@app.get("/metrics")
def metrics() -> dict[str, int | str]:
    return {"service": "skill-inference-service", "service_up": 1}


@app.post("/knowledge-graph/upsert")
def upsert_knowledge_graph(payload: KnowledgeGraphUpsertRequest) -> dict[str, int]:
    return api.upsert_knowledge_graph(payload)


@app.post("/analytics/ingest")
def ingest_analytics(payload: IngestAnalyticsRequest) -> dict[str, object]:
    return api.ingest_analytics(payload)


@app.post("/inference/run")
def run_inference(payload: InferenceRequest) -> dict[str, object]:
    return api.infer(payload)


@app.get("/learners/{tenant_id}/{learner_id}/progression")
def learner_progression(tenant_id: str, learner_id: str) -> dict[str, object]:
    return api.get_progression(ProgressionQuery(tenant_id=tenant_id, learner_id=learner_id))

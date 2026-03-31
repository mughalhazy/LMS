import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.models import AnalyticsSignal, SkillGraphEdge, SkillGraphNode
from app.service import SkillInferenceApplicationService


def test_inference_uses_analytics_and_knowledge_graph_and_returns_progression() -> None:
    service = SkillInferenceApplicationService()

    service.upsert_knowledge_graph(
        nodes=[
            SkillGraphNode(skill_id="s-python", name="Python", category_id="cat-dev"),
            SkillGraphNode(skill_id="s-ml", name="Machine Learning", category_id="cat-ai"),
        ],
        edges=[
            SkillGraphEdge(
                source_skill_id="s-python",
                target_skill_id="s-ml",
                relation_type="PREREQUISITE_OF",
                relation_weight=1.0,
            )
        ],
    )

    now = datetime.utcnow()
    ingest_result = service.ingest_analytics_signals(
        tenant_id="tenant-1",
        learner_id="learner-1",
        signals=[
            AnalyticsSignal(
                tenant_id="tenant-1",
                learner_id="learner-1",
                skill_id="s-python",
                signal_id="sig-1",
                signal_type="assessment",
                score=0.95,
                confidence=1.0,
                occurred_at=now - timedelta(days=1),
                verified=True,
            ),
            AnalyticsSignal(
                tenant_id="tenant-1",
                learner_id="learner-1",
                skill_id="s-ml",
                signal_id="sig-2",
                signal_type="quiz",
                score=1.0,
                confidence=0.9,
                occurred_at=now,
                verified=False,
            ),
        ],
    )

    assert ingest_result["ingested_signals"] == 2

    first_inference = service.run_inference(tenant_id="tenant-1", learner_id="learner-1", as_of=now)
    second_inference = service.run_inference(tenant_id="tenant-1", learner_id="learner-1", as_of=now + timedelta(days=2))

    python_level = first_inference["skill_levels"]["s-python"]["current_level"]
    ml_level = first_inference["skill_levels"]["s-ml"]["current_level"]

    assert python_level >= 4
    assert ml_level <= python_level + 1
    assert second_inference["skill_progression_count"] == 2

    progression = service.get_skill_progression(tenant_id="tenant-1", learner_id="learner-1")
    assert "s-python" in progression["skill_progression"]
    assert len(progression["skill_progression"]["s-python"]) == 2

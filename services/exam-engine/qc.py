from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))
sys.path.append(str(Path(__file__).resolve().parent))

from service import ExamEngineService, TenantCapacityProfile


def run_qc() -> dict[str, object]:
    service = ExamEngineService()
    service.register_tenant("tenant_alpha", TenantCapacityProfile(max_active_sessions=2, shard_count=3, burst_queue_limit=2))
    service.register_tenant("tenant_beta", TenantCapacityProfile(max_active_sessions=1, shard_count=3, burst_queue_limit=0))

    s1 = service.create_exam_session(tenant_id="tenant_alpha", exam_id="exam", student_id="u1")
    s2 = service.create_exam_session(tenant_id="tenant_alpha", exam_id="exam", student_id="u2")
    service.start_exam_session(tenant_id="tenant_alpha", exam_session_id=s1.exam_session_id)
    service.start_exam_session(tenant_id="tenant_alpha", exam_session_id=s2.exam_session_id)
    service.submit_exam_session(tenant_id="tenant_alpha", exam_session_id=s1.exam_session_id, score=91)

    b1 = service.create_exam_session(tenant_id="tenant_beta", exam_id="exam", student_id="u3")
    service.start_exam_session(tenant_id="tenant_beta", exam_session_id=b1.exam_session_id)
    try:
        b2 = service.create_exam_session(tenant_id="tenant_beta", exam_id="exam", student_id="u4")
        service.start_exam_session(tenant_id="tenant_beta", exam_session_id=b2.exam_session_id)
        hot_tenant_limited = False
    except RuntimeError:
        hot_tenant_limited = True

    alpha = service.tenant_metrics("tenant_alpha")
    beta = service.tenant_metrics("tenant_beta")

    tenant_isolation = alpha["completed_sessions"] == 1 and beta["completed_sessions"] == 0
    no_shared_bottlenecks = hot_tenant_limited and alpha["active_sessions"] >= 1
    shard_partitioning = len(alpha["shard_load"]) == 3 and len(beta["shard_load"]) == 3
    deterministic_audit = len(service.tenant_audit_log("tenant_alpha")) > 0

    passed = tenant_isolation and no_shared_bottlenecks and shard_partitioning and deterministic_audit
    return {
        "checks": {
            "tenant_isolation": tenant_isolation,
            "load_handling_per_tenant": no_shared_bottlenecks,
            "shard_partitioning": shard_partitioning,
            "deterministic_audit_trail": deterministic_audit,
        },
        "score": 10 if passed else 0,
    }


if __name__ == "__main__":
    print(json.dumps(run_qc(), indent=2))

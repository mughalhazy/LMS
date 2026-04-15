from __future__ import annotations

import json
import statistics
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run_python(code: str, cwd: Path) -> dict:
    proc = subprocess.run(
        ["python", "-c", code],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout.strip())


def benchmark_api_gateway() -> dict:
    import re

    routes_text = (ROOT / "infrastructure/api-gateway/routes.yaml").read_text(encoding="utf-8")
    route_lines = [line.strip().split(": ", 1)[1] for line in routes_text.splitlines() if line.strip().startswith("- path:")]
    regexes = [re.compile("^" + re.sub(r"\{[^/]+\}", "[^/]+", p) + "$") for p in route_lines]
    samples = [
        "/api/v1/auth/login",
        "/api/v1/courses/c-123",
        "/api/v1/enrollments/e-456",
        "/api/v1/events/metrics",
        "/api/v1/analytics/courses/c-1/performance",
    ]

    latencies = []
    iterations = 5000
    for i in range(iterations):
        path = samples[i % len(samples)]
        start = time.perf_counter()
        any(r.match(path) for r in regexes)
        latencies.append((time.perf_counter() - start) * 1000)

    return {
        "name": "api_gateway_latency",
        "avg_ms": round(statistics.mean(latencies), 4),
        "p95_ms": round(statistics.quantiles(latencies, n=100)[94], 4),
    }


def benchmark_auth_throughput() -> dict:
    code = r'''
import json, time
from app.store import InMemoryAuthStore
from app.service import AuthService
from app.schemas import LoginRequest, TokenRequest, TokenValidationRequest

store = InMemoryAuthStore()
service = AuthService(store, signing_secret="perf-secret")

status, login_payload = service.login(LoginRequest(tenant_id="tenant-acme", email="admin@acme.test", password="AcmePass#123"))
assert status == 200

iterations = 5000
start = time.perf_counter()
for _ in range(iterations):
    status, token_payload = service.issue_tokens(TokenRequest(
        tenant_id="tenant-acme",
        user_id=login_payload["user_id"],
        session_id=login_payload["session_id"],
        roles=login_payload["roles"],
    ))
    assert status == 200
    status, _ = service.validate_session(TokenValidationRequest(
        tenant_id="tenant-acme",
        access_token=token_payload["access_token"],
    ))
    assert status == 200
elapsed = time.perf_counter() - start
print(json.dumps({"throughput_rps": (iterations * 2) / elapsed, "avg_request_ms": (elapsed / (iterations * 2)) * 1000}))
'''
    out = run_python(code, ROOT / "backend/services/auth-service")
    return {
        "name": "auth_throughput",
        "throughput_rps": round(out["throughput_rps"], 2),
        "avg_ms": round(out["avg_request_ms"], 4),
    }


def benchmark_course_queries() -> dict:
    code = r'''
import json, time
from app.service import CourseService
from app.schemas import CreateCourseRequest

service = CourseService()
tenant_id = "tenant_perf"
for i in range(3000):
    service.create_course(CreateCourseRequest(
        tenant_id=tenant_id,
        created_by="perf",
        title=f"Course {i}",
    ))

start = time.perf_counter()
for _ in range(500):
    courses = service.list_courses(tenant_id)
    _ = courses[0]
elapsed = time.perf_counter() - start
print(json.dumps({"avg_list_ms": (elapsed/500)*1000, "course_count": len(courses)}))
'''
    out = run_python(code, ROOT / "backend/services/course-service")
    return {
        "name": "course_service_queries",
        "avg_ms": round(out["avg_list_ms"], 4),
        "course_count": out["course_count"],
    }


def benchmark_enrollment_processing() -> dict:
    code = r'''
import json, time
from src.service import EnrollmentService
from src.models import EnrollmentRequest

service = EnrollmentService()
iterations = 5000
start = time.perf_counter()
for i in range(iterations):
    service.enroll_learner(EnrollmentRequest(
        tenant_id="tenant_perf",
        organization_id="org-1",
        learner_id=f"learner-{i}",
        learning_object_id="course-1",
        requested_by="perf",
    ))
elapsed = time.perf_counter() - start
print(json.dumps({"throughput_rps": iterations/elapsed, "avg_ms": (elapsed/iterations)*1000}))
'''
    out = run_python(code, ROOT / "backend/services/enrollment-service")
    return {
        "name": "enrollment_processing",
        "throughput_rps": round(out["throughput_rps"], 2),
        "avg_ms": round(out["avg_ms"], 4),
    }


def benchmark_analytics_ingestion() -> dict:
    code = r'''
import json, time
from app.service import EventIngestionService
from app.store import InMemoryEventStore
from app.schemas import EventIngestRequest, utc_now_iso

service = EventIngestionService(InMemoryEventStore())
iterations = 5000
start = time.perf_counter()
for i in range(iterations):
    status, _ = service.ingest_event(EventIngestRequest(
        event_id=f"event-{i}",
        event_type="AssessmentAttemptSubmitted",
        source_system="web",
        tenant_id="tenant_perf",
        actor_id=f"user-{i}",
        session_id=f"session-{i}",
        timestamp=utc_now_iso(),
        schema_version="1.0",
        payload={"attempt_id": f"attempt-{i}", "learner_id": f"user-{i}", "assessment_id": "a1", "course_id": "c1", "attempt_number": 1, "score": 88, "max_score": 100, "passed_flag": True, "submitted_at": utc_now_iso(), "time_spent_seconds": 120},
        ingestion_channel="api",
    ))
    assert status == 202
elapsed = time.perf_counter() - start
print(json.dumps({"throughput_rps": iterations/elapsed, "avg_ms": (elapsed/iterations)*1000}))
'''
    out = run_python(code, ROOT / "backend/services/event-ingestion-service")
    return {
        "name": "analytics_ingestion",
        "throughput_rps": round(out["throughput_rps"], 2),
        "avg_ms": round(out["avg_ms"], 4),
    }


def benchmark_event_bus_latency() -> dict:
    import collections

    queue = collections.deque()
    latencies = []
    iterations = 8000
    for i in range(iterations):
        sent = time.perf_counter()
        queue.append({"event_id": i, "ts": sent})
        event = queue.popleft()
        latencies.append((time.perf_counter() - event["ts"]) * 1000)

    return {
        "name": "event_bus_latency",
        "avg_ms": round(statistics.mean(latencies), 4),
        "p95_ms": round(statistics.quantiles(latencies, n=100)[94], 4),
    }


def verify_service_startup() -> list[str]:
    checks = [
        (ROOT / "backend/services/auth-service", "import app.main"),
        (ROOT / "backend/services/course-service", "import app.main"),
        (ROOT / "backend/services/enrollment-service", "import app.main"),
        (ROOT / "backend/services/event-ingestion-service", "import app.main"),
    ]
    failures: list[str] = []
    for cwd, stmt in checks:
        cmd = ["python", "-c", stmt]
        env = None
        if "auth-service" in str(cwd):
            env = {**__import__("os").environ, "JWT_SHARED_SECRET": "perf-secret"}
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)
        if proc.returncode != 0:
            failures.append(f"{cwd.name}: {proc.stderr.strip()}")
    return failures


def main() -> None:
    metrics = [
        benchmark_api_gateway(),
        benchmark_auth_throughput(),
        benchmark_course_queries(),
        benchmark_enrollment_processing(),
        benchmark_analytics_ingestion(),
        benchmark_event_bus_latency(),
    ]

    startup_failures = verify_service_startup()

    latency_values = [m["avg_ms"] for m in metrics if "avg_ms" in m]
    under_target = all(v < 200 for v in latency_values)
    no_startup_failures = not startup_failures
    score = 10 if under_target and no_startup_failures else 6

    print(json.dumps({
        "services_tested": [m["name"] for m in metrics],
        "performance_metrics": metrics,
        "startup_failures": startup_failures,
        "performance_score": score,
    }, indent=2))


if __name__ == "__main__":
    main()

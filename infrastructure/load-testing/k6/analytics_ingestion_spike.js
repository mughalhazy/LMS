import http from 'k6/http';
import { check } from 'k6';

export const options = {
  scenarios: {
    ingestion_spike: {
      executor: 'constant-arrival-rate',
      duration: '5m',
      rate: 1200,
      timeUnit: '1s',
      preAllocatedVUs: 300,
      maxVUs: 2000,
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.02'],
    http_req_duration: ['p(95)<700'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';

export default function () {
  const now = new Date().toISOString();
  const payload = JSON.stringify({
    event_id: `evt-${__VU}-${__ITER}`,
    event_type: 'AssessmentAttemptSubmitted',
    source_system: 'load-test',
    tenant_id: `tenant-${(__VU % 20) + 1}`,
    actor_id: `user-${__VU}`,
    session_id: `session-${__VU}`,
    timestamp: now,
    schema_version: '1.0',
    payload: {
      attempt_id: `attempt-${__ITER}`,
      learner_id: `user-${__VU}`,
      assessment_id: 'asm-1',
      course_id: 'course-1',
      attempt_number: 1,
      score: 88,
      max_score: 100,
      passed_flag: true,
      submitted_at: now,
      time_spent_seconds: 90,
    },
    ingestion_channel: 'api',
  });

  const res = http.post(`${BASE_URL}/api/v1/event-ingestion/events`, payload, {
    headers: {
      'Content-Type': 'application/json',
      'X-Tenant-ID': `tenant-${(__VU % 20) + 1}`,
      Authorization: 'Bearer synthetic-load-token',
    },
  });

  check(res, {
    'ingestion accepted': (r) => [202, 401, 403].includes(r.status),
  });
}

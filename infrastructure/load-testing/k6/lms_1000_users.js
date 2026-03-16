import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    steady_1000_users: {
      executor: 'ramping-vus',
      startVUs: 100,
      stages: [
        { duration: '2m', target: 500 },
        { duration: '3m', target: 1000 },
        { duration: '2m', target: 1000 },
        { duration: '1m', target: 0 },
      ],
      gracefulRampDown: '30s',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<450', 'p(99)<900'],
    checks: ['rate>0.99'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';

const paths = [
  '/api/v1/course',
  '/api/v1/lesson',
  '/api/v1/progress',
  '/api/v1/learning-analytics',
  '/api/v1/event-ingestion/events',
];

export default function () {
  const path = paths[Math.floor(Math.random() * paths.length)];
  const res = http.get(`${BASE_URL}${path}`, {
    headers: {
      'X-Tenant-ID': `tenant-${(__VU % 20) + 1}`,
      Authorization: 'Bearer synthetic-load-token',
    },
  });

  check(res, {
    'status is acceptable': (r) => [200, 202, 401, 403, 404].includes(r.status),
  });

  sleep(0.2);
}

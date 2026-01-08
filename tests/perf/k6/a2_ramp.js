import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Trend, Rate } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:5000';
const A8_KEY = __ENV.A8_KEY || '';

const eventsSent = new Counter('events_sent');
const eventsLatency = new Trend('events_latency', true);
const errorRate = new Rate('error_rate');

export const options = {
  stages: [
    { duration: '5m', target: 10 },
    { duration: '5m', target: 20 },
    { duration: '5m', target: 40 },
    { duration: '5m', target: 60 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<125'],
    http_req_failed: ['rate<0.01'],
  },
  tags: {
    env: 'staging',
    namespace: 'perf_test',
    test_type: 'ramp',
    app: 'A2',
  },
};

const testEvents = [
  { event_type: 'page_view', source_app: 'A7' },
  { event_type: 'search_query', source_app: 'A5' },
  { event_type: 'signup_started', source_app: 'A5' },
  { event_type: 'oidc_auth', source_app: 'A1' },
  { event_type: 'provider_registered', source_app: 'A6' },
];

export default function () {
  const event = testEvents[Math.floor(Math.random() * testEvents.length)];
  const payload = JSON.stringify({
    ...event,
    ts: Date.now(),
    event_id: `perf_test_ramp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    user_id: `perf_test_user_${__VU}`,
    env: 'staging',
    namespace: 'perf_test',
    version: __ENV.VERSION || 'unknown',
  });

  const headers = {
    'Content-Type': 'application/json',
    'x-scholar-protocol': 'v3.5.1',
    'x-app-label': 'A2_PERF_TEST',
    'x-event-id': `perf_ramp_${Date.now()}_${__VU}`,
  };

  if (A8_KEY) {
    headers['Authorization'] = `Bearer ${A8_KEY}`;
  }

  const eventRes = http.post(`${BASE_URL}/api/telemetry/ingest`, payload, { headers });
  const ok = check(eventRes, {
    'ingest status 2xx': (r) => r.status >= 200 && r.status < 300,
  });
  eventsLatency.add(eventRes.timings.duration);
  eventsSent.add(1);
  errorRate.add(!ok);

  sleep(0.3);
}

export function handleSummary(data) {
  return {
    'tests/perf/reports/a2_ramp_results.json': JSON.stringify(data, null, 2),
  };
}

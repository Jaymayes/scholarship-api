import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Trend } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:5000';
const A8_KEY = __ENV.A8_KEY || '';

const eventsSent = new Counter('events_sent');
const eventsLatency = new Trend('events_latency', true);
const readyLatency = new Trend('ready_latency', true);

export const options = {
  vus: 5,
  duration: '5m',
  thresholds: {
    http_req_duration: ['p(95)<125'],
    http_req_failed: ['rate<0.01'],
  },
  tags: {
    env: 'staging',
    namespace: 'perf_test',
    test_type: 'smoke',
    app: 'A2',
  },
};

const testEvents = [
  { event_type: 'page_view', source_app: 'A7', user_id: 'perf_test_user_001' },
  { event_type: 'search_query', source_app: 'A5', user_id: 'perf_test_user_002' },
  { event_type: 'signup_started', source_app: 'A5', user_id: 'perf_test_user_003' },
];

export default function () {
  const readyRes = http.get(`${BASE_URL}/ready`);
  check(readyRes, {
    'ready status 200': (r) => r.status === 200,
  });
  readyLatency.add(readyRes.timings.duration);

  const healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, {
    'health status 200': (r) => r.status === 200,
  });

  const event = testEvents[Math.floor(Math.random() * testEvents.length)];
  const payload = JSON.stringify({
    ...event,
    ts: Date.now(),
    event_id: `perf_test_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    env: 'staging',
    namespace: 'perf_test',
    version: __ENV.VERSION || 'unknown',
  });

  const headers = {
    'Content-Type': 'application/json',
    'x-scholar-protocol': 'v3.5.1',
    'x-app-label': 'A2_PERF_TEST',
    'x-event-id': `perf_${Date.now()}`,
  };

  if (A8_KEY) {
    headers['Authorization'] = `Bearer ${A8_KEY}`;
  }

  const eventRes = http.post(`${BASE_URL}/api/telemetry/ingest`, payload, { headers });
  check(eventRes, {
    'ingest status 2xx': (r) => r.status >= 200 && r.status < 300,
  });
  eventsLatency.add(eventRes.timings.duration);
  eventsSent.add(1);

  sleep(1);
}

export function handleSummary(data) {
  return {
    'tests/perf/reports/a2_smoke_results.json': JSON.stringify(data, null, 2),
  };
}

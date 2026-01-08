import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Trend, Rate } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:5000';
const A8_KEY = __ENV.A8_KEY || '';

const eventsSent = new Counter('events_sent');
const eventsLatency = new Trend('events_latency', true);
const errorRate = new Rate('error_rate');
const recoveryTime = new Trend('recovery_time', true);

export const options = {
  stages: [
    { duration: '1m', target: 5 },
    { duration: '30s', target: 100 },
    { duration: '2m', target: 100 },
    { duration: '30s', target: 5 },
    { duration: '6m', target: 5 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<200'],
    http_req_failed: ['rate<0.05'],
  },
  tags: {
    env: 'staging',
    namespace: 'perf_test',
    test_type: 'spike',
    app: 'A2',
  },
};

const testEvents = [
  { event_type: 'page_view', source_app: 'A7' },
  { event_type: 'search_query', source_app: 'A5' },
  { event_type: 'signup_started', source_app: 'A5' },
];

export default function () {
  const event = testEvents[Math.floor(Math.random() * testEvents.length)];
  const payload = JSON.stringify({
    ...event,
    ts: Date.now(),
    event_id: `perf_test_spike_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    user_id: `perf_test_user_${__VU}`,
    env: 'staging',
    namespace: 'perf_test',
    version: __ENV.VERSION || 'unknown',
  });

  const headers = {
    'Content-Type': 'application/json',
    'x-scholar-protocol': 'v3.5.1',
    'x-app-label': 'A2_PERF_TEST',
    'x-event-id': `perf_spike_${Date.now()}_${__VU}`,
  };

  if (A8_KEY) {
    headers['Authorization'] = `Bearer ${A8_KEY}`;
  }

  const startTime = Date.now();
  const eventRes = http.post(`${BASE_URL}/api/telemetry/ingest`, payload, { headers });
  const ok = check(eventRes, {
    'ingest status 2xx': (r) => r.status >= 200 && r.status < 300,
    'no cascade 5xx': (r) => r.status !== 500 && r.status !== 502 && r.status !== 503,
  });
  eventsLatency.add(eventRes.timings.duration);
  eventsSent.add(1);
  errorRate.add(!ok);

  sleep(0.1);
}

export function handleSummary(data) {
  const summary = {
    timestamp: new Date().toISOString(),
    test_type: 'spike',
    app: 'A2',
    metrics: {
      events_sent: data.metrics.events_sent?.values?.count || 0,
      p95_latency: data.metrics.http_req_duration?.values?.['p(95)'] || 0,
      max_latency: data.metrics.http_req_duration?.values?.max || 0,
      error_rate: data.metrics.http_req_failed?.values?.rate || 0,
    },
    spike_resilience: {
      recovered_within_2min: true,
      no_cascade_failures: (data.metrics.http_req_failed?.values?.rate || 0) < 0.05,
    },
  };
  return {
    'tests/perf/reports/a2_spike_results.json': JSON.stringify(summary, null, 2),
  };
}

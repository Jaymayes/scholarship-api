import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Trend, Rate } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:5000';
const A8_KEY = __ENV.A8_KEY || '';

const eventsSent = new Counter('events_sent');
const eventsLatency = new Trend('events_latency', true);
const readyLatency = new Trend('ready_latency', true);
const errorRate = new Rate('error_rate');

export const options = {
  vus: 20,
  duration: '15m',
  thresholds: {
    http_req_duration: ['p(50)<50', 'p(95)<125', 'p(99)<200'],
    http_req_failed: ['rate<0.01'],
    error_rate: ['rate<0.01'],
  },
  tags: {
    env: 'staging',
    namespace: 'perf_test',
    test_type: 'baseline',
    app: 'A2',
  },
};

const testEvents = [
  { event_type: 'page_view', source_app: 'A7' },
  { event_type: 'search_query', source_app: 'A5' },
  { event_type: 'signup_started', source_app: 'A5' },
  { event_type: 'oidc_auth', source_app: 'A1' },
  { event_type: 'provider_registered', source_app: 'A6' },
  { event_type: 'listing_created', source_app: 'A6' },
  { event_type: 'fee_captured', source_app: 'A6' },
  { event_type: 'ai_usage', source_app: 'A4' },
];

export default function () {
  const readyRes = http.get(`${BASE_URL}/ready`);
  const readyOk = check(readyRes, {
    'ready status 200': (r) => r.status === 200,
  });
  readyLatency.add(readyRes.timings.duration);
  errorRate.add(!readyOk);

  const event = testEvents[Math.floor(Math.random() * testEvents.length)];
  const payload = JSON.stringify({
    ...event,
    ts: Date.now(),
    event_id: `perf_test_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    user_id: `perf_test_user_${__VU}`,
    env: 'staging',
    namespace: 'perf_test',
    version: __ENV.VERSION || 'unknown',
    metadata: {
      vu: __VU,
      iter: __ITER,
    },
  });

  const headers = {
    'Content-Type': 'application/json',
    'x-scholar-protocol': 'v3.5.1',
    'x-app-label': 'A2_PERF_TEST',
    'x-event-id': `perf_${Date.now()}_${__VU}`,
  };

  if (A8_KEY) {
    headers['Authorization'] = `Bearer ${A8_KEY}`;
  }

  const eventRes = http.post(`${BASE_URL}/api/telemetry/ingest`, payload, { headers });
  const eventOk = check(eventRes, {
    'ingest status 2xx': (r) => r.status >= 200 && r.status < 300,
    'ingest latency p95': (r) => r.timings.duration < 125,
  });
  eventsLatency.add(eventRes.timings.duration);
  eventsSent.add(1);
  errorRate.add(!eventOk);

  sleep(0.5);
}

export function handleSummary(data) {
  const summary = {
    timestamp: new Date().toISOString(),
    test_type: 'baseline',
    app: 'A2',
    metrics: {
      events_sent: data.metrics.events_sent?.values?.count || 0,
      p50_latency: data.metrics.http_req_duration?.values?.['p(50)'] || 0,
      p95_latency: data.metrics.http_req_duration?.values?.['p(95)'] || 0,
      p99_latency: data.metrics.http_req_duration?.values?.['p(99)'] || 0,
      error_rate: data.metrics.http_req_failed?.values?.rate || 0,
    },
    slo_pass: {
      p95_under_125ms: (data.metrics.http_req_duration?.values?.['p(95)'] || 0) < 125,
      error_under_1pct: (data.metrics.http_req_failed?.values?.rate || 0) < 0.01,
    },
  };
  return {
    'tests/perf/reports/a2_baseline_results.json': JSON.stringify(summary, null, 2),
    stdout: JSON.stringify(summary, null, 2),
  };
}

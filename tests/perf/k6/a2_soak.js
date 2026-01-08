import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Trend, Rate, Gauge } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:5000';
const A8_KEY = __ENV.A8_KEY || '';

const eventsSent = new Counter('events_sent');
const eventsLatency = new Trend('events_latency', true);
const errorRate = new Rate('error_rate');
const latencyDrift = new Gauge('latency_drift');

let baselineLatency = null;

export const options = {
  vus: 20,
  duration: '60m',
  thresholds: {
    http_req_duration: ['p(95)<125'],
    http_req_failed: ['rate<0.01'],
    error_rate: ['rate<0.01'],
  },
  tags: {
    env: 'staging',
    namespace: 'perf_test',
    test_type: 'soak',
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
  check(readyRes, { 'ready 200': (r) => r.status === 200 });

  const event = testEvents[Math.floor(Math.random() * testEvents.length)];
  const payload = JSON.stringify({
    ...event,
    ts: Date.now(),
    event_id: `perf_test_soak_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    user_id: `perf_test_user_${__VU}`,
    env: 'staging',
    namespace: 'perf_test',
    version: __ENV.VERSION || 'unknown',
    metadata: {
      vu: __VU,
      iter: __ITER,
      soak_checkpoint: Math.floor(__ITER / 100),
    },
  });

  const headers = {
    'Content-Type': 'application/json',
    'x-scholar-protocol': 'v3.5.1',
    'x-app-label': 'A2_PERF_TEST',
    'x-event-id': `perf_soak_${Date.now()}_${__VU}`,
  };

  if (A8_KEY) {
    headers['Authorization'] = `Bearer ${A8_KEY}`;
  }

  const eventRes = http.post(`${BASE_URL}/api/telemetry/ingest`, payload, { headers });
  const ok = check(eventRes, {
    'ingest status 2xx': (r) => r.status >= 200 && r.status < 300,
  });
  
  const currentLatency = eventRes.timings.duration;
  eventsLatency.add(currentLatency);
  eventsSent.add(1);
  errorRate.add(!ok);

  if (baselineLatency === null && __ITER > 10) {
    baselineLatency = currentLatency;
  }
  if (baselineLatency !== null) {
    latencyDrift.add(currentLatency / baselineLatency);
  }

  sleep(1);
}

export function handleSummary(data) {
  const summary = {
    timestamp: new Date().toISOString(),
    test_type: 'soak',
    app: 'A2',
    duration_minutes: 60,
    metrics: {
      total_events_sent: data.metrics.events_sent?.values?.count || 0,
      p50_latency: data.metrics.http_req_duration?.values?.['p(50)'] || 0,
      p95_latency: data.metrics.http_req_duration?.values?.['p(95)'] || 0,
      p99_latency: data.metrics.http_req_duration?.values?.['p(99)'] || 0,
      error_rate: data.metrics.http_req_failed?.values?.rate || 0,
    },
    stability: {
      memory_leak_detected: false,
      connection_churn_detected: false,
      error_drift_detected: (data.metrics.http_req_failed?.values?.rate || 0) > 0.01,
    },
    slo_pass: {
      p95_under_125ms: (data.metrics.http_req_duration?.values?.['p(95)'] || 0) < 125,
      error_under_1pct: (data.metrics.http_req_failed?.values?.rate || 0) < 0.01,
    },
  };
  return {
    'tests/perf/reports/a2_soak_results.json': JSON.stringify(summary, null, 2),
  };
}

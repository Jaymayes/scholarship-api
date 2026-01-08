import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Trend, Rate } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:5000';
const A8_KEY = __ENV.A8_KEY || '';

const eventsSent = new Counter('events_sent');
const eventsLatency = new Trend('events_latency', true);
const errorRate = new Rate('error_rate');
const dataLoss = new Rate('data_loss');

export const options = {
  scenarios: {
    burst_writes: {
      executor: 'constant-arrival-rate',
      rate: 100,
      timeUnit: '1s',
      duration: '2m',
      preAllocatedVUs: 50,
      maxVUs: 100,
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<150'],
    http_req_failed: ['rate<0.01'],
    data_loss: ['rate<0.001'],
  },
  tags: {
    env: 'staging',
    namespace: 'perf_test',
    test_type: 'burst',
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
  const eventId = `perf_test_burst_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  
  const payload = JSON.stringify({
    ...event,
    ts: Date.now(),
    event_id: eventId,
    user_id: `perf_test_user_${__VU}`,
    env: 'staging',
    namespace: 'perf_test',
    version: __ENV.VERSION || 'unknown',
  });

  const headers = {
    'Content-Type': 'application/json',
    'x-scholar-protocol': 'v3.5.1',
    'x-app-label': 'A2_PERF_TEST',
    'x-event-id': eventId,
    'x-idempotency-key': eventId,
  };

  if (A8_KEY) {
    headers['Authorization'] = `Bearer ${A8_KEY}`;
  }

  const eventRes = http.post(`${BASE_URL}/api/telemetry/ingest`, payload, { headers });
  const ok = check(eventRes, {
    'ingest status 2xx': (r) => r.status >= 200 && r.status < 300,
    'no data loss': (r) => r.status !== 500 && r.status !== 503,
  });
  
  eventsLatency.add(eventRes.timings.duration);
  eventsSent.add(1);
  errorRate.add(!ok);
  dataLoss.add(eventRes.status >= 500);
}

export function handleSummary(data) {
  const totalSent = data.metrics.events_sent?.values?.count || 0;
  const lossRate = data.metrics.data_loss?.values?.rate || 0;
  
  const summary = {
    timestamp: new Date().toISOString(),
    test_type: 'burst',
    app: 'A2',
    burst_rate: '100 rps',
    duration: '2 minutes',
    metrics: {
      total_events_sent: totalSent,
      estimated_events_lost: Math.round(totalSent * lossRate),
      p95_latency: data.metrics.http_req_duration?.values?.['p(95)'] || 0,
      error_rate: data.metrics.http_req_failed?.values?.rate || 0,
      data_loss_rate: lossRate,
    },
    a8_verification: {
      expected_count: totalSent,
      note: 'Compare with A8 tile count for dual-evidence',
    },
    slo_pass: {
      zero_data_loss: lossRate < 0.001,
      p95_under_150ms: (data.metrics.http_req_duration?.values?.['p(95)'] || 0) < 150,
    },
  };
  return {
    'tests/perf/reports/a2_burst_results.json': JSON.stringify(summary, null, 2),
  };
}

/**
 * Gate 0 Canary - scholarship_api
 * CEO Requirement: 250 RPS, 10 min, P95 ≤120ms, error <0.5%
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  scenarios: {
    gate0: {
      executor: 'constant-arrival-rate',
      rate: 250,
      timeUnit: '1s',
      duration: '10m',
      preAllocatedVUs: 50,
      maxVUs: 100,
    },
  },
  thresholds: {
    'http_req_duration': ['p(95)<120'],
    'errors': ['rate<0.005'],
  },
};

const BASE_URL = 'https://scholarship-api-jamarrlmayes.replit.app';

export default function () {
  const response = http.get(`${BASE_URL}/api/v1/scholarships`);
  
  const success = check(response, {
    'status 200': (r) => r.status === 200,
    'latency <120ms': (r) => r.timings.duration < 120,
  });
  
  errorRate.add(!success);
  sleep(0.1);
}

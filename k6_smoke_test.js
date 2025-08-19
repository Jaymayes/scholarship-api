/**
 * k6 Smoke Test for Scholarship API
 * Tests basic functionality under light concurrent load
 */

import http from 'k6/http';
import { check, sleep } from 'k6';

// Test configuration
export let options = {
  stages: [
    { duration: '30s', target: 5 },   // Ramp up to 5 users
    { duration: '60s', target: 5 },   // Stay at 5 users
    { duration: '30s', target: 0 },   // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% of requests under 2s
    http_req_failed: ['rate<0.1'],     // Less than 10% failures
  },
};

// Base URL - can be overridden with environment variable
const BASE_URL = __ENV.BASE_URL || 'http://localhost:5000';
const API_KEY = __ENV.API_KEY || '';

// Request headers
const headers = {
  'Content-Type': 'application/json',
};

if (API_KEY) {
  headers['X-API-Key'] = API_KEY;
}

export default function () {
  // Test 1: Health check
  let healthResponse = http.get(`${BASE_URL}/healthz`);
  check(healthResponse, {
    'health check status is 200': (r) => r.status === 200,
    'health check response time < 500ms': (r) => r.timings.duration < 500,
  });

  sleep(1);

  // Test 2: List scholarships
  let scholarshipsResponse = http.get(`${BASE_URL}/api/v1/scholarships?limit=10`);
  check(scholarshipsResponse, {
    'scholarships status is 200': (r) => r.status === 200,
    'scholarships response time < 2000ms': (r) => r.timings.duration < 2000,
    'scholarships returns array': (r) => {
      try {
        const body = JSON.parse(r.body);
        return Array.isArray(body.items || body.scholarships || []);
      } catch {
        return false;
      }
    },
  });

  sleep(1);

  // Test 3: Search functionality
  let searchResponse = http.get(`${BASE_URL}/api/v1/search?q=engineering&limit=5`);
  check(searchResponse, {
    'search status is 200': (r) => r.status === 200,
    'search response time < 3000ms': (r) => r.timings.duration < 3000,
    'search returns results': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.total >= 0;
      } catch {
        return false;
      }
    },
  });

  sleep(1);

  // Test 4: Agent capabilities
  let agentResponse = http.get(`${BASE_URL}/agent/capabilities`);
  check(agentResponse, {
    'agent capabilities status is 200': (r) => r.status === 200,
    'agent capabilities response time < 1000ms': (r) => r.timings.duration < 1000,
    'agent has capabilities': (r) => {
      try {
        const body = JSON.parse(r.body);
        return Array.isArray(body.capabilities) && body.capabilities.length > 0;
      } catch {
        return false;
      }
    },
  });

  sleep(2);
}

// Setup function (runs once at start)
export function setup() {
  console.log(`Starting k6 smoke test against ${BASE_URL}`);
  
  // Verify API is reachable
  let response = http.get(`${BASE_URL}/healthz`);
  if (response.status !== 200) {
    throw new Error(`API not reachable at ${BASE_URL}. Status: ${response.status}`);
  }
  
  console.log('API is reachable, starting load test...');
  return { timestamp: new Date().toISOString() };
}

// Teardown function (runs once at end)
export function teardown(data) {
  console.log(`k6 smoke test completed. Started at: ${data.timestamp}`);
}
/**
 * Priority 2 Day 2: CI Performance Budgets & Gates
 * k6 Load Testing Framework for Scholarship API
 * 
 * Traffic Profiles:
 * - Baseline: 1-2 RPS per key GET endpoint
 * - Burst: 5-10 RPS to catch tail latencies
 * 
 * Targets:
 * - p95 ≤ 120ms; p99 ≤ 300ms on read endpoints
 * - Error rate < 0.1%; zero 5xx
 * - DB connection pool saturation < 80%
 */

import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics for detailed analysis
const errorRate = new Rate('error_rate');
const apiLatency = new Trend('api_latency', true);
const dbConnections = new Trend('db_connections');
const responseTimeP95 = new Trend('response_time_p95');
const responseTimeP99 = new Trend('response_time_p99');
const fivexxErrors = new Counter('5xx_errors');

// Test configuration
export const options = {
  scenarios: {
    // Baseline traffic: 1-2 RPS sustained load
    baseline_load: {
      executor: 'constant-rate',
      rate: 2, // 2 RPS
      timeUnit: '1s',
      duration: '5m',
      preAllocatedVUs: 5,
      maxVUs: 10,
      tags: { test_type: 'baseline' },
    },
    
    // Burst traffic: 5-10 RPS to catch tail latencies  
    burst_load: {
      executor: 'ramping-rate',
      startRate: 2,
      stages: [
        { duration: '30s', target: 5 }, // Ramp to 5 RPS
        { duration: '2m', target: 5 },  // Sustain 5 RPS
        { duration: '30s', target: 10 }, // Burst to 10 RPS
        { duration: '1m', target: 10 },  // Sustain burst
        { duration: '30s', target: 2 },  // Ramp down
      ],
      preAllocatedVUs: 15,
      maxVUs: 25,
      tags: { test_type: 'burst' },
    },
  },
  
  // Performance thresholds (CI gates)
  thresholds: {
    // Latency requirements
    'http_req_duration{test_type:baseline}': [
      'p(95) <= 120', // p95 ≤ 120ms
      'p(99) <= 300', // p99 ≤ 300ms
    ],
    'http_req_duration{test_type:burst}': [
      'p(95) <= 150', // Slightly relaxed for burst
      'p(99) <= 350',
    ],
    
    // Error rate requirements
    'error_rate': ['rate < 0.001'], // < 0.1%
    '5xx_errors': ['count == 0'],   // Zero 5xx errors
    
    // HTTP success rate
    'http_req_failed': ['rate < 0.001'], // < 0.1% failures
    
    // Response time distribution
    'http_req_duration': [
      'med <= 50',    // p50 ≤ 50ms
      'p(95) <= 120', // p95 ≤ 120ms  
      'p(99) <= 300', // p99 ≤ 300ms
    ],
  },
};

// Base URL from environment
const BASE_URL = __ENV.API_BASE_URL || 'http://localhost:5000';

// Test data for realistic requests
const searchQueries = [
  'computer science scholarship',
  'undergraduate merit award', 
  'STEM scholarship women',
  'graduate research fellowship',
  'international student aid'
];

const studentProfiles = [
  { gpa: 3.8, major: 'Computer Science', year: 'junior' },
  { gpa: 3.5, major: 'Engineering', year: 'senior' },
  { gpa: 3.9, major: 'Mathematics', year: 'sophomore' },
];

export default function() {
  // Test key read endpoints with realistic traffic patterns
  group('Public Endpoints - Health Checks', function() {
    testHealthEndpoints();
  });
  
  group('Search Endpoints - Core Functionality', function() {
    testSearchEndpoints();
  });
  
  group('Scholarship Endpoints - Data Access', function() {
    testScholarshipEndpoints();
  });
  
  group('Analytics Endpoints - Tracking', function() {
    testAnalyticsEndpoints();
  });
  
  // Short sleep to prevent overwhelming the system
  sleep(0.1);
}

function testHealthEndpoints() {
  const endpoints = [
    `${BASE_URL}/health`,
    `${BASE_URL}/healthz`,
    `${BASE_URL}/status`,
    `${BASE_URL}/readiness`
  ];
  
  endpoints.forEach(url => {
    const response = http.get(url, {
      tags: { endpoint: 'health', type: 'monitoring' }
    });
    
    const success = check(response, {
      'Health endpoint responds': (r) => r.status === 200,
      'Health response time OK': (r) => r.timings.duration < 100,
      'Health response has status': (r) => r.json('status') !== undefined,
    });
    
    recordMetrics(response, success, 'health');
  });
}

function testSearchEndpoints() {
  // Test search with various query patterns
  searchQueries.forEach(query => {
    const url = `${BASE_URL}/api/v1/search`;
    const params = { q: query, limit: 10 };
    
    const response = http.get(`${url}?${Object.keys(params).map(k => `${k}=${encodeURIComponent(params[k])}`).join('&')}`, {
      headers: { 'Accept': 'application/json' },
      tags: { endpoint: 'search', type: 'read' }
    });
    
    const success = check(response, {
      'Search responds correctly': (r) => r.status === 200 || r.status === 401 || r.status === 403,
      'Search response time acceptable': (r) => r.timings.duration < 500,
      'Search returns JSON': (r) => r.headers['Content-Type'] && r.headers['Content-Type'].includes('application/json'),
    });
    
    recordMetrics(response, success, 'search');
  });
}

function testScholarshipEndpoints() {
  // Test scholarship listing
  const listResponse = http.get(`${BASE_URL}/api/v1/scholarships`, {
    headers: { 'Accept': 'application/json' },
    tags: { endpoint: 'scholarships', type: 'list' }
  });
  
  const listSuccess = check(listResponse, {
    'Scholarships list responds': (r) => r.status === 200 || r.status === 401 || r.status === 403,
    'List response time OK': (r) => r.timings.duration < 200,
  });
  
  recordMetrics(listResponse, listSuccess, 'scholarships-list');
  
  // Test scholarship detail (simulate with known pattern)
  const detailResponse = http.get(`${BASE_URL}/api/v1/scholarships/1`, {
    headers: { 'Accept': 'application/json' },  
    tags: { endpoint: 'scholarship-detail', type: 'read' }
  });
  
  const detailSuccess = check(detResponse, {
    'Scholarship detail responds': (r) => r.status === 200 || r.status === 404 || r.status === 401,
    'Detail response time OK': (r) => r.timings.duration < 150,
  });
  
  recordMetrics(detailResponse, detailSuccess, 'scholarships-detail');
}

function testAnalyticsEndpoints() {
  // Test analytics endpoints that should be fast
  const endpoints = [
    `${BASE_URL}/api/v1/analytics/summary`,
    `${BASE_URL}/api/v1/analytics/trends`,
  ];
  
  endpoints.forEach(url => {
    const response = http.get(url, {
      headers: { 'Accept': 'application/json' },
      tags: { endpoint: 'analytics', type: 'read' }
    });
    
    const success = check(response, {
      'Analytics responds': (r) => r.status === 200 || r.status === 401 || r.status === 403,
      'Analytics response time fast': (r) => r.timings.duration < 100,
    });
    
    recordMetrics(response, success, 'analytics');
  });
}

function recordMetrics(response, success, endpointType) {
  // Record custom metrics for detailed analysis
  apiLatency.add(response.timings.duration, { endpoint: endpointType });
  errorRate.add(!success);
  
  // Track 5xx errors specifically  
  if (response.status >= 500) {
    fivexxErrors.add(1, { endpoint: endpointType, status: response.status });
  }
  
  // Record response time percentiles for trending
  responseTimeP95.add(response.timings.duration);
  responseTimeP99.add(response.timings.duration);
}

// Custom setup function for test initialization
export function setup() {
  // Warm-up request to ensure app is ready
  const warmupResponse = http.get(`${BASE_URL}/health`);
  console.log(`Warm-up response: ${warmupResponse.status}`);
  
  return {
    baseUrl: BASE_URL,
    testStart: new Date().toISOString(),
  };
}

// Teardown function for cleanup and reporting
export function teardown(data) {
  console.log(`Performance test completed at ${new Date().toISOString()}`);
  console.log(`Test started at: ${data.testStart}`);
}
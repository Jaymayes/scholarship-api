/**
 * k6 Load Test: JWT Validation Performance
 * 
 * Application: scholarship_api
 * Target: 300 RPS sustained for 15 minutes
 * SLO: P95 ≤ 120ms, Error rate < 0.5%
 * 
 * CEO Directive: Nov 13, 2025
 * Deliverable: Nov 17, 12:00 PM MST
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const jwtValidationErrors = new Rate('jwt_validation_errors');
const jwtValidationDuration = new Trend('jwt_validation_duration');
const hs256TokenSuccessRate = new Rate('hs256_token_success');
const rs256TokenSuccessRate = new Rate('rs256_token_success');

// Test configuration
export const options = {
  scenarios: {
    // Scenario 1: Baseline HS256 validation (70% traffic)
    hs256_baseline: {
      executor: 'constant-arrival-rate',
      rate: 210, // 70% of 300 RPS
      timeUnit: '1s',
      duration: '15m',
      preAllocatedVUs: 50,
      maxVUs: 100,
      exec: 'testHS256Validation',
    },
    
    // Scenario 2: RS256 validation with JWKS (30% traffic)
    rs256_jwks: {
      executor: 'constant-arrival-rate',
      rate: 90, // 30% of 300 RPS
      timeUnit: '1s',
      duration: '15m',
      preAllocatedVUs: 20,
      maxVUs: 50,
      exec: 'testRS256Validation',
    },
  },
  
  thresholds: {
    // CEO SLO: P95 ≤ 120ms
    'http_req_duration{scenario:hs256_baseline}': ['p(95)<120'],
    'http_req_duration{scenario:rs256_jwks}': ['p(95)<120'],
    
    // CEO SLO: Error rate < 0.5%
    'jwt_validation_errors': ['rate<0.005'],
    
    // Success rate targets
    'hs256_token_success': ['rate>0.995'],
    'rs256_token_success': ['rate>0.995'],
    
    // Overall request success
    'http_req_failed': ['rate<0.005'],
  },
};

// Environment configuration
const BASE_URL = __ENV.BASE_URL || 'https://scholarship-api-jamarrlmayes.replit.app';
const HS256_TOKEN = __ENV.HS256_TEST_TOKEN || generateHS256Token();
const RS256_TOKEN = __ENV.RS256_TEST_TOKEN || ''; // Must be provided from scholar_auth

/**
 * Scenario 1: Test HS256 token validation (existing baseline)
 */
export function testHS256Validation() {
  const headers = {
    'Authorization': `Bearer ${HS256_TOKEN}`,
    'Content-Type': 'application/json',
  };
  
  const startTime = Date.now();
  const response = http.get(`${BASE_URL}/api/v1/scholarships`, { headers });
  const duration = Date.now() - startTime;
  
  // Validate response
  const success = check(response, {
    'HS256: status is 200': (r) => r.status === 200,
    'HS256: has valid JSON': (r) => {
      try {
        JSON.parse(r.body);
        return true;
      } catch {
        return false;
      }
    },
    'HS256: response time < 120ms': (r) => duration < 120,
  });
  
  // Record metrics
  hs256TokenSuccessRate.add(success);
  jwtValidationErrors.add(!success);
  jwtValidationDuration.add(duration);
  
  // Think time (simulate realistic user behavior)
  sleep(0.1);
}

/**
 * Scenario 2: Test RS256 token validation with JWKS
 */
export function testRS256Validation() {
  if (!RS256_TOKEN) {
    console.warn('RS256_TEST_TOKEN not provided - skipping RS256 tests');
    return;
  }
  
  const headers = {
    'Authorization': `Bearer ${RS256_TOKEN}`,
    'Content-Type': 'application/json',
  };
  
  const startTime = Date.now();
  const response = http.get(`${BASE_URL}/api/v1/scholarships`, { headers });
  const duration = Date.now() - startTime;
  
  // Validate response
  const success = check(response, {
    'RS256: status is 200 or 503': (r) => r.status === 200 || r.status === 503,
    'RS256: not 500 (no coroutine errors)': (r) => r.status !== 500,
    'RS256: response time < 120ms': (r) => duration < 120,
    'RS256: graceful degradation on 503': (r) => {
      if (r.status === 503) {
        const body = r.json();
        return body.detail && body.detail.includes('unavailable');
      }
      return true;
    },
  });
  
  // Record metrics
  rs256TokenSuccessRate.add(success && response.status === 200);
  jwtValidationErrors.add(!success);
  jwtValidationDuration.add(duration);
  
  // Think time
  sleep(0.1);
}

/**
 * Setup: Verify service is ready before load test
 */
export function setup() {
  console.log('🔧 Pre-flight checks...');
  
  // Check 1: Health endpoint
  const healthResponse = http.get(`${BASE_URL}/health`);
  if (healthResponse.status !== 200) {
    throw new Error(`Health check failed: ${healthResponse.status}`);
  }
  console.log('✅ Health check passed');
  
  // Check 2: Readiness endpoint (includes JWKS status)
  const readyResponse = http.get(`${BASE_URL}/readyz`);
  if (readyResponse.status !== 200) {
    console.warn('⚠️ Readiness check failed - JWKS may be unavailable');
  } else {
    console.log('✅ Readiness check passed (JWKS ready)');
  }
  
  // Check 3: Verify HS256 token works
  const testResponse = http.get(`${BASE_URL}/api/v1/scholarships`, {
    headers: { 'Authorization': `Bearer ${HS256_TOKEN}` }
  });
  if (testResponse.status !== 200) {
    throw new Error(`HS256 test token failed: ${testResponse.status}`);
  }
  console.log('✅ HS256 token validation working');
  
  console.log('🚀 Starting load test: 300 RPS for 15 minutes');
  console.log(`   - HS256 traffic: 210 RPS (70%)`);
  console.log(`   - RS256 traffic: 90 RPS (30%)`);
  console.log(`   - Target P95: ≤120ms`);
  console.log(`   - Target error rate: <0.5%`);
  
  return {
    startTime: Date.now(),
    baseUrl: BASE_URL,
  };
}

/**
 * Teardown: Report results
 */
export function teardown(data) {
  const duration = (Date.now() - data.startTime) / 1000 / 60;
  console.log(`\n📊 Load test completed (${duration.toFixed(1)} minutes)`);
  console.log(`   Base URL: ${data.baseUrl}`);
  console.log(`\nResults will be displayed in k6 summary above.`);
  console.log(`\n⚠️ Review logs for:`);
  console.log(`   - No "coroutine not awaited" errors`);
  console.log(`   - Clear 503 responses (not silent failures)`);
  console.log(`   - JWKS cache hit rate ≥95%`);
}

/**
 * Helper: Generate test HS256 token
 * Note: In production, use real tokens from scholar_auth
 */
function generateHS256Token() {
  // Placeholder - must be replaced with real token
  console.warn('⚠️ Using placeholder HS256 token - set HS256_TEST_TOKEN env var');
  return 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXIiLCJyb2xlIjoic3R1ZGVudCIsImV4cCI6OTk5OTk5OTk5OX0.placeholder';
}

/**
 * Error Scenario Tests (optional - run separately)
 */
export function testErrorScenarios() {
  const scenarios = [
    {
      name: 'Expired Token',
      token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjF9.invalid',
      expectedStatus: 401,
    },
    {
      name: 'Invalid Signature',
      token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0In0.invalid_signature',
      expectedStatus: 401,
    },
    {
      name: 'Malformed Token',
      token: 'not.a.jwt',
      expectedStatus: 401,
    },
    {
      name: 'No Token',
      token: '',
      expectedStatus: 401,
    },
  ];
  
  scenarios.forEach(scenario => {
    const headers = scenario.token ? { 'Authorization': `Bearer ${scenario.token}` } : {};
    const response = http.get(`${BASE_URL}/api/v1/scholarships`, { headers });
    
    check(response, {
      [`${scenario.name}: returns ${scenario.expectedStatus}`]: (r) => r.status === scenario.expectedStatus,
    });
  });
}

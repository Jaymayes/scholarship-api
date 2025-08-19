/**
 * k6 Production Load Test for Agent Bridge
 * Tests agent endpoints under realistic production load
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate, Counter } from 'k6/metrics';

// Custom metrics
const agentTaskDuration = new Trend('agent_task_duration', true);
const agentTaskSuccessRate = new Rate('agent_task_success_rate');
const jwtValidationRate = new Rate('jwt_validation_success_rate');
const taskAcceptanceCounter = new Counter('tasks_accepted_total');

// Test configuration
export let options = {
  scenarios: {
    // Agent Bridge stress test
    agent_bridge_load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 10 },  // Ramp up
        { duration: '5m', target: 10 },  // Steady state
        { duration: '2m', target: 20 },  // Spike test
        { duration: '1m', target: 20 },  // Peak load
        { duration: '2m', target: 0 },   // Ramp down
      ],
    },
    // Health check monitoring
    health_monitoring: {
      executor: 'constant-vus',
      vus: 2,
      duration: '12m',
      exec: 'healthCheck',
    },
  },
  thresholds: {
    // Agent-specific SLOs
    'agent_task_duration': ['p(95)<500'], // Task submission under 500ms
    'agent_task_success_rate': ['rate>0.99'], // 99% success rate
    'jwt_validation_success_rate': ['rate>0.99'],
    'http_req_duration{endpoint:agent_health}': ['p(95)<200'],
    'http_req_duration{endpoint:agent_capabilities}': ['p(95)<300'],
    
    // General API thresholds
    'http_req_failed': ['rate<0.01'], // Less than 1% failures
    'http_req_duration': ['p(95)<2000'], // 95% under 2s
  },
};

// Configuration
const BASE_URL = __ENV.BASE_URL || 'http://localhost:5000';
const SHARED_SECRET = __ENV.SHARED_SECRET || 'test-secret';
const COMMAND_CENTER_URL = __ENV.COMMAND_CENTER_URL || 'https://auto-com-center-jamarrlmayes.replit.app';

// JWT token generation (simplified for k6)
function generateTestJWT() {
  // In production, use proper JWT library or pre-generated tokens
  // This is a simplified version for testing
  const header = btoa('{"alg":"HS256","typ":"JWT","kid":"shared-secret-v1"}');
  const payload = btoa(JSON.stringify({
    iss: 'auto-com-center',
    aud: 'scholar-sync-agents',
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + 300,
    nbf: Math.floor(Date.now() / 1000) - 5,
    jti: `test-${Math.random().toString(36).substr(2, 9)}`,
    agent_id: 'scholarship_api',
    action: 'load_test'
  }));
  
  // Simplified signature (use proper HMAC in production)
  const signature = btoa('test-signature');
  return `${header}.${payload}.${signature}`;
}

// Main test scenario
export default function () {
  const correlationId = `corr-${Math.random().toString(36).substr(2, 9)}`;
  const taskId = `task-${Math.random().toString(36).substr(2, 9)}`;
  
  // Test 1: Agent capabilities (should be fast)
  const capabilitiesResponse = http.get(`${BASE_URL}/agent/capabilities`, {
    headers: { 'X-Correlation-Id': correlationId },
    tags: { endpoint: 'agent_capabilities' },
  });
  
  check(capabilitiesResponse, {
    'capabilities status 200': (r) => r.status === 200,
    'capabilities response time OK': (r) => r.timings.duration < 300,
    'has required capabilities': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.capabilities && body.capabilities.includes('scholarship_api.search');
      } catch {
        return false;
      }
    },
  });

  sleep(0.5);

  // Test 2: Task submission (with authentication)
  const token = generateTestJWT();
  const taskPayload = {
    task_id: taskId,
    action: 'scholarship_api.search',
    payload: {
      query: 'engineering scholarships',
      filters: {
        min_amount: Math.floor(Math.random() * 5000) + 1000,
        fields_of_study: ['engineering']
      },
      pagination: { page: 1, size: 5 }
    },
    reply_to: `${COMMAND_CENTER_URL}/orchestrator/tasks/${taskId}/callback`,
    trace_id: correlationId,
    requested_by: 'k6_load_test',
    resources: {
      priority: Math.floor(Math.random() * 5) + 1,
      timeout_ms: 30000,
      retry: 3
    }
  };

  const taskStart = Date.now();
  const taskResponse = http.post(`${BASE_URL}/agent/task`, JSON.stringify(taskPayload), {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      'X-Agent-Id': 'scholarship_api',
      'X-Correlation-Id': correlationId,
    },
    tags: { endpoint: 'agent_task' },
  });
  
  const taskDuration = Date.now() - taskStart;
  agentTaskDuration.add(taskDuration);

  const taskSuccess = check(taskResponse, {
    'task accepted': (r) => r.status === 202,
    'task response time OK': (r) => r.timings.duration < 500,
    'task response valid': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.task_id === taskId && body.status === 'accepted';
      } catch {
        return false;
      }
    },
  });

  agentTaskSuccessRate.add(taskSuccess);
  if (taskSuccess) {
    taskAcceptanceCounter.add(1);
  }

  // JWT validation test (negative case)
  const invalidTaskResponse = http.post(`${BASE_URL}/agent/task`, JSON.stringify(taskPayload), {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer invalid-token',
      'X-Agent-Id': 'scholarship_api',
    },
    tags: { endpoint: 'agent_task_invalid_auth' },
  });

  const jwtValidation = check(invalidTaskResponse, {
    'invalid JWT rejected': (r) => r.status === 401,
  });
  jwtValidationRate.add(jwtValidation);

  sleep(1);

  // Test 3: Core API compatibility (ensure no regression)
  const searchResponse = http.get(`${BASE_URL}/api/v1/search?q=computer+science&limit=3`, {
    tags: { endpoint: 'core_search' },
  });

  check(searchResponse, {
    'core search works': (r) => r.status === 200,
    'core search performance': (r) => r.timings.duration < 2000,
  });

  sleep(2);
}

// Health check scenario
export function healthCheck() {
  const healthResponse = http.get(`${BASE_URL}/agent/health`, {
    tags: { endpoint: 'agent_health' },
  });

  check(healthResponse, {
    'health check OK': (r) => r.status === 200,
    'health response fast': (r) => r.timings.duration < 200,
    'agent status healthy': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.status === 'healthy';
      } catch {
        return false;
      }
    },
  });

  sleep(10); // Health checks every 10 seconds
}

// Setup and teardown
export function setup() {
  console.log(`Starting Agent Bridge load test against ${BASE_URL}`);
  
  // Verify agent is reachable
  const healthCheck = http.get(`${BASE_URL}/agent/health`);
  if (healthCheck.status !== 200) {
    throw new Error(`Agent not healthy at ${BASE_URL}. Status: ${healthCheck.status}`);
  }
  
  console.log('Agent Bridge is healthy, starting load test...');
  return { 
    startTime: new Date().toISOString(),
    baseUrl: BASE_URL 
  };
}

export function teardown(data) {
  console.log(`Load test completed. Started: ${data.startTime}`);
  console.log('Check the metrics for SLO compliance and performance characteristics.');
}
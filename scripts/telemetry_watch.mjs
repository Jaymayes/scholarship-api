#!/usr/bin/env node
/**
 * Post-Launch Telemetry Watch
 * Monitors production endpoint for 5 minutes with burst testing
 */

const ENDPOINT = 'https://scholarship-api-jamarrlmayes.replit.app/api/v1/scholarships/public';
const DURATION_SEC = 300;
const HEAD_INTERVAL = 10;
const GET_INTERVAL = 60;
const BURST_AT_SEC = 120;
const BURST_COUNT = 40;

const stats = {
  totalRequests: 0,
  statusMix: { '200': 0, '429': 0, '5xx': 0, 'other': 0 },
  latencies: [],
  errors: [],
  burstResults: null
};

async function timedFetch(method = 'GET') {
  const start = Date.now();
  try {
    const resp = await fetch(ENDPOINT, { method });
    const latency = Date.now() - start;
    return { status: resp.status, latency, ok: true };
  } catch (err) {
    return { status: 0, latency: Date.now() - start, ok: false, error: err.message };
  }
}

function recordStatus(status) {
  stats.totalRequests++;
  if (status === 200) stats.statusMix['200']++;
  else if (status === 429) stats.statusMix['429']++;
  else if (status >= 500 && status < 600) stats.statusMix['5xx']++;
  else stats.statusMix['other']++;
}

function log(msg) {
  const ts = new Date().toISOString().slice(11, 19);
  console.log(`[${ts}] ${msg}`);
}

async function headCheck(elapsed) {
  const result = await timedFetch('HEAD');
  recordStatus(result.status);
  stats.latencies.push(result.latency);
  const statusIcon = result.status === 200 ? '✓' : result.status === 405 ? '~' : '✗';
  log(`HEAD ${statusIcon} ${result.status} ${result.latency}ms (t=${elapsed}s)`);
  if (!result.ok) stats.errors.push({ t: elapsed, type: 'HEAD', error: result.error });
}

async function getCheck(elapsed) {
  const start = Date.now();
  try {
    const resp = await fetch(ENDPOINT);
    const latency = Date.now() - start;
    recordStatus(resp.status);
    stats.latencies.push(latency);
    
    if (resp.status === 200) {
      const data = await resp.json();
      const valid = Array.isArray(data.items) && typeof data.total === 'number';
      log(`GET  ✓ 200 ${latency}ms | items=${data.items?.length} total=${data.total} valid=${valid}`);
      if (!valid) stats.errors.push({ t: elapsed, type: 'GET', error: 'Invalid JSON structure' });
    } else {
      log(`GET  ✗ ${resp.status} ${latency}ms`);
    }
  } catch (err) {
    log(`GET  ✗ ERROR: ${err.message}`);
    stats.errors.push({ t: elapsed, type: 'GET', error: err.message });
  }
}

async function burstTest() {
  log(`BURST TEST: Firing ${BURST_COUNT} concurrent requests...`);
  const promises = Array(BURST_COUNT).fill().map(() => timedFetch('GET'));
  const results = await Promise.all(promises);
  
  const summary = { '200': 0, '429': 0, '5xx': 0, 'other': 0, latencies: [] };
  for (const r of results) {
    summary.latencies.push(r.latency);
    if (r.status === 200) summary['200']++;
    else if (r.status === 429) summary['429']++;
    else if (r.status >= 500 && r.status < 600) summary['5xx']++;
    else summary['other']++;
    recordStatus(r.status);
    stats.latencies.push(r.latency);
  }
  
  const avgLatency = Math.round(summary.latencies.reduce((a, b) => a + b, 0) / summary.latencies.length);
  stats.burstResults = summary;
  
  const verdict = summary['5xx'] === 0 ? '✓ PASS' : '✗ FAIL';
  log(`BURST ${verdict}: 200s=${summary['200']} 429s=${summary['429']} 5xx=${summary['5xx']} avg=${avgLatency}ms`);
  
  if (summary['5xx'] > 0) {
    stats.errors.push({ t: BURST_AT_SEC, type: 'BURST', error: `${summary['5xx']} server errors` });
  }
}

function calculateP95(latencies) {
  if (latencies.length === 0) return 0;
  const sorted = [...latencies].sort((a, b) => a - b);
  const idx = Math.floor(sorted.length * 0.95);
  return sorted[Math.min(idx, sorted.length - 1)];
}

async function main() {
  console.log('='.repeat(60));
  console.log('POST-LAUNCH TELEMETRY WATCH');
  console.log(`Target: ${ENDPOINT}`);
  console.log(`Duration: ${DURATION_SEC}s | HEAD every ${HEAD_INTERVAL}s | GET every ${GET_INTERVAL}s`);
  console.log(`Burst test at t=${BURST_AT_SEC}s with ${BURST_COUNT} concurrent requests`);
  console.log('='.repeat(60));
  
  const startTime = Date.now();
  let lastHead = 0;
  let lastGet = 0;
  let burstDone = false;
  
  while (true) {
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    if (elapsed >= DURATION_SEC) break;
    
    if (elapsed >= BURST_AT_SEC && !burstDone) {
      await burstTest();
      burstDone = true;
    }
    
    if (elapsed - lastHead >= HEAD_INTERVAL) {
      await headCheck(elapsed);
      lastHead = elapsed;
    }
    
    if (elapsed - lastGet >= GET_INTERVAL) {
      await getCheck(elapsed);
      lastGet = elapsed;
    }
    
    await new Promise(r => setTimeout(r, 1000));
  }
  
  const p95 = calculateP95(stats.latencies);
  const errorRate = stats.totalRequests > 0 
    ? ((stats.statusMix['5xx'] + stats.statusMix['other']) / stats.totalRequests * 100).toFixed(2)
    : '0.00';
  
  console.log('\n' + '='.repeat(60));
  console.log('FINAL REPORT');
  console.log('='.repeat(60));
  
  const report = {
    total_requests: stats.totalRequests,
    error_rate: `${errorRate}%`,
    p95_latency: `${p95} ms`,
    status_mix: {
      '200': stats.statusMix['200'],
      '429': stats.statusMix['429'],
      '5xx': stats.statusMix['5xx']
    },
    burst_test: stats.burstResults ? {
      passed: stats.burstResults['5xx'] === 0,
      results: {
        '200': stats.burstResults['200'],
        '429': stats.burstResults['429'],
        '5xx': stats.burstResults['5xx']
      }
    } : null,
    errors: stats.errors.length > 0 ? stats.errors : 'none'
  };
  
  console.log(JSON.stringify(report, null, 2));
  
  const overall = stats.statusMix['5xx'] === 0 ? '✓ ALL CHECKS PASSED' : '✗ FAILURES DETECTED';
  console.log('\n' + overall);
}

main().catch(console.error);

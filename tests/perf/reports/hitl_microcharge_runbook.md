# HITL Microcharge Runbook
**Run ID**: CEOSPRINT-20260113-EXEC-ZT3G-FIX-027

## Overview
This runbook documents the procedure for executing a $0.50 micro-charge test with 3-of-3 confirmation when CEO authorization is granted.

## Prerequisites

1. **Stripe Safety Check**
   ```bash
   # Verify remaining charges
   # Current: ~4/25
   # Requirement: Either remaining >= 5 OR explicit CEO override
   ```

2. **CEO Override Token**
   - Must be present in tests/perf/reports/hitl_approvals.log
   - Format: `[timestamp] CEO_MICROCHARGE_OVERRIDE <token> APPROVED <details>`

## Execution Procedure

### Step 1: Log CEO Authorization
```bash
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] CEO_MICROCHARGE_OVERRIDE CEO-20260117-MICROCHARGE-AUTH APPROVED $0.50 test charge authorized" >> tests/perf/reports/hitl_approvals.log
```

### Step 2: Create Payment Intent
```bash
curl -X POST https://api.stripe.com/v1/payment_intents \
  -u $STRIPE_SECRET_KEY: \
  -d amount=50 \
  -d currency=usd \
  -d "metadata[run_id]=CEOSPRINT-20260113-EXEC-ZT3G-FIX-027" \
  -d "metadata[purpose]=microcharge_test" \
  -d confirm=true \
  -d "payment_method_types[]=card" \
  -d payment_method=pm_card_visa
```

### Step 3: Capture Response
Save to: tests/perf/evidence/b2c_checkout_trace.json
```json
{
  "run_id": "CEOSPRINT-20260113-EXEC-ZT3G-FIX-027",
  "payment_intent_id": "<pi_xxx>",
  "amount": 50,
  "currency": "usd",
  "status": "succeeded",
  "timestamp": "<ISO8601>"
}
```

### Step 4: Issue Refund (within 60s)
```bash
curl -X POST https://api.stripe.com/v1/refunds \
  -u $STRIPE_SECRET_KEY: \
  -d payment_intent=<pi_xxx> \
  -d "metadata[run_id]=CEOSPRINT-20260113-EXEC-ZT3G-FIX-027"
```

### Step 5: Capture Refund Confirmation
Save to: tests/perf/evidence/refund_confirmations.json
```json
{
  "run_id": "CEOSPRINT-20260113-EXEC-ZT3G-FIX-027",
  "refund_id": "<re_xxx>",
  "payment_intent_id": "<pi_xxx>",
  "amount": 50,
  "status": "succeeded",
  "timestamp": "<ISO8601>",
  "elapsed_seconds": <time_from_charge>
}
```

### Step 6: 3-of-3 Confirmation
1. **HTTP 200 with X-Trace-Id**: Payment intent created successfully
2. **Stripe Dashboard**: Verify payment + refund in Stripe
3. **A8 Telemetry**: POST event with charge details, GET by event_id

### Step 7: Update Verdict
```bash
# Update tests/perf/reports/b2c_funnel_verdict.md
# Change status from CONDITIONAL to VERIFIED
# Add evidence file references
```

## Safety Guardrails

- **NEVER** execute without CEO override when remaining <5
- **ALWAYS** refund within 60 seconds
- **ALWAYS** log all actions to hitl_approvals.log
- **STOP** if any step fails and document in manual_intervention_manifest.md

## Current Status
- Stripe Remaining: ~4/25
- CEO Override: NOT PRESENT
- Status: WAITING FOR AUTHORIZATION

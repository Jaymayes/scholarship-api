# HITL Microcharge Runbook
**Run ID**: CEOSPRINT-20260113-VERIFY-ZT3G-030

## Current Status
- Stripe remaining: ~4/25
- CEO Override: NOT PRESENT
- Threshold Override (<5): NOT PRESENT
- Status: **WAITING FOR AUTHORIZATION**

## Prerequisites for Execution
1. CEO explicit override for B2C charge
2. Threshold (<5 remaining) override approval
3. Both recorded in hitl_approvals.log

## Procedure (When Authorized)
1. Log CEO authorization with timestamp
2. Create $0.50 payment intent
3. Capture to tests/perf/evidence/b2c_checkout_trace.json
4. Refund within 60 seconds
5. Capture refund to tests/perf/evidence/refund_confirmations.json
6. Complete 3-of-3 confirmation

## Current Verdict: FORBIDDEN
No charge executed. Awaiting authorization.

# HITL Microcharge Runbook
**Run ID**: CEOSPRINT-20260113-EXEC-ZT3G-FIX-027

## Prerequisites
1. Stripe remaining >= 5 OR explicit CEO override
2. CEO authorization in hitl_approvals.log

## Procedure
1. Log CEO authorization
2. Create $0.50 payment intent
3. Capture response to b2c_checkout_trace.json
4. Issue refund within 60s
5. Capture refund to refund_confirmations.json
6. Complete 3-of-3 confirmation

## Current Status
- Remaining: ~4/25
- CEO Override: NOT PRESENT
- Status: WAITING FOR AUTHORIZATION

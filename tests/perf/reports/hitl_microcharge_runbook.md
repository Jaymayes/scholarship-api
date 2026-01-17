# HITL Microcharge Runbook
**Run ID**: CEOSPRINT-20260113-VERIFY-ZT3G-032

## Prerequisites
1. Stripe remaining >= 5 OR explicit CEO override
2. CEO authorization recorded in hitl_approvals.log

## Current Status
- Remaining: ~4/25
- CEO Override: NOT PRESENT
- Status: WAITING FOR AUTHORIZATION

## Procedure (When Authorized)
1. Log CEO authorization to hitl_approvals.log
2. Create $0.50 payment intent
3. Capture response to b2c_checkout_trace.json
4. Issue refund within 60 seconds
5. Capture refund to refund_confirmations.json
6. Complete 3-of-3 confirmation:
   - HTTP response
   - Stripe dashboard
   - A8 event checksum

## Sample Commands
```bash
# Create payment intent (requires CEO override)
curl -X POST https://<API>/api/payments/intent \
  -H "Authorization: Bearer $CEO_TOKEN" \
  -d '{"amount": 50, "currency": "usd"}'

# Refund
curl -X POST https://<API>/api/payments/refund \
  -H "Authorization: Bearer $CEO_TOKEN" \
  -d '{"payment_intent_id": "<pi_...>"}'
```

## Verdict: CONDITIONAL
No charge executed. Runbook ready for CEO authorization.

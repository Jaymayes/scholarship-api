# RL + Error-Correction - FIX-029

## Episode Tracking
| Metric | Value |
|--------|-------|
| Episode Increment | +1 |
| Exploration Rate | ≤0.001 |

## Closed-Loop Example
1. **Probe**: Cold-start variance detected
2. **Fail**: Initial P95 > target
3. **Backoff**: Warmup cycle (20 requests)
4. **Success**: P95 under target

## HITL Integration
Override mechanism: hitl_approvals.log

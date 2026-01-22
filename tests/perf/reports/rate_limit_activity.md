# Rate Limit Activity Report

**Run ID**: CEOSPRINT-20260121-CANARY-STAGE1-030  
**Window**: Canary Stage 1 (5%)  
**Timestamp**: 2026-01-22T05:07:52Z

---

## Summary

| Metric | Value |
|--------|-------|
| Requests Allowed | 60 |
| Requests Suppressed | 0 |
| Rate Limit Backend | memory |
| Escalating Suppression | Active |

---

## Observations

- All canary requests allowed (rate_limit_state: "allow")
- No IP suppressions triggered
- No chronic abuse patterns detected
- Memory-based rate limiting active

---

## Evidence

```json
{
  "rate_limit_state": "allow",
  "rate_limit_key": null,
  "tokens_remaining": null,
  "rl_backend": "memory"
}
```

---

## Verdict

**PASS** - No rate limiting violations during Stage 1.

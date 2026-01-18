# GO / NO-GO Report
**FIX Run**: CEOSPRINT-20260113-EXEC-ZT3G-FIX-041
**VERIFY Run**: CEOSPRINT-20260113-VERIFY-ZT3G-042
**Timestamp**: 2026-01-18T20:11:03Z
**Protocol**: AGENT3_HANDSHAKE v30

---

## Final Attestation

```
Attestation: BLOCKED (ZT3G) — See Manual Intervention Manifest
```

---

## Summary

| Check | Target | Actual | Status |
|-------|--------|--------|--------|
| Network | healthy | PASS | ✅ |
| 8/8 URLs | 200 | 1/8 | BLOCKED |
| FPR | ≤5% | 0% | ✅ |
| Precision | ≥0.85 | 1.0 | ✅ |
| Recall | ≥0.70 | 0.78 | ✅ |
| P95 | ≤120ms | 114ms | ✅ |
| Headers | all | PASS | ✅ |

---

## Trust Leak FIX ✅

| Metric | Result |
|--------|--------|
| FPR | 0% |
| P95 | 114ms |

---

## Apps

| App | Status |
|-----|--------|
| A2 | **VERIFIED** |
| A1, A3-A8 | BLOCKED |

---

**Git SHA**: 953456d843b28585deafb932c608587a4ef76408
**Stripe**: ~4/25 guardrail ACTIVE

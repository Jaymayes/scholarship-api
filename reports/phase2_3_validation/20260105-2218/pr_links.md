# PR Links and Patch Status
**Phase**: 2 (Implementation)
**Date**: 2026-01-05T22:20:00Z

## Status: PATCHES GENERATED (No Direct Write Access)

Since direct write access to A7 and A8 repositories is not available, all changes are provided as local patch files with merge instructions.

---

## Issue A: A2 /ready Enhancement

| Item | Status |
|------|--------|
| **Repository** | scholarship-api (A2) - CURRENT PROJECT |
| **Branch** | Can be created locally |
| **Patch Location** | `pr_docs/issue_a_a2_ready/ready_enhancement.patch` |
| **Tests** | `pr_docs/issue_a_a2_ready/test_ready_contract.py` |
| **Feature Flag** | `READY_EXTENDED_CHECKS=false` |
| **Status** | READY TO APPLY |

**Note**: A2 /ready already exists and works. This enhancement adds extended upstream checks.

---

## Issue B: A7 Async Ingestion

| Item | Status |
|------|--------|
| **Repository** | auto-page-maker (A7) - REQUIRES ACCESS |
| **Patch Location** | `pr_docs/issue_b_a7_async/async_ingestion.py` |
| **Tests** | `pr_docs/issue_b_a7_async/test_async_ingestion.py` |
| **Feature Flag** | `ASYNC_INGESTION_ENABLED=false` |
| **Expected P95 Improvement** | 234ms → ≤80ms (-65%) |
| **Status** | READY - Awaiting A7 project access |

---

## Issue C: A8 Banner Auto-Clear

| Item | Status |
|------|--------|
| **Repository** | auto-com-center (A8) - REQUIRES ACCESS |
| **Patch Location** | `pr_docs/issue_c_a8_banners/banner_auto_clear.py` |
| **Tests** | `pr_docs/issue_c_a8_banners/test_banner_auto_clear.py` |
| **Feature Flag** | `BANNER_AUTO_CLEAR_ENABLED=false` |
| **Database Migration** | Required (see README.md) |
| **Status** | READY - Awaiting A8 project access |

---

## Issue D: A8 Demo Mode

| Item | Status |
|------|--------|
| **Repository** | auto-com-center (A8) - REQUIRES ACCESS |
| **Patch Location** | `pr_docs/issue_d_a8_demo_mode/demo_mode.py` |
| **UI Component** | `pr_docs/issue_d_a8_demo_mode/DemoModeBadge.vue` |
| **Tests** | `pr_docs/issue_d_a8_demo_mode/test_demo_mode.py` |
| **Feature Flag** | `DEMO_MODE_ENABLED=false` |
| **Status** | READY - Awaiting A8 project access |

---

## Summary

| Issue | Repository | Access | Patches Ready | Tests Ready |
|-------|------------|--------|---------------|-------------|
| A | A2 | YES | YES | YES |
| B | A7 | NO | YES | YES |
| C | A8 | NO | YES | YES |
| D | A8 | NO | YES | YES |

---

## Next Steps

1. **Issue A**: Can be applied immediately to A2 (this project)
2. **Issues B, C, D**: Require CEO to grant access to A7 and A8 projects

## Files Included

```
pr_docs/
├── issue_a_a2_ready/
│   ├── README.md
│   ├── ready_enhancement.patch
│   └── test_ready_contract.py
├── issue_b_a7_async/
│   ├── README.md
│   ├── async_ingestion.py
│   └── test_async_ingestion.py
├── issue_c_a8_banners/
│   ├── README.md
│   ├── banner_auto_clear.py
│   └── test_banner_auto_clear.py
└── issue_d_a8_demo_mode/
    ├── README.md
    ├── demo_mode.py
    ├── DemoModeBadge.vue
    └── test_demo_mode.py
```

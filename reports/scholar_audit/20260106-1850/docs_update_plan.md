# Documentation Update Plan
**Scholar Ecosystem Audit**
**Date**: 2026-01-06

---

## Proposed Documentation Changes

### 1. ECOSYSTEM_README.md Updates

**File**: `/ECOSYSTEM_README.md` (or equivalent)

**Changes**:
- Add fleet health dashboard section
- Document A6 recovery runbook
- Update OIDC troubleshooting guide
- Add telemetry protocol v3.5.1 reference

**PR Plan**:
```
Title: docs: Add fleet health and OIDC troubleshooting sections
Branch: docs/audit-2026-01-06
Labels: documentation, non-breaking
Reviewers: @ecosystem-team
```

---

### 2. A6 Recovery Runbook

**New File**: `/runbooks/a6_recovery.md`

**Content**:
```markdown
# A6 Provider Service Recovery

## Symptoms
- All A6 endpoints return 500 Internal Server Error
- A8 shows A6 as DOWN
- B2B funnel stalled

## Diagnostic Steps
1. Access A6 Replit console
2. Check startup logs for errors
3. Verify environment variables:
   - DATABASE_URL
   - STRIPE_SECRET_KEY
   - STRIPE_PUBLISHABLE_KEY
   - JWT_SECRET_KEY

## Recovery Steps
1. Fix missing/invalid secrets
2. Test database connection
3. Restart deployment
4. Verify /health returns 200
5. Confirm B2B events flowing to A2

## Escalation
- Primary: A6 Maintainer
- Secondary: Platform Team
- SLA: 4 hours for P0
```

---

### 3. OIDC Client Configuration Guide

**New File**: `/docs/oidc_client_setup.md`

**Content**:
- Required OAuth parameters
- Redirect URI allowlist management
- Token refresh best practices
- Troubleshooting "Session Expired" errors

---

### 4. Telemetry Protocol v3.5.1 Reference

**Update File**: `/docs/telemetry.md`

**Add**:
```markdown
## Required Headers (v3.5.1)
- x-scholar-protocol: v3.5.1
- x-app-label: <APP_ID>
- x-event-id: <UUID>

## Required Payload Fields
- event_name: string
- source_app_id: string
- ts: number (epoch milliseconds)

## Optional Tags
- namespace: string (e.g., "simulated_audit")
- env: string ("staging" | "production")
- version: string
```

---

## PR Checklist

| Item | Status |
|------|--------|
| ECOSYSTEM_README updates | DRAFT |
| A6 recovery runbook | DRAFT |
| OIDC client guide | DRAFT |
| Telemetry reference | DRAFT |

**Note**: All documentation PRs require HUMAN_APPROVAL_REQUIRED before merge.

---

## Implementation Order

1. **Immediate** (after A6 fix): A6 recovery runbook
2. **This week**: OIDC client configuration guide
3. **This sprint**: ECOSYSTEM_README updates
4. **Backlog**: Telemetry protocol reference

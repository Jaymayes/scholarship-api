# Manual Intervention Manifest - FIX-029

## Blocked Services

| App | Service | Status | Action |
|-----|---------|--------|--------|
| A1 | scholar-auth | BLOCKED (HTTP 000) | Deploy in separate workspace |
| A3 | scholarship-agent | BLOCKED (HTTP 000) | Deploy in separate workspace |
| A4 | scholarship-sage | BLOCKED (HTTP 000) | Deploy in separate workspace |
| A5 | student-pilot | BLOCKED (HTTP 000) | Deploy in separate workspace |
| A6 | provider-register | BLOCKED (HTTP 000) | Deploy in separate workspace |
| A7 | auto-page-maker | BLOCKED (HTTP 000) | Deploy in separate workspace |

## Accessible Services

| App | Service | Status |
|-----|---------|--------|
| A2 | scholarship-api | ✅ PASS |
| A8 | auto-com-center | ✅ PASS |

## Required Actions

For each blocked service, navigate to its Replit workspace and:
1. Verify deployment is running
2. Execute: `curl -vL "https://<service>/health"`
3. Confirm HTTP 200 with valid JSON response

**Full ZT3G attestation pending manual verification of A1, A3-A7**

# Golden Path Violations Audit
**Incident ID**: CIR-20260119-001
**Timestamp**: 2026-01-19T15:44:54Z

## DaaS Contract

```
POLICY: No worker app (A2-A7) may hold DATABASE_URL except A2 Core
ENFORCEMENT: A8 registry blocks deploy if detected
```

## A2 (Core Data API)

| Check | Status |
|-------|--------|
| DATABASE_URL | ✅ Authorized |
| Pooling configured | ✅ |
| Statement timeout | ✅ |

## External Apps (A3-A7)

| App | DATABASE_URL | Status |
|-----|--------------|--------|
| A3 | FORBIDDEN | BLOCKED (verify manually) |
| A4 | FORBIDDEN | BLOCKED |
| A5 | FORBIDDEN | BLOCKED |
| A6 | FORBIDDEN | BLOCKED |
| A7 | FORBIDDEN | BLOCKED |

## CI/CD Guard

```yaml
# Manifest digest + static scan
golden_path_guard:
  scan: DATABASE_URL
  exclude: DataService
  fail_on: detected
```

**Action**: A3 workspace owner must audit and remove any DATABASE_URL secret

# WAF Hotfix - Production

**RUN_ID:** CEOSPRINT-20260120-SEV1-HOTFIX-DEPLOY-001  
**Applied:** 2026-01-20T08:34:17Z

## Changes Made

### 1. X-Forwarded-Host Policy

| Setting | Value |
|---------|-------|
| WAF_STRIP_X_FORWARDED_HOST | false |
| WAF_ALLOWLIST_XFH | true |
| WAF_TRUSTED_INGRESS_CIDRS | 35.192.0.0/12,35.224.0.0/12,34.0.0.0/8,136.0.0.0/8 |
| WAF_TRUSTED_INTERNALS | 127.0.0.1/32,::1/128 |
| WAF_ALLOWED_HOST_SUFFIXES | .replit.app,.replit.co,.replit.dev,.scholaraiadvisor.com |

**Policy Logic:**
```
IF (src_ip IN TRUSTED_CIDRS OR src_ip IN TRUSTED_INTERNALS)
   AND (host OR xfh endswith ALLOWED_SUFFIX)
THEN PRESERVE x-forwarded-host
ELSE strip header OR return 403
```

### 2. Underscore Allowlist

| Setting | Value |
|---------|-------|
| WAF_UNDERSCORE_ALLOWLIST | _meta |

**Behavior:**
- `_meta` key is PRESERVED in request bodies (infra signals)
- `__proto__`, `constructor`, `__prototype__`, `prototype` are ALWAYS BLOCKED (prototype pollution)
- Other underscore keys are dropped (logged, not 4xx)

### 3. Code Changes

**File:** `middleware/waf_protection.py`

```python
# Added underscore allowlist parsing
self._underscore_allowlist = self._parse_underscore_allowlist(
    os.getenv("WAF_UNDERSCORE_ALLOWLIST", "")
)
self._proto_pollution_blocklist = {
    "__proto__", "constructor", "__prototype__", "prototype"
}

# Updated _remove_underscore_keys to respect allowlist
if key.lower() in self._proto_pollution_blocklist:
    # ALWAYS block prototype pollution
    dropped.append(f"{key_path} [PROTO_POLLUTION_BLOCKED]")
    continue
    
if key.startswith("_"):
    if key in self._underscore_allowlist:
        # Preserve allowlisted keys like _meta
        sanitized[key] = value
    else:
        # Drop non-allowlisted underscore keys
        dropped.append(key_path)
```

### 4. Expected Log Output

**Preserve (allowlisted):**
```
WAF: Preserved allowlisted underscore key: _meta
```

**Block (prototype pollution):**
```
WAF: BLOCKED prototype pollution attempt: __proto__
```

**Drop (non-allowlisted):**
```
WAF: Dropped underscore-prefixed keys from request: [_internal]
```

## Verification

- Server restarted successfully
- WAF initialized with new underscore allowlist
- No "[SECURITY] Blocked underscore property: _meta" expected for internal telemetry

# WAF Emergency Rollback - X-Forwarded-Host Allowlist Implementation

**Date:** 2026-01-20  
**Phase:** Phase 1 - WAF Emergency Rollback  
**File:** `middleware/waf_protection.py`

---

## Environment Variable Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `WAF_STRIP_X_FORWARDED_HOST` | string | `"true"` | When `"true"`, X-Forwarded-Host headers are stripped (logged only). When `"false"`, headers are preserved for trusted sources with allowed host suffixes. |
| `WAF_TRUSTED_INGRESS_CIDRS` | string | `""` | Comma-separated list of trusted ingress CIDRs (e.g., `"10.0.0.0/8,172.16.0.0/12"`). Requests from these IPs can pass X-Forwarded-Host. |
| `WAF_TRUSTED_INTERNALS` | string | `"127.0.0.1,::1"` | Comma-separated list of trusted internal IPs/CIDRs (localhost by default). |
| `WAF_ALLOWED_HOST_SUFFIXES` | string | `""` | Comma-separated list of allowed host suffixes (e.g., `".replit.app,.scholaraiadvisor.com"`). Empty = allow all. |

### Example Configuration

```bash
# Production configuration
export WAF_STRIP_X_FORWARDED_HOST="false"
export WAF_TRUSTED_INGRESS_CIDRS="10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"
export WAF_TRUSTED_INTERNALS="127.0.0.1,::1,10.42.0.0/16"
export WAF_ALLOWED_HOST_SUFFIXES=".replit.app,.scholaraiadvisor.com,.jamarrlmayes.replit.app"
```

---

## Policy Pseudocode

```
FUNCTION dispatch(request):
    client_ip = request.client.host
    x_forwarded_host = request.headers.get("x-forwarded-host")
    
    IF x_forwarded_host IS NOT EMPTY:
        is_trusted = is_client_trusted(client_ip)
        is_host_allowed = is_host_suffix_allowed(x_forwarded_host)
        
        IF WAF_STRIP_X_FORWARDED_HOST == "false" AND is_trusted AND is_host_allowed:
            # PRESERVE: X-Forwarded-Host is allowed through
            LOG_DEBUG("Preserving X-Forwarded-Host for trusted source")
            INCREMENT xfh_preserved_count
        ELSE:
            IF WAF_STRIP_X_FORWARDED_HOST == "true":
                # STRIP MODE: Header stripped at proxy layer, log only
                LOG_DEBUG("X-Forwarded-Host would be stripped")
                INCREMENT xfh_stripped_count
            ELSE IF NOT is_trusted:
                # BLOCK: Untrusted source sending X-Forwarded-Host
                LOG_WARNING("Blocking untrusted X-Forwarded-Host")
                RETURN HTTP 403 (WAF_XFH_UNTRUSTED)
            ELSE IF NOT is_host_allowed:
                # BLOCK: Host suffix not in allowlist
                LOG_WARNING("Blocking disallowed host suffix")
                RETURN HTTP 403 (WAF_XFH_DISALLOWED)
    
    # Continue to other WAF checks and application
    CONTINUE_PROCESSING()

FUNCTION is_client_trusted(client_ip):
    FOR each network IN WAF_TRUSTED_INTERNALS:
        IF client_ip IN network: RETURN TRUE
    FOR each network IN WAF_TRUSTED_INGRESS_CIDRS:
        IF client_ip IN network: RETURN TRUE
    RETURN FALSE

FUNCTION is_host_suffix_allowed(host):
    IF WAF_ALLOWED_HOST_SUFFIXES IS EMPTY:
        RETURN TRUE  # Permissive mode when no suffixes configured
    host_lower = host.lower().split(":")[0]  # Remove port
    FOR each suffix IN WAF_ALLOWED_HOST_SUFFIXES:
        IF host_lower.endswith(suffix) OR host_lower == suffix.lstrip("."):
            RETURN TRUE
    RETURN FALSE
```

---

## Underscore-Key Payload Handling

For JSON payloads containing underscore-prefixed keys (like `_meta`, `_internal`):

```
FUNCTION sanitize_underscore_keys(body):
    IF body IS NOT VALID JSON:
        RETURN body, []  # Pass through unchanged
    
    data = JSON_PARSE(body)
    sanitized, dropped_keys = remove_underscore_keys(data)
    
    IF dropped_keys IS NOT EMPTY:
        LOG_WARNING("Dropped underscore-prefixed keys: " + dropped_keys)
        INCREMENT underscore_key_dropped_count
    
    RETURN JSON_STRINGIFY(sanitized), dropped_keys

# IMPORTANT: Do NOT return 4xx for underscore keys
# Log and drop the properties, but allow the request to proceed
```

---

## Diff of Changes

### New Imports Added
```python
import ipaddress
import json
import os
from typing import Optional
```

### New Instance Variables in `__init__`
```python
self.xfh_stripped_count = 0
self.xfh_preserved_count = 0
self.underscore_key_dropped_count = 0

# X-Forwarded-Host allowlist configuration
self._strip_xfh = os.getenv("WAF_STRIP_X_FORWARDED_HOST", "true").lower() == "true"
self._trusted_ingress_cidrs = self._parse_cidrs(os.getenv("WAF_TRUSTED_INGRESS_CIDRS", ""))
self._trusted_internals = self._parse_cidrs(os.getenv("WAF_TRUSTED_INTERNALS", "127.0.0.1,::1"))
self._allowed_host_suffixes = self._parse_host_suffixes(os.getenv("WAF_ALLOWED_HOST_SUFFIXES", ""))
```

### New Methods Added

1. **`_parse_cidrs(cidr_string: str)`** - Parses comma-separated CIDR notation into network objects
2. **`_parse_host_suffixes(suffix_string: str)`** - Parses comma-separated host suffixes into a list
3. **`is_client_trusted(client_ip: str)`** - Checks if client IP is in trusted CIDRs/internals
4. **`is_host_suffix_allowed(host: str)`** - Checks if host ends with an allowed suffix
5. **`_sanitize_underscore_keys(body: str)`** - Removes underscore-prefixed keys from JSON
6. **`_remove_underscore_keys(obj: dict, prefix: str)`** - Recursive helper for key removal

### Updated `dispatch()` Method

Added X-Forwarded-Host validation logic after debug path blocking:

```python
# PHASE 1: Emergency Rollback - X-Forwarded-Host allowlist logic
x_forwarded_host = request.headers.get("x-forwarded-host", "")

if x_forwarded_host:
    is_trusted = self.is_client_trusted(client_ip)
    is_host_allowed = self.is_host_suffix_allowed(x_forwarded_host)
    
    if not self._strip_xfh and is_trusted and is_host_allowed:
        # Preserve header - do nothing
        self.xfh_preserved_count += 1
    else:
        if self._strip_xfh:
            self.xfh_stripped_count += 1
        elif not is_trusted:
            return HTTP 403 (WAF_XFH_UNTRUSTED)
        elif not is_host_allowed:
            return HTTP 403 (WAF_XFH_DISALLOWED)
```

### Updated `get_stats()` Method

Added new counters to WAF statistics:

```python
return {
    "total_blocked": self.blocked_requests,
    "sql_injection_blocks": self.sql_injection_blocks,
    "xss_blocks": self.xss_blocks,
    "auth_enforcement_blocks": self.auth_enforcement_blocks,
    "xfh_stripped_count": self.xfh_stripped_count,
    "xfh_preserved_count": self.xfh_preserved_count,
    "underscore_key_dropped_count": self.underscore_key_dropped_count
}
```

---

## HTTP Response Codes

| Code | Error Code | Description |
|------|------------|-------------|
| 403 | `WAF_XFH_UNTRUSTED` | X-Forwarded-Host received from untrusted IP |
| 403 | `WAF_XFH_DISALLOWED` | X-Forwarded-Host suffix not in allowlist |

---

## Metrics Exposed

The following metrics are now available via `waf_protection.get_stats()`:

- `xfh_stripped_count` - Number of requests where X-Forwarded-Host was stripped (strip mode)
- `xfh_preserved_count` - Number of requests where X-Forwarded-Host was preserved (trusted)
- `underscore_key_dropped_count` - Number of underscore-prefixed keys dropped from payloads

---

## Testing

### Verify Trusted IP Detection

```bash
# From localhost (should be trusted)
curl -H "X-Forwarded-Host: test.replit.app" http://localhost:5000/health

# Expected: Request passes (localhost in trusted internals)
```

### Verify Host Suffix Validation

```bash
# Set allowed suffixes
export WAF_ALLOWED_HOST_SUFFIXES=".replit.app"
export WAF_STRIP_X_FORWARDED_HOST="false"

# Valid suffix
curl -H "X-Forwarded-Host: myapp.replit.app" http://localhost:5000/health
# Expected: Pass

# Invalid suffix (when from trusted IP but not allowed host)
curl -H "X-Forwarded-Host: evil.attacker.com" http://localhost:5000/health  
# Expected: 403 WAF_XFH_DISALLOWED (if from trusted IP)
```

---

## Rollback Procedure

To revert to default behavior (strip all X-Forwarded-Host headers):

```bash
export WAF_STRIP_X_FORWARDED_HOST="true"
# or simply unset the variable (defaults to "true")
unset WAF_STRIP_X_FORWARDED_HOST
```

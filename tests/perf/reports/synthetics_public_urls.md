# Synthetic Monitors: Public URL Configuration

**Phase 3 Additional Repair - CIR-20260119-001**  
**Date:** 2026-01-20  
**Status:** ✅ VERIFIED

## Overview

All synthetic health check and probe URLs have been verified to use public HTTPS endpoints. Localhost references are explicitly blocked and replaced with PUBLIC_BASE_URL from environment.

## URL Resolution Order

The `get_public_base_url()` function in `services/pilot_controller.py` resolves URLs in this priority order:

| Priority | Source | Example |
|----------|--------|---------|
| 1 | `PUBLIC_BASE_URL` env var | `https://scholarship-api-jamarrlmayes.replit.app` |
| 2 | `APP_BASE_URL` env var | `https://scholarship-api-jamarrlmayes.replit.app` |
| 3 | `REPLIT_DEV_DOMAIN` with https:// | `https://83dfcf73-98cb-4164-b6f8-418c739faf3b-00-10wl0zocrf1wy.picard.replit.dev` |
| 4 | `REPLIT_DOMAINS` first domain | `https://83dfcf73-98cb-4164-b6f8-418c739faf3b-00-10wl0zocrf1wy.picard.replit.dev` |
| 5 | Fallback | `https://scholarship-api-jamarrlmayes.replit.app` |

## Localhost Blocking

The synthetic probe implementation explicitly blocks localhost URLs:

```python
elif "localhost" in provider_login_url.lower() or provider_login_url.startswith("http://localhost"):
    logger.warning(f"SYNTHETIC URL BLOCKED: localhost not allowed in '{provider_login_url}', using PUBLIC_BASE_URL")
    base_url = get_public_base_url()
    provider_login_url = f"{base_url}/health"
```

## HTTPS Enforcement

Non-HTTPS URLs are automatically converted:

```python
elif not provider_login_url.startswith("https://"):
    logger.warning(f"SYNTHETIC URL WARNING: Non-HTTPS URL '{provider_login_url}', enforcing HTTPS")
    provider_login_url = provider_login_url.replace("http://", "https://")
```

## Verified Endpoints

| Endpoint | URL Pattern | Protocol |
|----------|-------------|----------|
| Health Check | `{PUBLIC_BASE_URL}/health` | HTTPS ✅ |
| Synthetic Login | `{PUBLIC_BASE_URL}/health` | HTTPS ✅ |
| Provider Login | User-provided or auto-resolved | HTTPS ✅ |

## API Endpoints

### Get Synthetics Configuration
```
GET /api/internal/pilot/synthetics/config
```

Response:
```json
{
  "public_base_url": "https://...",
  "localhost_blocked": true,
  "https_enforced": true,
  "url_resolution_order": [...],
  "probe_deduplication": {
    "enabled": true,
    "mutex_per_target": true,
    "jitter_pct": 20,
    "backoff_sequence_sec": [2, 5, 10]
  }
}
```

## Verification Checklist

- [x] `get_public_base_url()` never returns localhost
- [x] Localhost detection blocks `http://localhost` and any URL containing "localhost"
- [x] HTTPS is enforced for all synthetic probe URLs
- [x] Environment variable resolution follows documented priority
- [x] Fallback URL is a valid public HTTPS endpoint
- [x] API endpoint exposes configuration for monitoring

## Files Modified

- `services/pilot_controller.py`: Added `get_public_base_url()`, updated `run_synthetic_login_test()`
- `routers/pilot.py`: Added `/synthetics/config` endpoint

## Related Documentation

- `tests/perf/reports/probe_mutex_backoff.md` - Probe de-duplication mechanism

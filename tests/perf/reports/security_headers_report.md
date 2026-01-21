# Security Headers Report

**Run ID**: CEOSPRINT-20260121-EXEC-ZT3G-V2S2-FIX-027  
**Protocol**: AGENT3_HANDSHAKE v30  

---

## A0 (Scholarship API) Headers

### CORS Configuration
- **Status**: ✅ Locked down to approved origins
- **Origins**: CORS_ALLOWED_ORIGINS from env (production domains only)
- **Credentials**: Allowed for cross-domain auth

### Privacy-by-Default Middleware
- **Status**: ✅ Active
- **COPPA/GPC/GDPR**: Implemented
- **DNT Header**: Honored
- **GPC Header**: Honored
- **Minor Detection**: Age-based (DOB, school/grade, JWT claims)
- **Headers Added**:
  - X-Privacy-Mode: minor|adult
  - X-Do-Not-Sell: 1 (for minors/GPC)
  - X-Tracking-Disabled: 1 (for DNT/GPC)

### Security Headers (via middleware)
- **X-Content-Type-Options**: nosniff
- **X-Frame-Options**: DENY
- **X-XSS-Protection**: 1; mode=block
- **Strict-Transport-Security**: max-age=31536000

---

## External Apps (Cannot Verify)

| App | Status |
|-----|--------|
| A1 | BLOCKED |
| A2 | BLOCKED |
| A3 | BLOCKED |
| A4 | BLOCKED |
| A5 | Partial (no detailed headers) |
| A6 | BLOCKED |
| A7 | BLOCKED |
| A8 | DEGRADED |

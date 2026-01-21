
---

## Security Improvements Required (Pre-Production)

### Issue 1: Role Validation Hardening

**Status**: Documented for canary stage  
**Priority**: HIGH  
**Fix Timeline**: Before 100% cutover

**Current State**:
- X-User-Role header is accepted from clients
- No validation against JWT claims

**Required Fix**:
```python
def get_trusted_role(request: Request) -> UserRole:
    """Get role from trusted source (JWT claims > session > header fallback)"""
    # 1. Check JWT claims (set by auth middleware)
    if hasattr(request.state, "jwt_claims"):
        role = request.state.jwt_claims.get("role")
        if role:
            return UserRole(role)
    
    # 2. Check session data
    if hasattr(request.state, "session"):
        role = request.state.session.get("role")
        if role:
            return UserRole(role)
    
    # 3. Header fallback ONLY for consumer role
    header_role = request.headers.get("X-User-Role", "consumer")
    if header_role in ["admin", "system", "school_official"]:
        raise HTTPException(403, "Elevated roles require authenticated session")
    
    return UserRole.CONSUMER
```

**Mitigation for Canary**:
- Admin/system roles blocked at API gateway level
- FERPA-covered data requires additional auth checks

### Issue 2: CORS Configuration (FIXED)

**Status**: ✅ RESOLVED  
**Fix Applied**: Restricted allow_origins to approved domains

---

**Last Updated**: 2026-01-21T10:30:00Z

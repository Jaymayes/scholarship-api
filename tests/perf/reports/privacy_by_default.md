# Privacy-by-Default (13-17 Age Group)

**RUN_ID**: CEOSPRINT-20260121-EXEC-ZT3G-V2-S1-058  
**Sprint**: V2 Sprint-1 (72h)

## Overview

Privacy-by-Default middleware ensures enhanced privacy protections for users aged 13-17, complying with COPPA, state privacy laws, and platform policies.

## Age Detection

### Methods
| Method | Priority | Accuracy |
|--------|----------|----------|
| Registration DOB | 1 | 100% |
| School/grade level | 2 | 95% |
| Document extraction | 3 | 90% |
| User attestation | 4 | N/A |

### Implementation
```python
class AgeDetectionMiddleware:
    """Detect user age and apply privacy policies."""
    
    async def __call__(self, request: Request, call_next):
        user = await get_current_user(request)
        if user:
            age = self.calculate_age(user.date_of_birth)
            request.state.user_age = age
            request.state.is_minor = age < 18
            request.state.privacy_level = self.get_privacy_level(age)
        return await call_next(request)
    
    def get_privacy_level(self, age: int) -> str:
        if age < 13:
            return "COPPA"  # Requires parental consent
        elif age < 16:
            return "MINOR_RESTRICTED"  # No ads, no tracking
        elif age < 18:
            return "MINOR_STANDARD"  # Limited tracking
        else:
            return "ADULT"
```

## Privacy Protections for Minors (<18)

### Disabled Features
| Feature | <13 | 13-15 | 16-17 | 18+ |
|---------|-----|-------|-------|-----|
| Advertising pixels | ❌ | ❌ | ❌ | ✅ |
| Third-party tracking | ❌ | ❌ | ❌ | ✅ |
| Data sale | ❌ | ❌ | ❌ | ✅* |
| Behavioral targeting | ❌ | ❌ | ❌ | ✅ |
| Location tracking | ❌ | ❌ | ❌ | ✅ |
| Cross-site tracking | ❌ | ❌ | ❌ | ✅ |

*Subject to opt-out (Do Not Sell)

### Automatic Settings
```python
MINOR_PRIVACY_SETTINGS = {
    "do_not_sell": True,
    "do_not_track": True,
    "disable_pixels": True,
    "disable_analytics_sharing": True,
    "restrict_data_retention": True,  # 90 days max
    "require_parental_consent": True,  # For <13
}
```

## Do Not Sell Implementation

### Header Detection
```python
def check_do_not_sell(request: Request) -> bool:
    """Check for GPC (Global Privacy Control) header."""
    # Sec-GPC header (standard)
    gpc = request.headers.get("Sec-GPC")
    if gpc == "1":
        return True
    
    # DNT header (legacy)
    dnt = request.headers.get("DNT")
    if dnt == "1":
        return True
    
    return False
```

### Enforcement
```python
async def enforce_do_not_sell(request: Request, call_next):
    """Remove tracking if DoNotSell is active."""
    if request.state.do_not_sell or request.state.is_minor:
        # Remove tracking cookies
        response = await call_next(request)
        response.delete_cookie("_ga")
        response.delete_cookie("_gid")
        response.delete_cookie("_fbp")
        
        # Add compliance headers
        response.headers["X-Do-Not-Sell"] = "1"
        return response
    
    return await call_next(request)
```

## DataService Policy Integration

### User Record Extension
```sql
ALTER TABLE users ADD COLUMN privacy_level VARCHAR(20) DEFAULT 'ADULT';
ALTER TABLE users ADD COLUMN do_not_sell BOOLEAN DEFAULT false;
ALTER TABLE users ADD COLUMN parental_consent_date TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN consent_verified BOOLEAN DEFAULT false;
```

### Policy Enforcement at Data Layer
```python
class PrivacyPolicyEnforcer:
    """Enforce privacy policies at DataService level."""
    
    def filter_response(self, user: User, data: dict) -> dict:
        """Filter response based on user privacy level."""
        if user.privacy_level in ("COPPA", "MINOR_RESTRICTED"):
            # Remove sensitive fields
            data.pop("analytics", None)
            data.pop("tracking_id", None)
            data.pop("behavioral_data", None)
        return data
    
    def can_share_data(self, user: User, purpose: str) -> bool:
        """Check if data can be shared for given purpose."""
        if user.privacy_level == "COPPA":
            return False
        if user.do_not_sell and purpose == "advertising":
            return False
        return True
```

## Verification

### Header Check Test
```bash
# Test GPC header is respected
curl -H "Sec-GPC: 1" https://api.scholaraiadvisor.com/health

# Response should include:
# X-Do-Not-Sell: 1
```

### Minor Detection Test
```python
def test_minor_privacy():
    # Create test user age 15
    user = create_test_user(age=15)
    response = client.get(f"/api/users/{user.id}/profile")
    
    assert response.headers.get("X-Do-Not-Sell") == "1"
    assert "tracking_id" not in response.json()
```

## Compliance Checklist

| Requirement | Status |
|-------------|--------|
| Age detection | ✅ Designed |
| Pixel/tracking disable | ✅ Designed |
| Do Not Sell flag | ✅ Designed |
| GPC header respect | ✅ Designed |
| DataService policy | ✅ Designed |
| Parental consent flow | ✅ Designed |

## Monitoring

| Metric | Purpose |
|--------|---------|
| minor_user_count | Track protected users |
| do_not_sell_rate | Compliance rate |
| pixel_disable_count | Protection effectiveness |
| gpc_header_count | GPC adoption |

**Status**: ✅ DESIGN COMPLETE

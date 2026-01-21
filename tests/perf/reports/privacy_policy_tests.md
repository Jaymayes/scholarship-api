# Privacy Policy Test Scenarios

**RUN_ID**: CEOSPRINT-20260121-EXEC-ZT3G-V2-S1-TESTS  
**Sprint**: V2 Sprint-1 (72h)  
**Status**: ✅ TEST SCENARIOS DEFINED

## Overview

This document defines test scenarios for age detection and privacy policy enforcement in `server/v2/privacy/`.

## 1. Age Detection Tests

### 1.1 DOB-Based Detection

```python
def test_dob_detection_adult():
    """Test adult detection from DOB"""
    detector = AgeDetector()
    profile = detector.from_dob("1990-01-15")
    
    assert profile.is_minor == False
    assert profile.age_range == AgeRange.ADULT
    assert profile.detection_method == DetectionMethod.DOB
    assert profile.exact_age >= 18

def test_dob_detection_teen_16_17():
    """Test 16-17 year old detection"""
    from datetime import date, timedelta
    
    detector = AgeDetector()
    dob = date.today() - timedelta(days=365 * 17)
    profile = detector.from_dob(dob)
    
    assert profile.is_minor == True
    assert profile.age_range == AgeRange.TEEN_16_17
    assert profile.do_not_sell == True

def test_dob_detection_teen_13_15():
    """Test 13-15 year old detection"""
    from datetime import date, timedelta
    
    detector = AgeDetector()
    dob = date.today() - timedelta(days=365 * 14)
    profile = detector.from_dob(dob)
    
    assert profile.is_minor == True
    assert profile.age_range == AgeRange.TEEN_13_15
    assert profile.requires_parental_consent == False

def test_dob_detection_under_13():
    """Test under-13 detection (COPPA)"""
    from datetime import date, timedelta
    
    detector = AgeDetector()
    dob = date.today() - timedelta(days=365 * 10)
    profile = detector.from_dob(dob)
    
    assert profile.is_minor == True
    assert profile.age_range == AgeRange.UNDER_13
    assert profile.requires_parental_consent == True
    assert profile.do_not_sell == True
```

### 1.2 School/Grade Detection

```python
def test_high_school_detection():
    """Test high school = minor detection"""
    detector = AgeDetector()
    profile = detector.from_school_grade(school_level="High School")
    
    assert profile.is_minor == True
    assert profile.detection_method == DetectionMethod.SCHOOL_GRADE

def test_grade_level_detection():
    """Test specific grade detection"""
    detector = AgeDetector()
    
    # 12th grade = ~17 years old
    profile = detector.from_school_grade(grade="12th")
    assert profile.is_minor == True
    assert profile.exact_age == 17
    
    # 9th grade = ~14 years old
    profile = detector.from_school_grade(grade="freshman")
    assert profile.is_minor == True
    assert profile.exact_age == 14

def test_middle_school_detection():
    """Test middle school detection"""
    detector = AgeDetector()
    profile = detector.from_school_grade(school_level="Middle School")
    
    assert profile.is_minor == True
    assert profile.age_range in [AgeRange.TEEN_13_15, AgeRange.UNDER_13]
```

### 1.3 JWT Claims Detection

```python
def test_jwt_birthdate_claim():
    """Test birthdate in JWT claims"""
    detector = AgeDetector()
    claims = {"birthdate": "2010-05-15"}
    profile = detector.from_jwt_claims(claims)
    
    assert profile.is_minor == True
    assert profile.detection_method == DetectionMethod.JWT_CLAIMS

def test_jwt_is_minor_claim():
    """Test explicit is_minor claim"""
    detector = AgeDetector()
    claims = {"is_minor": True}
    profile = detector.from_jwt_claims(claims)
    
    assert profile.is_minor == True
    assert profile.do_not_sell == True

def test_jwt_age_claim():
    """Test age claim in JWT"""
    detector = AgeDetector()
    claims = {"age": 15}
    profile = detector.from_jwt_claims(claims)
    
    assert profile.is_minor == True
    assert profile.exact_age == 15
```

### 1.4 Document Extraction Detection

```python
def test_document_dob_extraction():
    """Test DOB extracted from document"""
    detector = AgeDetector()
    doc_data = {
        "date_of_birth": "2008-03-20",
        "document_type": "student_id"
    }
    profile = detector.from_document_extraction(doc_data)
    
    assert profile.is_minor == True
    assert profile.detection_method == DetectionMethod.DOCUMENT_EXTRACTION

def test_document_grade_extraction():
    """Test grade extracted from document"""
    detector = AgeDetector()
    doc_data = {
        "school": "Lincoln High School",
        "grade": "11th"
    }
    profile = detector.from_document_extraction(doc_data)
    
    assert profile.is_minor == True
```

## 2. Privacy Policy Tests

### 2.1 Policy Mode Selection

```python
def test_minor_policy():
    """Test minor gets full protection"""
    profile = PrivacyProfile(
        is_minor=True,
        age_range=AgeRange.TEEN_16_17,
        detection_method=DetectionMethod.DOB,
    )
    policy = get_privacy_policy(profile)
    
    assert policy.mode == PrivacyMode.MINOR
    assert policy.do_not_sell == True
    assert policy.disable_advertising_pixels == True
    assert policy.disable_third_party_tracking == True
    assert policy.disable_behavioral_targeting == True
    assert policy.disable_location_tracking == True

def test_coppa_policy():
    """Test COPPA for under-13"""
    profile = PrivacyProfile(
        is_minor=True,
        age_range=AgeRange.UNDER_13,
        detection_method=DetectionMethod.DOB,
        requires_parental_consent=True,
    )
    policy = get_privacy_policy(profile)
    
    assert policy.mode == PrivacyMode.COPPA
    assert policy.require_parental_consent == True
    assert policy.data_retention_days == 90

def test_gpc_policy():
    """Test GPC header is honored"""
    policy = get_privacy_policy(gpc_enabled=True)
    
    assert policy.mode == PrivacyMode.GPC_HONORED
    assert policy.gpc_honored == True
    assert policy.do_not_sell == True
    assert policy.disable_behavioral_targeting == True

def test_do_not_sell_policy():
    """Test user DoNotSell preference"""
    policy = get_privacy_policy(user_do_not_sell_preference=True)
    
    assert policy.mode == PrivacyMode.DO_NOT_SELL
    assert policy.do_not_sell == True
    assert policy.disable_third_party_tracking == True
```

### 2.2 Response Headers

```python
def test_minor_headers():
    """Test headers set for minors"""
    profile = PrivacyProfile(
        is_minor=True,
        age_range=AgeRange.TEEN_16_17,
        detection_method=DetectionMethod.DOB,
    )
    policy = get_privacy_policy(profile)
    headers = policy.get_response_headers()
    
    assert headers["X-Privacy-Mode"] == "minor"
    assert headers["X-Do-Not-Sell"] == "true"
    assert headers["X-Tracking-Disabled"] == "true"
    assert headers["X-Ads-Disabled"] == "true"

def test_gpc_headers():
    """Test GPC headers"""
    policy = get_privacy_policy(gpc_enabled=True)
    headers = policy.get_response_headers()
    
    assert headers["X-Privacy-Mode"] == "gpc_honored"
    assert headers["X-GPC-Honored"] == "true"
    assert headers["X-Do-Not-Sell"] == "true"
```

## 3. Middleware Integration Tests

### 3.1 Request Processing

```python
@pytest.mark.asyncio
async def test_middleware_gpc_header():
    """Test middleware honors GPC header"""
    from fastapi.testclient import TestClient
    
    response = client.get(
        "/api/health",
        headers={"Sec-GPC": "1"}
    )
    
    assert response.headers.get("X-GPC-Honored") == "true"
    assert response.headers.get("X-Do-Not-Sell") == "true"

@pytest.mark.asyncio
async def test_middleware_privacy_context_header():
    """Test X-Privacy-Context header processing"""
    response = client.get(
        "/api/health",
        headers={"X-Privacy-Context": "minor=true"}
    )
    
    assert response.headers.get("X-Privacy-Mode") == "minor"
    assert response.headers.get("X-Tracking-Disabled") == "true"

@pytest.mark.asyncio
async def test_middleware_csp_for_minors():
    """Test CSP is set for minors"""
    response = client.get(
        "/api/health",
        headers={"X-Privacy-Context": "minor=true"}
    )
    
    csp = response.headers.get("Content-Security-Policy")
    assert "connect-src 'self'" in csp
    assert "script-src 'self'" in csp
```

### 3.2 Privacy Context Dependency

```python
@pytest.mark.asyncio
async def test_privacy_context_can_track():
    """Test can_track() for different policies"""
    # Minor cannot be tracked
    minor_context = PrivacyContext(is_minor=True)
    assert minor_context.can_track() == False
    
    # Adult can be tracked
    adult_context = PrivacyContext(is_minor=False)
    assert adult_context.can_track() == True
    
    # GPC disables tracking
    gpc_context = PrivacyContext(gpc_honored=True)
    assert gpc_context.can_track() == False

@pytest.mark.asyncio
async def test_require_adult_dependency():
    """Test require_adult raises for minors"""
    from fastapi import HTTPException
    
    minor_context = PrivacyContext(is_minor=True)
    
    with pytest.raises(HTTPException) as exc_info:
        require_adult(minor_context)
    
    assert exc_info.value.status_code == 403
```

## 4. E2E Test Scenarios

### 4.1 Student Registration Flow

```gherkin
Scenario: Minor registers and receives privacy protection
  Given a user with DOB "2010-05-15"
  When they complete registration
  Then is_minor should be True
  And X-Privacy-Mode header should be "minor"
  And X-Do-Not-Sell header should be "true"
  And advertising pixels should be disabled
```

### 4.2 GPC Browser Setting

```gherkin
Scenario: User with GPC enabled browses site
  Given a browser with Sec-GPC: 1 header
  When the user visits any page
  Then X-GPC-Honored header should be "true"
  And X-Do-Not-Sell header should be "true"
  And third-party tracking should be disabled
```

### 4.3 Adult Opt-Out

```gherkin
Scenario: Adult user opts out of data sale
  Given an adult user with do_not_sell preference True
  When they make API requests
  Then X-Privacy-Mode header should be "do_not_sell"
  And X-Do-Not-Sell header should be "true"
  And behavioral targeting should be disabled
```

## 5. Compliance Verification

### 5.1 Header Verification Test

```bash
# Test GPC header is honored
curl -H "Sec-GPC: 1" https://api.scholaraiadvisor.com/api/health -v 2>&1 | grep "X-"

# Expected headers:
# X-Privacy-Mode: gpc_honored
# X-Do-Not-Sell: true
# X-GPC-Honored: true
```

### 5.2 Minor Detection Test

```bash
# Test minor privacy context
curl -H "X-Privacy-Context: minor=true" https://api.scholaraiadvisor.com/api/health -v 2>&1 | grep "X-"

# Expected headers:
# X-Privacy-Mode: minor
# X-Do-Not-Sell: true
# X-Tracking-Disabled: true
# X-Ads-Disabled: true
```

## 6. Test Coverage Matrix

| Test Category | Scenarios | Status |
|---------------|-----------|--------|
| Age Detection - DOB | 4 | ✅ Defined |
| Age Detection - School | 3 | ✅ Defined |
| Age Detection - JWT | 3 | ✅ Defined |
| Age Detection - Document | 2 | ✅ Defined |
| Policy Selection | 4 | ✅ Defined |
| Response Headers | 2 | ✅ Defined |
| Middleware Integration | 3 | ✅ Defined |
| Privacy Context | 2 | ✅ Defined |
| E2E Scenarios | 3 | ✅ Defined |
| Compliance Verification | 2 | ✅ Defined |

## 7. Running Tests

```bash
# Run all privacy tests
pytest server/v2/privacy/ -v

# Run with coverage
pytest server/v2/privacy/ --cov=server/v2/privacy --cov-report=html

# Run specific test categories
pytest server/v2/privacy/ -k "test_dob" -v
pytest server/v2/privacy/ -k "test_gpc" -v
pytest server/v2/privacy/ -k "test_minor" -v
```

# Gate 0 Execution Packet: auto_com_center
**Service**: auto_com_center  
**DRI**: Agent3 + SRE  
**Deadline**: Today 14:00 MST  
**Gate**: Gate 0 - Security Foundation  

---

## Executive Summary

Replace all hardcoded links in email/SMS templates with environment-derived base URLs. This ensures notifications route users to correct frontends (student_pilot or provider_register) regardless of environment.

**Success Criteria**:
- ✅ Zero hardcoded URLs in notification templates
- ✅ Environment variables for all frontend/service URLs
- ✅ Boot-time validation enforces required env vars
- ✅ Link generation tested for all notification types
- ✅ Template rendering uses dynamic URL building

---

## I. Current State Assessment

### Step 1: Identify Hardcoded URLs

Search for hardcoded URLs across the codebase:

```bash
# Find hardcoded https:// URLs in templates
grep -r "https://" templates/ || grep -r "https://" app/ || find . -name "*.html" -o -name "*.txt" -o -name "*.py" | xargs grep -l "https://"

# Common patterns to find:
# - https://student-pilot-jamarrlmayes.replit.app/...
# - https://provider-register-jamarrlmayes.replit.app/...
# - href="https://..." in HTML templates
# - Plain URLs in SMS templates
```

### Step 2: Catalog Notification Types

List all notification types and their URL requirements:

| Notification Type | Audience | Required Links | Destination |
|-------------------|----------|----------------|-------------|
| Application Confirmation | Student | View Application, Dashboard | student_pilot |
| Application Status Update | Student | View Status | student_pilot |
| Scholarship Match | Student | View Scholarship, Apply Now | student_pilot |
| Deadline Reminder | Student | Complete Application | student_pilot |
| Provider Onboarding | Provider | Complete Profile | provider_register |
| Applicant Notification | Provider | View Applicants | provider_register |
| New Scholarship Published | Provider | View Scholarship | provider_register |
| Password Reset | Both | Reset Link | student_pilot OR provider_register |

---

## II. Environment Variable Configuration

### Required Environment Variables

Add to Replit Secrets:

```bash
# Frontend Base URLs (for user-facing links)
STUDENT_PILOT_BASE_URL=https://student-pilot-jamarrlmayes.replit.app
PROVIDER_REGISTER_BASE_URL=https://provider-register-jamarrlmayes.replit.app

# Backend Service URLs (for API calls)
AUTH_API_BASE_URL=https://scholar-auth-jamarrlmayes.replit.app
SCHOLARSHIP_API_BASE_URL=https://scholarship-api-jamarrlmayes.replit.app

# Service Identity
SERVICE_NAME=auto_com_center
ENVIRONMENT=production

# Email Configuration
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=notifications@scholarai.com
SMTP_PASSWORD=<secret>
FROM_EMAIL=noreply@scholarai.com
FROM_NAME=Scholar AI Advisor

# SMS Configuration (if applicable)
SMS_PROVIDER=twilio
SMS_API_KEY=<secret>
SMS_FROM_NUMBER=+1234567890
```

---

## III. Implementation Steps

### Step 1: Create URL Builder Service

```python
# services/url_builder.py
import os
from urllib.parse import urljoin
from typing import Dict, Optional

class URLBuilder:
    """Centralized URL building for notification links"""
    
    def __init__(self):
        self.student_base = os.getenv("STUDENT_PILOT_BASE_URL")
        self.provider_base = os.getenv("PROVIDER_REGISTER_BASE_URL")
        
        if not self.student_base or not self.provider_base:
            raise RuntimeError(
                "FATAL: STUDENT_PILOT_BASE_URL and PROVIDER_REGISTER_BASE_URL "
                "must be configured in environment variables"
            )
    
    def student_dashboard(self) -> str:
        """Student dashboard URL"""
        return urljoin(self.student_base, "/dashboard")
    
    def student_scholarship(self, scholarship_id: str) -> str:
        """Student scholarship detail page"""
        return urljoin(self.student_base, f"/scholarships/{scholarship_id}")
    
    def student_application(self, application_id: str) -> str:
        """Student application detail page"""
        return urljoin(self.student_base, f"/applications/{application_id}")
    
    def student_profile(self) -> str:
        """Student profile page"""
        return urljoin(self.student_base, "/profile")
    
    def provider_dashboard(self) -> str:
        """Provider dashboard URL"""
        return urljoin(self.provider_base, "/dashboard")
    
    def provider_scholarship(self, scholarship_id: str) -> str:
        """Provider scholarship management page"""
        return urljoin(self.provider_base, f"/scholarships/{scholarship_id}")
    
    def provider_applicants(self, scholarship_id: str) -> str:
        """Provider applicant list page"""
        return urljoin(self.provider_base, f"/scholarships/{scholarship_id}/applicants")
    
    def provider_profile(self) -> str:
        """Provider profile page"""
        return urljoin(self.provider_base, "/profile")
    
    def password_reset(self, user_type: str, token: str) -> str:
        """Password reset link (student or provider)"""
        base = self.student_base if user_type == "student" else self.provider_base
        return urljoin(base, f"/auth/reset-password?token={token}")
    
    def unsubscribe(self, user_id: str, notification_type: str) -> str:
        """Unsubscribe link"""
        # This could go to either frontend or a dedicated unsubscribe page
        return urljoin(self.student_base, f"/preferences/unsubscribe?user={user_id}&type={notification_type}")

# Singleton instance
url_builder = URLBuilder()
```

### Step 2: Update Email Templates

**Before** (hardcoded):
```html
<!-- templates/email/application_confirmation.html -->
<html>
  <body>
    <h1>Application Submitted!</h1>
    <p>View your application: <a href="https://student-pilot-jamarrlmayes.replit.app/applications/{{application_id}}">Click here</a></p>
    <p>Go to dashboard: <a href="https://student-pilot-jamarrlmayes.replit.app/dashboard">Dashboard</a></p>
  </body>
</html>
```

**After** (environment-driven):
```html
<!-- templates/email/application_confirmation.html -->
<html>
  <body>
    <h1>Application Submitted!</h1>
    <p>View your application: <a href="{{application_url}}">Click here</a></p>
    <p>Go to dashboard: <a href="{{dashboard_url}}">Dashboard</a></p>
  </body>
</html>
```

### Step 3: Update Notification Service

```python
# services/notification_service.py
from jinja2 import Environment, FileSystemLoader, select_autoescape
from typing import Dict, Optional
from services.url_builder import url_builder
import os

class NotificationService:
    def __init__(self):
        # Set up Jinja2 template environment
        self.jinja_env = Environment(
            loader=FileSystemLoader("templates"),
            autoescape=select_autoescape(['html', 'xml'])
        )
    
    async def send_application_confirmation(
        self,
        recipient_email: str,
        student_name: str,
        application_id: str,
        scholarship_name: str
    ):
        """Send application confirmation to student"""
        # Build URLs using URLBuilder
        context = {
            "student_name": student_name,
            "scholarship_name": scholarship_name,
            "application_id": application_id,
            "application_url": url_builder.student_application(application_id),
            "dashboard_url": url_builder.student_dashboard()
        }
        
        # Render template
        template = self.jinja_env.get_template("email/application_confirmation.html")
        html_content = template.render(**context)
        
        # Send email
        await self._send_email(
            to=recipient_email,
            subject=f"Application Confirmed: {scholarship_name}",
            html_content=html_content
        )
    
    async def send_scholarship_match(
        self,
        recipient_email: str,
        student_name: str,
        scholarship_id: str,
        scholarship_name: str,
        match_score: float
    ):
        """Send scholarship match notification to student"""
        context = {
            "student_name": student_name,
            "scholarship_name": scholarship_name,
            "match_score": f"{match_score:.0%}",
            "scholarship_url": url_builder.student_scholarship(scholarship_id),
            "dashboard_url": url_builder.student_dashboard()
        }
        
        template = self.jinja_env.get_template("email/scholarship_match.html")
        html_content = template.render(**context)
        
        await self._send_email(
            to=recipient_email,
            subject=f"New Scholarship Match: {scholarship_name}",
            html_content=html_content
        )
    
    async def send_provider_new_applicant(
        self,
        recipient_email: str,
        provider_name: str,
        scholarship_id: str,
        scholarship_name: str,
        applicant_name: str
    ):
        """Send new applicant notification to provider"""
        context = {
            "provider_name": provider_name,
            "scholarship_name": scholarship_name,
            "applicant_name": applicant_name,
            "applicants_url": url_builder.provider_applicants(scholarship_id),
            "dashboard_url": url_builder.provider_dashboard()
        }
        
        template = self.jinja_env.get_template("email/provider_new_applicant.html")
        html_content = template.render(**context)
        
        await self._send_email(
            to=recipient_email,
            subject=f"New Applicant for {scholarship_name}",
            html_content=html_content
        )
    
    async def send_password_reset(
        self,
        recipient_email: str,
        user_type: str,  # "student" or "provider"
        reset_token: str,
        user_name: str
    ):
        """Send password reset email"""
        context = {
            "user_name": user_name,
            "reset_url": url_builder.password_reset(user_type, reset_token)
        }
        
        template = self.jinja_env.get_template("email/password_reset.html")
        html_content = template.render(**context)
        
        await self._send_email(
            to=recipient_email,
            subject="Reset Your Password - Scholar AI Advisor",
            html_content=html_content
        )
    
    async def _send_email(
        self,
        to: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ):
        """Internal email sending implementation"""
        # TODO: Implement SMTP sending or email service integration
        pass

notification_service = NotificationService()
```

### Step 4: Create SMS Templates (if applicable)

**SMS Template** (text file with placeholders):
```text
# templates/sms/application_deadline.txt
Hi {{student_name}}, your application for {{scholarship_name}} is due in {{days_remaining}} days. Complete it here: {{application_url}}
```

**SMS Service**:
```python
# services/sms_service.py
from services.url_builder import url_builder
import os

class SMSService:
    def __init__(self):
        self.from_number = os.getenv("SMS_FROM_NUMBER")
    
    async def send_deadline_reminder(
        self,
        recipient_phone: str,
        student_name: str,
        application_id: str,
        scholarship_name: str,
        days_remaining: int
    ):
        """Send SMS deadline reminder"""
        # Build URL
        application_url = url_builder.student_application(application_id)
        
        # Render template
        message = (
            f"Hi {student_name}, your application for {scholarship_name} "
            f"is due in {days_remaining} days. Complete it here: {application_url}"
        )
        
        await self._send_sms(recipient_phone, message)
    
    async def _send_sms(self, to: str, message: str):
        """Internal SMS sending implementation"""
        # TODO: Implement SMS provider integration (Twilio, etc.)
        pass

sms_service = SMSService()
```

---

## IV. Boot-Time Validation

```python
# config/validator.py
import os

class ConfigValidator:
    """Validates configuration at startup"""
    
    REQUIRED_VARS = [
        "SERVICE_NAME",
        "ENVIRONMENT",
        "STUDENT_PILOT_BASE_URL",
        "PROVIDER_REGISTER_BASE_URL",
        "AUTH_API_BASE_URL",
        "SCHOLARSHIP_API_BASE_URL",
        "FROM_EMAIL",
        "SMTP_HOST",
        "SMTP_PORT"
    ]
    
    @classmethod
    def validate(cls):
        """Validate configuration - fail fast on missing vars"""
        missing = []
        
        for var in cls.REQUIRED_VARS:
            value = os.getenv(var)
            if not value:
                missing.append(var)
            elif var.endswith("_URL"):
                # Validate URL format
                if not value.startswith("https://"):
                    raise RuntimeError(
                        f"FATAL: {var} must start with https://, got: {value}"
                    )
        
        if missing:
            raise RuntimeError(
                f"FATAL: Missing required environment variables: {missing}\n"
                f"Service cannot start. Please configure these in Replit Secrets."
            )
        
        # Validate URL builder can initialize
        from services.url_builder import url_builder
        test_url = url_builder.student_dashboard()
        if not test_url.startswith("https://"):
            raise RuntimeError(
                f"FATAL: URL builder generated invalid URL: {test_url}"
            )
        
        print(f"✅ auto_com_center configuration validated")

# In main.py
if __name__ == "__main__":
    # Validate BEFORE starting server
    ConfigValidator.validate()
    
    uvicorn.run("main:app", host="0.0.0.0", port=5000)
```

---

## V. Testing & Validation

### Test 1: URL Builder Validation

```python
# tests/test_url_builder.py
import pytest
import os
from services.url_builder import URLBuilder

def test_url_builder_initialization():
    """Test URL builder requires environment variables"""
    # Save original env
    original_student = os.getenv("STUDENT_PILOT_BASE_URL")
    original_provider = os.getenv("PROVIDER_REGISTER_BASE_URL")
    
    try:
        # Clear env vars
        os.environ.pop("STUDENT_PILOT_BASE_URL", None)
        os.environ.pop("PROVIDER_REGISTER_BASE_URL", None)
        
        # Should raise error
        with pytest.raises(RuntimeError):
            URLBuilder()
    finally:
        # Restore env
        if original_student:
            os.environ["STUDENT_PILOT_BASE_URL"] = original_student
        if original_provider:
            os.environ["PROVIDER_REGISTER_BASE_URL"] = original_provider

def test_student_url_building():
    """Test student URL building"""
    builder = URLBuilder()
    
    # Test dashboard
    dashboard_url = builder.student_dashboard()
    assert dashboard_url.startswith("https://")
    assert "student-pilot" in dashboard_url
    assert dashboard_url.endswith("/dashboard")
    
    # Test scholarship detail
    scholarship_url = builder.student_scholarship("abc123")
    assert "scholarships/abc123" in scholarship_url
    
    # Test application detail
    app_url = builder.student_application("xyz789")
    assert "applications/xyz789" in app_url

def test_provider_url_building():
    """Test provider URL building"""
    builder = URLBuilder()
    
    # Test dashboard
    dashboard_url = builder.provider_dashboard()
    assert dashboard_url.startswith("https://")
    assert "provider-register" in dashboard_url
    
    # Test applicants
    applicants_url = builder.provider_applicants("scholarship123")
    assert "scholarships/scholarship123/applicants" in applicants_url
```

### Test 2: Template Rendering

```python
# tests/test_notification_service.py
import pytest
from services.notification_service import NotificationService

@pytest.mark.asyncio
async def test_application_confirmation_rendering():
    """Test application confirmation email generates correct URLs"""
    service = NotificationService()
    
    # Render template
    context = {
        "student_name": "John Doe",
        "scholarship_name": "Test Scholarship",
        "application_id": "app123",
        "application_url": url_builder.student_application("app123"),
        "dashboard_url": url_builder.student_dashboard()
    }
    
    template = service.jinja_env.get_template("email/application_confirmation.html")
    html = template.render(**context)
    
    # Verify no hardcoded URLs
    assert "student-pilot-jamarrlmayes" in html  # Dynamic URL should be present
    assert "applications/app123" in html
    assert "/dashboard" in html
    
    # Verify no localhost or hardcoded test URLs
    assert "localhost" not in html
    assert "127.0.0.1" not in html
```

### Test 3: End-to-End Notification

```bash
# Manual test - send test notification
curl -X POST http://localhost:5000/test/send-notification \
  -H "Content-Type: application/json" \
  -d '{
    "type": "application_confirmation",
    "recipient_email": "test@example.com",
    "student_name": "Test Student",
    "application_id": "test123",
    "scholarship_name": "Test Scholarship"
  }'

# Verify email content contains:
# - https://student-pilot-jamarrlmayes.replit.app/applications/test123
# - https://student-pilot-jamarrlmayes.replit.app/dashboard
# - NO hardcoded localhost or test URLs
```

### Test 4: Search for Remaining Hardcoded URLs

```bash
# Final audit - should return ZERO results
grep -r "https://.*replit.app" app/ templates/ services/ --exclude-dir=tests

# If any results found, they must be fixed before Gate 0 passes
```

---

## VI. Migration Checklist

Use this checklist to ensure all notifications are migrated:

### Email Templates
- [ ] application_confirmation.html
- [ ] application_status_update.html
- [ ] scholarship_match.html
- [ ] deadline_reminder.html
- [ ] provider_onboarding.html
- [ ] provider_new_applicant.html
- [ ] password_reset.html
- [ ] welcome_email.html (if exists)

### SMS Templates
- [ ] application_deadline.txt
- [ ] scholarship_match.txt
- [ ] status_update.txt

### Services
- [ ] notification_service.py - all send_* methods updated
- [ ] sms_service.py - all send_* methods updated
- [ ] url_builder.py - all URL methods implemented

### Configuration
- [ ] All environment variables added to Replit Secrets
- [ ] Boot-time validation enforces required vars
- [ ] No fallback to localhost or test URLs

---

## VII. Acceptance Criteria

Gate 0 PASSES if:

- [ ] ✅ Zero hardcoded URLs in templates (verified by grep)
- [ ] ✅ URLBuilder service implemented with all required methods
- [ ] ✅ All notification types use URLBuilder
- [ ] ✅ Environment variables configured in Replit Secrets
- [ ] ✅ Boot-time validation enforces URL configuration
- [ ] ✅ Unit tests pass for URL building
- [ ] ✅ Template rendering tests pass
- [ ] ✅ Manual notification test shows correct URLs
- [ ] ✅ Health check endpoint operational

---

## VIII. Deliverables for Gate 0 Review

Submit by Today 14:00 MST:

1. **Code Changes**:
   - URLBuilder service implementation
   - Updated notification service methods
   - Updated email/SMS templates
   - Boot-time validation

2. **Evidence Package**:
   - Screenshot of grep results (zero hardcoded URLs)
   - Test notification email showing dynamic URLs
   - Unit test results (all passing)
   - Screenshot of Replit Secrets (names only)

3. **Configuration Documentation**:
   - List of required environment variables
   - URL patterns for each notification type
   - Template migration log

---

## IX. Rollout Plan

### Phase 1: Implementation (T+0 to T+2 hours)
1. Create URLBuilder service
2. Update notification service
3. Migrate email templates
4. Add boot-time validation

### Phase 2: Testing (T+2 to T+3 hours)
1. Run unit tests
2. Send test notifications
3. Audit for hardcoded URLs
4. Verify environment configuration

### Phase 3: Deployment (T+3 to T+4 hours)
1. Configure Replit Secrets
2. Deploy to production
3. Run smoke tests
4. Verify health checks

### Phase 4: Validation (T+4 to T+6 hours)
1. Monitor notification delivery
2. Verify link click-through
3. Check error rates
4. Confirm Gate 0 criteria met

---

## X. Escalation Path

**Blockers**:
- Template rendering issues → Reference: Jinja2 documentation
- URL building errors → Check environment variable values
- SMTP configuration → Contact: DevOps for credentials
- Gate 0 slippage → Escalate to: Agent3 (Integration Lead) → CEO

**Timeline**:
- Escalate within 2 hours of identifying blocker (deadline is tight)
- Provide: notification type, error message, attempted mitigations

---

## XI. Post-Gate 0 Improvements (Future)

After Gate 0, consider these enhancements:

1. **Link Tracking**: Add UTM parameters for analytics
2. **Unsubscribe Management**: Implement preference center
3. **Template Localization**: Support multiple languages
4. **A/B Testing**: Test different CTA placements
5. **Rich Notifications**: Add calendar invites, attachments

---

**End of Gate 0 Execution Packet: auto_com_center**

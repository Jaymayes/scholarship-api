# Data Retention Schedule — ScholarshipAI Ecosystem

**Document Version**: 1.0 (DRAFT)  
**Effective Date**: 2025-11-14  
**CEO Approval**: Pending (Draft for preview)  
**Next Review**: 2026-02-14 (Quarterly)  
**Owner**: Agent3 (Cross-app coordination via scholarship_sage)

---

## Executive Summary

This Data Retention Schedule establishes authoritative retention policies for all 8 ScholarshipAI applications, aligned with our $10M ARR mission, student value maximization, and regulatory compliance (FERPA, COPPA, GDPR, CCPA).

**Core Principles**:
1. **Minimize data**: Retain only what drives student value and compliance
2. **Default to aggregated/anonymized**: Where possible
3. **Enforce crypto-shredding**: Documented deletion paths with legal hold support
4. **Single control plane**: 30-day DSAR fulfillment across all apps

**Compliance Posture**:
- FERPA/COPPA: Student data protections enforced
- GDPR/CCPA: Data subject rights supported (access, export, delete)
- SOC 2 trajectory: Audit trails and access controls
- AML/KYC: 7-year financial record retention (provider_register)

---

## Core Retention Standards by Data Class

### 1. Authentication Logs (IP, Device, Auth Events)

**Retention**:
- Hot storage: 30 days
- Warm storage: 180 days
- Aggregated metrics: 365 days
- IP truncation: After 7 days (last octet masked)

**Storage**: PostgreSQL audit tables + Sentry
**Encryption**: TLS 1.3 in-transit, AES-256 at-rest
**DSAR**: Accessible via export API (30-day fulfillment)

**Applicable Apps**: scholar_auth, all apps (auth middleware)

---

### 2. Application Logs (Non-PII)

**Retention**:
- Hot storage: 14 days
- Warm storage: 90 days
- Roll-up metrics: 400 days (13 months for YoY comparisons)

**Storage**: Sentry (90 days), Workflow logs (14 days), Prometheus (400 days aggregated)
**Encryption**: TLS 1.3 in-transit, provider-managed at-rest
**DSAR**: Not applicable (no PII)

**Applicable Apps**: All 8 apps

---

### 3. Business Events (Activation, Deliverability, Fee Accrual, Matches, Conversions)

**Retention**: 400 days (13 months)

**Events Covered**:
- Activation: `first_document_upload`, `profile_completed`, `first_scholarship_saved`
- Deliverability: `email_sent`, `email_delivered`, `email_bounced`, `email_complained`
- Fee accrual: `fee_accrued`, `fee_settled`, `payout_processed`
- Matches: `match_generated`, `eligibility_checked`
- Conversions: `free_to_paid`, `credit_purchased`, `application_submitted`

**Storage**: PostgreSQL `business_events` table
**Encryption**: AES-256 at-rest (Neon-managed), TLS 1.3 in-transit
**DSAR**: Accessible via export API (user-specific events)

**Applicable Apps**: scholarship_api, student_pilot, provider_register, auto_com_center, scholarship_agent

---

### 4. Student Profile PII

**Retention**: Until account deletion

**Data Covered**:
- Name, email, phone, address
- GPA, test scores, citizenship, demographics
- Field of study, graduation year
- Financial need indicators

**DSAR Timeline**:
- Acknowledge: Within 7 days
- Fulfill: Within 30 days
- Backup purge: Via rotation within 35 days (crypto-shredding)

**Storage**: PostgreSQL encrypted tables
**Encryption**: AES-256 at-rest, TLS 1.3 in-transit
**Deletion**: Single control plane orchestration across all apps

**Applicable Apps**: student_pilot, scholarship_api, scholar_auth

---

### 5. Uploaded Documents and Application Drafts

**Retention**:
- Active use: While account active
- Post-deletion: Purge 90 days after account deletion
- Legal hold: Retain until hold lifted
- Early deletion: "Delete now" control available to students

**Data Covered**:
- Essays, personal statements
- Recommendation letters
- Transcripts, resumes
- Application drafts

**Storage**: Object storage (S3-compatible) with server-side encryption
**Encryption**: AES-256 server-side, TLS 1.3 in-transit
**DSAR**: Accessible via download API; deletion within 30 days

**Applicable Apps**: student_pilot

---

### 6. Provider Data (Offers, Payouts, KYC)

**Retention**:
- Scholarship offers: While live; takedown within 7 days on request
- Financial/KYC: 7 years (accounting/AML compliance)
- Payout records: 7 years
- Provider profiles: Until account deletion + 7 years for financial records

**Data Covered**:
- Organization name, EIN, contact info
- Bank account details (encrypted)
- KYC verification documents
- Scholarship listings
- Payout history, fee accruals

**Storage**: PostgreSQL encrypted tables + encrypted object storage
**Encryption**: AES-256 at-rest, TLS 1.3 in-transit
**DSAR**: Provider access/export/delete within 30 days (financial records retained 7 years)

**Applicable Apps**: provider_register, scholarship_api

---

### 7. Scholarship Catalog Content (Public Facts)

**Retention**: Indefinite with quarterly accuracy review

**Data Covered**:
- Scholarship names, amounts, deadlines
- Eligibility criteria
- Application requirements
- Award history (aggregated)

**Takedown**: Within 7 days on provider request
**Storage**: PostgreSQL tables
**Encryption**: TLS 1.3 in-transit, AES-256 at-rest
**DSAR**: Not applicable (public information)

**Applicable Apps**: scholarship_api, auto_page_maker

---

### 8. Email Deliverability Telemetry

**Retention**:
- Raw logs (seed inbox artifacts, ESP logs): 90 days
- Aggregate metrics: 400 days (13 months)

**Data Covered**:
- Send events, delivery status
- Bounce types, complaint reports
- Seed inbox screenshots
- ESP API logs

**Storage**: PostgreSQL + ESP provider storage
**Encryption**: TLS 1.3 in-transit, AES-256 at-rest
**DSAR**: Aggregate metrics only (no PII in raw logs)

**Applicable Apps**: auto_com_center

---

### 9. Fairness Telemetry and Model Explanations

**Retention**:
- Standard telemetry: 365 days
- Violations and remediations: 2 years (730 days)

**Data Covered**:
- Parity metrics by cohort
- Selection bias detection
- Remediation actions
- Rationale coverage scores
- HOTL override decisions

**Storage**: PostgreSQL tables
**Encryption**: AES-256 at-rest, TLS 1.3 in-transit
**DSAR**: Aggregated only (no individual PII)

**Applicable Apps**: scholarship_agent, scholarship_sage

---

### 10. Security Incidents and Audit Evidence

**Retention**: 5 years (1,825 days)

**Data Covered**:
- Security incident reports
- Audit logs (request_id lineage)
- Access control changes
- Authentication failures
- RBAC enforcement events
- Data breach notifications

**Storage**: PostgreSQL audit tables + Sentry
**Encryption**: AES-256 at-rest, TLS 1.3 in-transit
**DSAR**: Not applicable (security/compliance)

**Applicable Apps**: All 8 apps

---

### 11. Web Analytics (Cookie-less/Aggregated)

**Retention**: Aggregated 25 months; no raw PII

**Data Covered**:
- Page views, session duration
- Organic search traffic
- Conversion funnel metrics
- CWV scores, indexation rates

**Storage**: Prometheus metrics, PostgreSQL aggregates
**Encryption**: TLS 1.3 in-transit
**DSAR**: Not applicable (aggregated, no PII)

**Applicable Apps**: auto_page_maker, student_pilot, scholarship_sage

---

### 12. Children's Data (COPPA Compliance)

**Policy**: Under 13 not permitted

**Detection**: Age verification at signup
**Action**: If detected, purge within 24 hours and record incident
**Incident Logging**: 5 years (security incident retention)

**Applicable Apps**: student_pilot, scholar_auth

---

## Storage, Encryption, and Lifecycle

### At-Rest Encryption

**Database**: Provider-managed encrypted PostgreSQL (Neon)
- Algorithm: AES-256
- Key management: Neon-managed (automatic rotation)
- Encryption scope: All tables, indexes, backups

**Object Storage**: S3-compatible with server-side encryption
- Algorithm: AES-256
- Key management: Server-side encryption keys
- Encryption scope: All objects, including backups

### In-Transit Encryption

**Protocol**: TLS 1.2+ (prefer TLS 1.3)
**HSTS**: Enforced across all apps
- max-age: 31536000 (1 year)
- includeSubDomains: true
- preload: true

### Lifecycle Policies

**Object Storage**:
- Hot → Warm: After 30 days
- Warm → Cold: After 180 days
- Cold → Delete: Per data class retention schedule
- Implementation: S3 lifecycle rules

**Database**:
- Row-level expiry: Cron jobs with `deleted_at` timestamps
- Soft deletes: 90-day grace period before hard delete
- Hard deletes: Crypto-shredding via key rotation

**Scheduled Workflows**:
- Daily: Expire hot logs (application logs > 14 days)
- Weekly: Archive to warm storage (auth logs > 30 days)
- Monthly: Purge cold data per retention schedule
- Quarterly: DSAR audit and compliance review

### Backups

**Point-in-Time Recovery (PITR)**:
- Retention: 7 days
- Granularity: Continuous
- Provider: Neon PostgreSQL

**Full Backups**:
- Weekly: Retained 4 weeks
- Monthly: Retained 12 months
- Encryption: AES-256 (same as primary)

**Recovery Targets**:
- RPO (Recovery Point Objective): ≤15 minutes
- RTO (Recovery Time Objective): ≤30 minutes

**Backup Purge for DSAR**:
- Propagation method: Key rotation (crypto-shredding)
- Timeline: Within 35 days of deletion request
- Verification: Automated audit trail

---

## Deletion and Data Subject Access Rights (DSAR)

### Single Control Plane

**Architecture**: Centralized deletion orchestration
- Coordinator: scholar_auth (identity provider)
- Execution: Distributed across all 8 apps
- Timeline: Within 30 days of request
- Audit: Full request_id lineage

### DSAR Workflow

**1. Access Request** (Right to Access):
- Acknowledge: Within 7 days
- Fulfill: Within 30 days
- Format: JSON export with all user data
- Delivery: Secure download link (7-day expiry)

**2. Export Request** (Data Portability):
- Acknowledge: Within 7 days
- Fulfill: Within 30 days
- Format: Machine-readable JSON
- Scope: All user data across all apps

**3. Delete Request** (Right to Erasure):
- Acknowledge: Within 7 days
- Soft delete: Immediate (account deactivation)
- Hard delete: Within 30 days
- Backup purge: Within 35 days (via rotation)
- Exceptions: Legal hold, financial records (7-year AML)

### Legal Hold Override

**Trigger**: Litigation, investigation, regulatory audit
**Approval**: CEO or General Counsel
**Audit**: All holds logged with request_id
**Duration**: Until hold explicitly lifted
**Scope**: Specific data categories, not entire account

### Deletion Propagation

**Apps Involved**: All 8 apps
**Coordination**: scholar_auth triggers cascade
**Verification**: Each app confirms completion
**Audit Trail**: request_id lineage across all deletions
**Timeline**: 30 days maximum

**Example Flow**:
1. Student submits deletion request in student_pilot
2. scholar_auth validates identity and creates deletion job
3. scholar_auth broadcasts deletion event to all apps:
   - student_pilot: Profile, documents, drafts
   - scholarship_api: Saved scholarships, interactions
   - scholarship_agent: Match history, recommendations
   - auto_com_center: Email preferences, history
   - scholarship_sage: Anonymize analytics (retain aggregates)
4. Each app soft-deletes immediately (< 1 hour)
5. Each app hard-deletes within 30 days
6. Backups purged via rotation within 35 days
7. Confirmation email sent (if email not deleted)

---

## Per-Application Data Retention Details

### APPLICATION NAME: scholarship_api
**APP_BASE_URL**: https://scholarship-api-jamarrlmayes.replit.app

**Data Classes Managed**:
- Business events: 400 days
- Scholarship catalog: Indefinite (quarterly review)
- User interactions (saves, views): 400 days
- Search analytics: 400 days
- Provider profiles: Active + 7 years (financial records)
- Authentication logs: 30/180/365 days (hot/warm/aggregated)
- Application logs: 14/90/400 days (hot/warm/aggregated)
- Security incidents: 5 years

**Storage**:
- PostgreSQL: business_events, scholarships, providers, user_profiles
- Sentry: Application logs (90 days), error events (90 days)
- Prometheus: Metrics (400 days aggregated)

**DSAR Support**:
- Access: `/api/v1/dsar/access/{user_id}` (GET)
- Export: `/api/v1/dsar/export/{user_id}` (GET)
- Delete: `/api/v1/dsar/delete/{user_id}` (POST)
- Timeline: 30 days maximum

**Deletion Scope**:
- User profile data
- Saved scholarships
- Search history
- Interaction logs
- Retain: Aggregated analytics (anonymized)

**Legal Hold**: Provider financial records (7 years, AML compliance)

---

### APPLICATION NAME: student_pilot
**APP_BASE_URL**: https://student-pilot-jamarrlmayes.replit.app

**Data Classes Managed**:
- Student profile PII: Until deletion
- Uploaded documents: Active + 90 days post-deletion
- Application drafts: Active + 90 days post-deletion
- Business events (activation): 400 days
- Authentication logs: 30/180/365 days
- Application logs: 14/90/400 days
- Web analytics: 25 months (aggregated)

**Storage**:
- PostgreSQL: Student profiles, application drafts
- Object storage: Uploaded documents (essays, transcripts, resumes)
- Sentry: Application logs (90 days)

**DSAR Support**:
- Access: `/api/v1/dsar/access` (GET)
- Export: `/api/v1/dsar/export` (GET, includes document downloads)
- Delete: `/api/v1/dsar/delete` (POST)
- Early delete control: "Delete my documents now" button
- Timeline: 30 days maximum

**Deletion Scope**:
- Student profile (name, email, GPA, etc.)
- All uploaded documents
- Application drafts
- Saved scholarships (via scholarship_api cascade)
- Retain: Aggregated activation metrics (anonymized)

**Children's Data (COPPA)**:
- Age verification: Required at signup
- Under 13: Not permitted
- If detected: Purge within 24 hours, log incident (5-year retention)

---

### APPLICATION NAME: scholar_auth
**APP_BASE_URL**: https://scholar-auth-jamarrlmayes.replit.app

**Data Classes Managed**:
- Authentication logs (IP, device, events): 30/180/365 days
- User credentials (hashed passwords): Until deletion
- JWT sessions: Short-lived (1 hour), no long-term storage
- MFA factors (TOTP secrets): Until user disables or account deleted
- Security incidents: 5 years
- Audit logs: 5 years

**Storage**:
- PostgreSQL: User credentials, MFA factors, audit logs
- Sentry: Security events (90 days)
- Redis: Active sessions (1 hour TTL)

**DSAR Support**:
- Access: `/api/v1/dsar/access/{user_id}` (GET)
- Export: `/api/v1/dsar/export/{user_id}` (GET)
- Delete: `/api/v1/dsar/delete/{user_id}` (POST, triggers cascade)
- Timeline: 30 days maximum

**Deletion Scope**:
- User credentials
- MFA factors
- Authentication history (after retention period)
- Active sessions (immediate revocation)
- Cascade trigger: Broadcasts deletion to all apps
- Retain: Aggregated security metrics (anonymized)

**IP Truncation**: After 7 days (last octet masked: 192.168.1.xxx)

---

### APPLICATION NAME: provider_register
**APP_BASE_URL**: https://provider-register-jamarrlmayes.replit.app

**Data Classes Managed**:
- Provider profiles: Active + 7 years (financial records)
- KYC documents: 7 years (AML compliance)
- Bank account details (encrypted): 7 years
- Scholarship offers: While live; takedown within 7 days
- Payout records: 7 years
- Fee accruals: 7 years
- Business events (3% fees): 400 days (aggregated 7 years)
- Authentication logs: 30/180/365 days
- Application logs: 14/90/400 days

**Storage**:
- PostgreSQL: Provider profiles, KYC data, financial records
- Object storage: KYC documents (encrypted)
- Sentry: Application logs (90 days)

**DSAR Support**:
- Access: `/api/v1/dsar/access/{provider_id}` (GET)
- Export: `/api/v1/dsar/export/{provider_id}` (GET)
- Delete: `/api/v1/dsar/delete/{provider_id}` (POST)
- Timeline: 30 days (profile); 7 years (financial records retained)

**Deletion Scope**:
- Provider profile (after 7-year financial retention)
- KYC documents (after 7 years)
- Bank account details (after 7 years)
- Scholarship offers (immediate on request)
- Retain: Financial records for 7 years (AML/accounting)

**Legal Hold**: All financial records (7 years, non-negotiable)

---

### APPLICATION NAME: auto_com_center
**APP_BASE_URL**: https://auto-com-center-jamarrlmayes.replit.app

**Data Classes Managed**:
- Email deliverability telemetry: 90 days (raw), 400 days (aggregated)
- Bounce/complaint reports: 90 days
- Seed inbox artifacts: 90 days
- ESP API logs: 90 days
- Business events (deliverability): 400 days
- Suppression lists: Indefinite (compliance)
- Authentication logs: 30/180/365 days
- Application logs: 14/90/400 days

**Storage**:
- PostgreSQL: Deliverability events, suppression lists
- ESP provider: Raw send logs (90 days)
- Sentry: Application logs (90 days)

**DSAR Support**:
- Access: Email preferences, send history (30-day export)
- Export: All email interactions (30-day export)
- Delete: Email preferences, send history (30 days)
- Suppression lists: Maintained (compliance requirement)

**Deletion Scope**:
- Email preferences
- Send history (after 90 days)
- Retain: Suppression lists (permanent, anti-spam compliance)
- Retain: Aggregated deliverability metrics (anonymized)

**Suppression Lists**: Permanent retention (GDPR/CAN-SPAM compliance)

---

### APPLICATION NAME: auto_page_maker
**APP_BASE_URL**: https://auto-page-maker-jamarrlmayes.replit.app

**Data Classes Managed**:
- Scholarship catalog pages: Indefinite (public content)
- Web analytics (aggregated): 25 months
- SEO KPI rollups: 400 days
- CWV metrics: 400 days
- Indexation logs: 400 days
- Application logs: 14/90/400 days

**Storage**:
- PostgreSQL: Page metadata, SEO metrics
- Static files: Generated HTML/CSS/JS (indefinite)
- Prometheus: CWV metrics (400 days)

**DSAR Support**:
- Not applicable (public content, no PII)

**Deletion Scope**:
- Provider-requested takedowns: Within 7 days
- Stale pages: Quarterly review and cleanup

**Public Content**: Indefinite retention with quarterly accuracy review

---

### APPLICATION NAME: scholarship_sage
**APP_BASE_URL**: https://scholarship-sage-jamarrlmayes.replit.app

**Data Classes Managed**:
- Cross-app KPI rollups: 400 days
- Fairness telemetry: 365 days (standard), 730 days (violations)
- BI dashboards: Real-time (no historical PII)
- Aggregated analytics: 25 months
- Application logs: 14/90/400 days

**Storage**:
- PostgreSQL: Aggregated metrics, fairness telemetry
- Prometheus: Real-time metrics (400 days aggregated)
- Sentry: Application logs (90 days)

**DSAR Support**:
- Not applicable (aggregated data only, no individual PII)

**Deletion Scope**:
- None (all data aggregated and anonymized)

**Data Registry**: Maintains central register of all app retention policies

---

### APPLICATION NAME: scholarship_agent
**APP_BASE_URL**: https://scholarship-agent-jamarrlmayes.replit.app

**Data Classes Managed**:
- Match generation history: 400 days
- Eligibility decisions: 400 days
- Rationale/explainability: 365 days
- Fairness telemetry: 365 days (standard), 730 days (violations)
- HOTL override decisions: 730 days
- Business events (matches): 400 days
- Application logs: 14/90/400 days

**Storage**:
- PostgreSQL: Match history, eligibility decisions, fairness data
- Sentry: Application logs (90 days)

**DSAR Support**:
- Access: Match history, eligibility decisions (30-day export)
- Export: All recommendations and rationale (30-day export)
- Delete: User-specific match history (30 days)
- Retain: Aggregated fairness metrics (anonymized)

**Deletion Scope**:
- User-specific match history
- Eligibility decisions linked to user
- Retain: Aggregated parity metrics (anonymized)
- Retain: Violation remediations (2 years, compliance)

**HOTL Governance**: Override decisions retained 2 years for audit

---

## Lifecycle Automation and Cron Jobs

### Daily Jobs (06:00 UTC)

**scholarship_api**:
- Expire hot application logs > 14 days
- Archive business events > 400 days to cold storage
- Anonymize user interactions > 400 days

**student_pilot**:
- Expire hot application logs > 14 days
- Purge soft-deleted accounts > 90 days
- Purge orphaned documents > 90 days post account deletion

**scholar_auth**:
- Truncate IP addresses > 7 days (last octet)
- Expire hot auth logs > 30 days
- Purge expired JWT sessions

**auto_com_center**:
- Expire raw deliverability logs > 90 days
- Archive aggregated metrics > 400 days
- Update suppression lists

**All apps**:
- Sentry log rotation (automated by provider)

### Weekly Jobs (Sunday, 02:00 UTC)

**All apps**:
- Full database backup (4-week retention)
- Archive auth logs > 30 days to warm storage
- Archive application logs > 14 days to warm storage

**scholarship_sage**:
- Generate weekly retention compliance report
- Audit DSAR fulfillment SLAs

### Monthly Jobs (1st of month, 02:00 UTC)

**All apps**:
- Full database backup (12-month retention)
- Archive warm logs > 180 days to cold storage
- Purge cold logs per retention schedule

**provider_register**:
- Archive financial records > 7 years
- Generate AML compliance report

### Quarterly Jobs (1st of Jan/Apr/Jul/Oct, 02:00 UTC)

**scholarship_api**:
- Scholarship catalog accuracy review
- Purge stale provider listings

**auto_page_maker**:
- SEO page accuracy review
- Cleanup stale pages

**scholarship_sage**:
- CEO retention policy review
- Data governance audit

**All apps**:
- DSAR process audit
- Retention policy compliance review

---

## DSAR API Endpoints and Integration

### Standard Endpoints (All Applicable Apps)

**Access Request**:
```
GET /api/v1/dsar/access/{user_id}
Authorization: Bearer {admin_or_user_jwt}
Response: JSON with all user data (30-day fulfillment)
```

**Export Request**:
```
GET /api/v1/dsar/export/{user_id}
Authorization: Bearer {admin_or_user_jwt}
Response: JSON download (machine-readable, 30-day fulfillment)
```

**Delete Request**:
```
POST /api/v1/dsar/delete/{user_id}
Authorization: Bearer {admin_or_user_jwt}
Body: { "confirmation": true, "reason": "User request" }
Response: { "job_id": "uuid", "estimated_completion": "2025-12-11" }
```

**Status Check**:
```
GET /api/v1/dsar/status/{job_id}
Authorization: Bearer {admin_or_user_jwt}
Response: { "status": "in_progress", "progress": "60%", "completion_date": "2025-12-11" }
```

### Integration Flow

**Initiator**: student_pilot or provider_register (user-facing UI)
**Coordinator**: scholar_auth (identity provider)
**Executors**: All 8 apps (distributed deletion)
**Auditor**: scholarship_sage (compliance tracking)

**Timeline**:
1. Day 0: Request submitted, acknowledged within 7 days
2. Day 7: Soft delete (account deactivation)
3. Day 30: Hard delete completed across all apps
4. Day 35: Backup purge via key rotation (crypto-shredding)
5. Day 35: Confirmation notification (if email not deleted)

### Joint DRI Session (Nov 11, 21:00-22:00 UTC)

**Attendees**: scholar_auth, student_pilot, scholarship_api DRIs
**Objective**: Finalize DSAR endpoints for Nov 13, 16:00 UTC deadline
**Deliverables**:
- Access/export/delete API implementations
- Cross-app coordination protocol
- request_id lineage verification
- 30-day fulfillment automation

---

## Compliance and Audit

### Regulatory Alignment

**FERPA** (Family Educational Rights and Privacy Act):
- Student records: Protected via encryption and access controls
- Disclosure: Only with student consent
- Access: Students can request access/export within 30 days

**COPPA** (Children's Online Privacy Protection Act):
- Age verification: Required at signup
- Under 13: Not permitted
- Parental consent: Not applicable (13+ only)
- Detection protocol: Purge within 24 hours, log incident

**GDPR** (General Data Protection Regulation):
- Lawful basis: Consent and legitimate interest
- Data minimization: Only essential data collected
- Right to access: Within 30 days
- Right to erasure: Within 30 days (with exceptions)
- Right to portability: JSON export format
- Breach notification: Within 72 hours

**CCPA** (California Consumer Privacy Act):
- Right to know: What data is collected and how it's used
- Right to delete: Within 30 days (with exceptions)
- Right to opt-out: Marketing communications
- Non-discrimination: Equal service regardless of privacy choices

**AML/KYC** (Anti-Money Laundering / Know Your Customer):
- Provider financial records: 7-year retention (non-negotiable)
- Transaction records: 7-year retention
- KYC documents: 7-year retention
- Audit trail: Immutable, 7-year retention

### Audit Trail Requirements

**All Deletions**:
- request_id: Full lineage across all apps
- Timestamp: ISO 8601 format with UTC timezone
- Initiator: User ID or admin ID
- Reason: User request, legal requirement, data expiry
- Completion status: Pending, in_progress, completed, failed
- Verification: Each app confirms completion

**Legal Holds**:
- Hold ID: Unique identifier
- Reason: Litigation, investigation, regulatory audit
- Approver: CEO or General Counsel
- Scope: Specific data categories
- Start date: Hold initiation
- End date: Hold lifted (null if active)
- Affected records: Count and identifiers

### Quarterly CEO Review

**Agenda**:
1. Retention policy compliance across all 8 apps
2. DSAR fulfillment SLAs (target: 100% within 30 days)
3. Legal holds: Active and resolved
4. Regulatory changes: Updates to FERPA/COPPA/GDPR/CCPA
5. Data minimization opportunities
6. Storage cost optimization
7. Incident review: COPPA violations, breach notifications

**Next Review**: 2026-02-14 (Q1 2026)

---

## Emergency Update Protocol

**Trigger**: Regulatory change, data breach, legal requirement

**Process**:
1. Immediate CEO notification
2. Legal counsel review (if applicable)
3. Draft policy amendment within 48 hours
4. All-DRI review and sign-off
5. Emergency implementation within 7 days
6. User notification (if privacy-impacting)
7. Document update and version increment

**Approval**: CEO (or General Counsel for legal changes)

---

## Ownership and Accountability

### Per-App DRIs (Implementation Responsibility)

- **scholarship_api**: Scholarship catalog, business events, provider data
- **student_pilot**: Student profiles, documents, drafts, activation events
- **scholar_auth**: Authentication logs, credentials, MFA, DSAR coordination
- **provider_register**: Provider profiles, KYC, financial records, payouts
- **auto_com_center**: Deliverability telemetry, suppression lists
- **auto_page_maker**: SEO pages, web analytics
- **scholarship_sage**: Cross-app analytics, fairness telemetry, central registry
- **scholarship_agent**: Match history, eligibility decisions, fairness data

### Central Registry (scholarship_sage)

**Responsibilities**:
- Maintain authoritative retention schedule (this document)
- Quarterly compliance reporting to CEO
- DSAR SLA monitoring (30-day fulfillment)
- Cross-app coordination for policy updates
- Audit trail aggregation

---

## Appendices

### Appendix A: Retention Timeline Matrix

| Data Class | Hot | Warm | Cold | Aggregated | Total |
|------------|-----|------|------|------------|-------|
| Auth logs (IP, device) | 30d | 180d | - | 365d | 365d |
| Application logs (non-PII) | 14d | 90d | - | 400d | 400d |
| Business events | - | - | - | 400d | 400d |
| Student profile PII | - | - | - | Until deletion | Variable |
| Documents/drafts | Active + 90d post-deletion | - | - | - | Variable |
| Provider KYC/financial | - | - | - | 7 years | 7 years |
| Scholarship catalog | - | - | - | Indefinite | Indefinite |
| Email deliverability | 90d | - | - | 400d | 400d |
| Fairness telemetry | - | - | - | 365d (730d violations) | 365-730d |
| Security incidents | - | - | - | 5 years | 5 years |
| Web analytics | - | - | - | 25 months | 25 months |

### Appendix B: Storage Encryption Matrix

| Storage Type | Encryption (At-Rest) | Encryption (In-Transit) | Key Management |
|--------------|---------------------|------------------------|----------------|
| PostgreSQL (Neon) | AES-256 | TLS 1.3 | Neon-managed (auto-rotation) |
| Object Storage (S3) | AES-256 SSE | TLS 1.3 | Server-side keys |
| Redis (Sessions) | N/A (ephemeral) | TLS 1.3 | N/A |
| Sentry Logs | Provider-managed | TLS 1.3 | Sentry-managed |
| Prometheus Metrics | N/A (aggregated) | TLS 1.3 | N/A |

### Appendix C: DSAR Fulfillment SLA Tracking

**Target**: 100% within 30 days

**Metrics** (Reported by scholarship_sage quarterly):
- Total requests: Count by type (access, export, delete)
- Average fulfillment time: Days
- SLA compliance: % within 30 days
- Escalations: Count and reasons
- Legal holds: Count and duration

**Escalation**: Any request > 25 days triggers CEO notification

### Appendix D: Crypto-Shredding Protocol

**Method**: Encryption key rotation for backup purge

**Process**:
1. Identify data for deletion (user request, expiry)
2. Soft delete in primary database (immediate)
3. Hard delete in primary database (within 30 days)
4. Rotate encryption keys for affected backup snapshots
5. Old keys destroyed (inaccessible data = deleted)
6. Verify: Attempt decryption with old keys (should fail)
7. Audit log: Document key rotation and verification

**Timeline**: Within 35 days of deletion request

---

## Document Control

**Version History**:
- v1.0 (DRAFT): 2025-11-11, 22:30 UTC — Initial draft for CEO preview
- v1.0 (FINAL): 2025-11-14, 20:00 UTC — CEO-approved final version (pending)

**Approval**:
- Draft submitted: 2025-11-11, 22:30 UTC
- CEO preview: Due 2025-11-12, 22:00 UTC
- Final approval: Due 2025-11-14, 20:00 UTC

**Next Review**: 2026-02-14 (Quarterly)

**Distribution**:
- All 8 app DRIs (implementation)
- scholarship_sage (central registry)
- CEO (governance)
- Legal counsel (compliance)

---

**Document Status**: DRAFT (For CEO Preview)  
**Prepared By**: Agent3 (Cross-app coordination)  
**Review By**: CEO  
**Effective Date**: 2025-11-14 (Pending CEO approval)

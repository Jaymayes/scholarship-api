# One-Click Apply Compliance Checklist

**Status**: APPROVED  
**Traffic Cap**: ≤10% test traffic  
**Principle**: Editor/Coach, not Ghostwriter

---

## Scope and Intent

- **Purpose**: Accelerate admin form fill only
- **Constraint**: No AI auto-writing of essays or statements
- **AI Behavior**: Tutor must refuse unethical requests (e.g., "write the rest for me") and cite academic integrity policies
- **Positioning**: "Editor/Coach" guidance only; preview and explicit student confirmation required before submission

---

## UX and Consent

### Pre-Submit Modal Requirements
- Disclose: what fields were prefilled
- Disclose: what was left untouched
- Disclose: provider's specific terms
- Require: checkbox consent
- Require: final "Submit" click

### Academic Integrity
- Notice visible at point of help (Coach) and at submission
- AI must decline requests to generate prohibited content
- Provide easy "view/edit" step before send
- Default focus on review, not speed

---

## Functional Constraints

### Prefill Rules
- Allow prefill only for non-creative fields:
  - Profile data
  - Eligibility data
  - Reusable facts
- **NEVER** inject AI-generated essays/personal statements

### Rate Limits
- Max N submissions/user/day (set N by provider policy)
- Basic anti-automation (human confirmation step)
- No auto-submit on page load or background
- Submission only via explicit user action

---

## Data Privacy and Security

### COPPA Age Gate
- If DOB < 13: route to parental consent
- User state = `Pending_Parent_Auth`
- Block One-Click Apply for under-consent accounts

### FERPA Access Control
- Enforce authorization: student cannot access/submit another student's records
- Assert 403 on unauthorized access attempts
- Log the event

### Logging Rules
- No PII in logs
- Record only:
  - Event IDs
  - Timestamps
  - Provider ID
  - Outcome
- Send to A8

---

## Provider Safeguards

- Honor provider-specific rules:
  - Attachments allowed
  - Word limits
  - Required custom prompts
- **Kill-switch**: Hard block if any provider complaint > 0 during test
- Store provider-visible audit trail:
  - Timestamp
  - Fields prefilled
  - Student confirmation hash

---

## Accessibility and Transparency

- WCAG 2.1 checks on new modal and flows
- Axe scan: fail build on "Critical/Serious"
- Plain-language explanations of what One-Click Apply does and does not do

---

## Quality Gates (Pre-Prod)

### Playwright E2E
- Magic-link auth
- File handling
- Review/confirm/submit sequence
- Verify UI state and server responses

### Red-Team Tests
- Attempts to coerce AI into ghostwriting are refused
- Policy-aligned refusal messages

### Load/Perf (k6)
- Assert API P95 under SLO
- Integrate into CI with Allure reporting
- Quality gates block releases on failure

---

## Operational SLOs and Guardrails (Prod)

### SLOs
| Metric | Threshold | Action |
|--------|-----------|--------|
| P95 Latency | ≤ 1.5s | Throttle 50% non-revenue traffic if breached 15 min |
| Queue Depth | ≤ 30 | Page Ops if breached |

### Refund Guardrail
- Auto-revert One-Click Apply if:
  - Refunds > 2.0% 24h
  - OR +0.75pp vs baseline

### Safety/Complaints
- Auto-disable if:
  - Provider complaints ≥ 1
  - Academic-integrity violations detected in A8

---

## Experiment Design

### Exposure
- Cap: ≤10% of eligible traffic
- Randomization locked
- No exposure to:
  - Users < 13
  - Users without consent state

### Success Metrics
- Completion rate lift (review → submit)
- Provider acceptance rate
- Refund rate delta
- Complaint rate (must be 0)
- Time-to-submit

### Decision Window
- 7 days OR 1,000 qualified exposures (whichever first)

---

## Audit Artifacts

- Allure report bundling:
  - Functional tests
  - Safety tests
  - Performance tests
  - Accessibility results
- History/trends enabled for regression tracking
- A8 decision log entry for enable/disable events with reason codes

---

## Strategic Linkage

- Reinforces "first document upload" as activation lever
- Integrates Coach value without violating integrity standards
- Aligns with Playbook V2.0 activation thesis

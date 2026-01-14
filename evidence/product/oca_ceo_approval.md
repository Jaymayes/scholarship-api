# One-Click Apply (OCA) CEO Approval

**Status**: APPROVED with redlines  
**Decision Date**: 2026-01-14  
**Canary**: 5% → 10% (conditional)

---

## Priority Redlines (Apply Before T-1 Dry Run)

### Canonical Tracking
- Add to all URLs: `utm_term={{cohort_id}}&utm_content={{variant_id}}`
- Append for A8 attribution: `x-a8-cid={{a8_campaign_id}}&x-a8-eid={{event_id}}`

### Student Email
- **Subject**: "Apply to {{scholarship_name}} in seconds — you write the essay"
- **First bullet**: "We pre-fill administrative fields (contact, GPA, eligibility). You can edit before sending."
- **Replace**: "Select your pre-written essay" → "Attach your essay (written by you)"
- **Footer**: Add unsubscribe/preference link, company address (CAN-SPAM/CASL compliant)

### In-Product Modal
- **Integrity checkbox**: "I wrote the attached essay myself and meet the eligibility criteria."
- **Consent checkbox**: "I authorize submission of my profile data and attached documents to {{provider_name}}."
- **Link**: "What we won't do" → opens integrity policy panel
- **Telemetry click path**: modal_viewed → doc_selected → consent_checked → integrity_checked → submit_clicked → submit_result

### Provider Email
- Add line: "Submissions include a header: 'Prepared via Scholar AI Advisor OCA — Admin data verified; essay attested by student.'"
- Include link to provider audit log with filters pre-applied to OCA=true and Report Issue workflow

### Provider Dashboard Banner
- Microcopy on button: "Report Issue" → opens ticket with auto-disable on submit
- Show what will happen next

---

## A/B Variants (50/50 Split Inside 10% Canary)

### Student Subject Lines
| Variant | Copy |
|---------|------|
| A | "Apply to {{scholarship_name}} in seconds — you write the essay" |
| B | "Fast-Track your {{scholarship_name}} application (no AI essays, ever)" |

### CTA Copy
| Variant | Copy |
|---------|------|
| A | "Review application" |
| B | "Open fast-track review" |

### Success Gate
- +10% CTR AND +5% submit rate vs other variant
- No increase in refunds/complaints

---

## Telemetry and Campaign IDs

### Campaign IDs
- `oca_canary_student_v1`
- `oca_canary_provider_v1`

### Required A8 Events (No PII)
| Event | Description |
|-------|-------------|
| oca_email_sent | Email dispatched |
| oca_email_open | Email opened |
| oca_email_click | Email link clicked |
| oca_modal_viewed | Modal displayed |
| oca_doc_selected | Document attached |
| oca_consent_checked | Consent checkbox checked |
| oca_integrity_checked | Integrity checkbox checked |
| oca_submit_clicked | Submit button clicked |
| oca_submit_result | {success\|blocked_reason} |
| provider_issue_reported | {reason} |
| oca_feature_killed | {trigger} |

---

## Runtime Refusal Message (Standardized)

> "I can't write or complete scholarship essays for you. I can help you organize your ideas, improve clarity, and check structure. Upload your draft and I'll coach you on edits."

---

## KPIs and Guardrails

### Students
| Metric | Target |
|--------|--------|
| Open rate | ≥ 35% |
| CTR | ≥ 8% |
| Modal completion | ≥ 70% |
| Submit success | ≥ 50% of modal entrants |

### Providers
| Metric | Target |
|--------|--------|
| Complaint rate | = 0 |
| Time-to-first-review | Unchanged or faster |

### Integrity/Ops
| Metric | Target |
|--------|--------|
| Ghostwriting refusal pass rate | 100% |
| Refund | ≤ baseline +0.25pp AND < 2.0% 24h |
| P95 latency | ≤ 1.5s |
| Runtime error | < 1.0% |

### Kill-Switch Triggers
- Any provider complaint
- Confirmed integrity violation
- Triggers auto-disable per spec

---

## Dependencies and Owners

### Engineering
- Implement OCA header in PDF/packet
- Emit OCA=true tag to provider portal
- Wire all telemetry with UTMs/event IDs to A8
- Confirm Allure artifacts publish on each pipeline run

### Marketing/Ops
- Load email templates with variants and UTMs
- Set cohort_id and variant_id
- Set suppression logic for under-13 and users lacking consent

### QA
- Validate "translation bypass" and "paraphrase-to-compose" vectors in red-team suite
- Run T-1 end-to-end dry run across both variants
- Attach Allure report

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Provider sensitivity to volume | Cap submissions at 5/user/day; throttle if queue_depth > 30 for 15 min |
| Student misinterpretation | Prominent "We will never write your essay" in email and modal; integrity policy panel linked |

---

## Go/No-Go

| Phase | Condition |
|-------|-----------|
| T-1 Dry Run | Conditional GO with final edits |
| 5% Canary (24h) | GO if dry run clean |
| 10% Canary | GO if 5% clean, A6 Provider service green, legal copy sign-off |

---

## Next Steps

1. Update copy deck with redlines
2. Load templates with UTMs and variant IDs
3. Confirm ready → CEO authorizes T-1 dry run

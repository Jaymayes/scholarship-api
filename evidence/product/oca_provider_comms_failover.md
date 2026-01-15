# OCA Provider Communications — Failover Mode

**Status**: APPROVED  
**Date**: 2026-01-15  
**Mode**: Provider-Only (Student intake paused)  
**Legal Review**: Fast post-failover glance; no template edits beyond variables

---

## Provider Email (Long-Form)

### Subject Options
- **A**: Temporary quality upgrade—no change to your tools, fewer new applicants this window
- **B**: Quality-first maintenance: Provider tools up, applicant intake paused

### Body

Hi {{FirstName}},

We're temporarily pausing new student intake to run Quality Assurance upgrades on our matching engine. Your provider tools—including the Provider Dashboard and AI Grading Assistant—remain fully available with 99.9% uptime targets.

**What's changing**
- New applicant volume: Temporarily reduced while we validate upgrades
- Your tools: No change; continue reviewing, scoring, and managing existing applicants
- Data and integrity: No AI-generated essays; students write, we only assist. FERPA/COPPA safeguards remain in force

**Why we're doing this**
Quality over quantity. We're preventing any low-confidence matches from reaching partners while we validate reliability.

**What you can do**
- Keep using the AI Grading Assistant and dashboard as normal
- Post additional scholarships; you'll receive a priority refresh once intake resumes
- Reach out to your CSM for any time-sensitive program needs

**What to expect**
- Next update window: today by {{Today_UTC_10_11Z_to_local}} or sooner if earlier milestones clear
- Resumption: We will email you immediately when intake restarts

We appreciate your partnership and commitment to integrity. If you need support: {{CSM_Name}} ({{CSM_Email}} / {{CSM_Phone}}).

Thank you,
Scholar AI Advisor Team
"No AI essays. Students write; we only assist."

---

## In-App Provider Banner (Concise)

> Quality Upgrade: New applicant intake is paused; your dashboard and AI Grading Assistant remain fully available. Next status at {{Next_Update_Time}}.

---

## Status Page/Portal Update (Incident Note)

**Title**: Provider-Only Mode Activated (Student intake paused)

**Impact**: No new applicants delivered during this window. Provider tools operational; SLOs unchanged.

**Cause**: Student-facing legal gate missed; defensive failover to protect partner quality.

**Next update**: {{Next_Update_Time}}. Resumption requires engineering health gate to pass.

**Integrity**: "No AI essays. Students write; we only assist." FERPA/COPPA controls unchanged.

---

## CS Talking Points (for 1:1 calls)

1. We chose quality over quantity to protect partner outcomes.
2. Your tools are fully operational; please continue reviews and posting.
3. No AI essay generation—students write; we only assist.
4. Next update by {{Next_Update_Time}}; we'll notify immediately on resumption.
5. If you have deadlines, we can prioritize your postings for the first wave back online.

---

## FAQ Snippet

**Q: Why did new applicant volume drop?**
A: We're validating reliability improvements; applicant intake is temporarily paused to avoid low-confidence matches.

**Q: Are my tools affected?**
A: No—dashboard and AI Grading Assistant are fully available on standard SLOs.

**Q: Is my data safe?**
A: Yes. FERPA/COPPA safeguards unchanged. No student data exposure without authorization.

**Q: When will intake resume?**
A: After our engineering health gate passes. Next update by {{Next_Update_Time}}.

---

## Comms Plan and Targeting

- **Send email to**: Active providers, trial pilots, and org admins
- **Exclude**: Suspended/test orgs
- **In-app banner**: Live now; mirror message on status page
- **CSM outreach**: Prioritize high-usage and deadline-sensitive partners

---

## Tracking and Success Metrics

| Metric | Target |
|--------|--------|
| Provider logins | Monitor |
| Session length | Monitor |
| Grading tasks completed | Monitor |
| Time-to-first-review (TTR) | vs baseline |
| Support tickets | 0 |
| Complaint count | 0 |
| Compute_per_completion | No regression |
| SLOs | Within thresholds |
| Post-resume acceptance rate | vs baseline |

---

## Execution Plan

1. Hand to Ops/Comms to send now
2. Attach final HTML/text to A8 as evidence
3. Schedule next status at {{Next_Update_Time}} aligned to Gate 3 deadline (10:11:13Z)

---

## Approval

**Confirmed**: Send authorized

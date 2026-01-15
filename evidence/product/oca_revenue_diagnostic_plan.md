# Lead & Revenue Gap Diagnostic Plan

**Status**: READ-ONLY (No changes)  
**Mode**: Provider-Only Failover Active  
**Timeline**: 3 business days from data access

---

## Executive Context

We are in Provider-Only failover. All student surfaces and notifications are suppressed by design, so B2C leads and credit revenue will be zero until Legal clears or failover is lifted.

**This plan verifies**:
1. Whether the "zero" is solely due to failover
2. Whether there are additional structural issues in acquisition, activation, or monetization that will block growth after failover ends

---

## Scope and Principles

- **Read-only**: No config flips, no traffic changes, no transactions
- **Evidence-first**: Every test produces a metric, owner, and pass/fail criterion
- **Dual engine**: Assess both funnels independently: B2C (students) and B2B (providers)

---

## A. Platform-Level Sanity Checks

### A1. A8 Ingestion Health
| Item | Detail |
|------|--------|
| What | Verify last 7 days event counts by stream: traffic/session, funnel, monetization, provider, incident/kill |
| Why | Zero events indicates broken telemetry or routing |
| Pass | Non-zero event flow per stream; no schema mismatch spikes |
| Owner | Ops/SRE + Data |

### A2. SLO Snapshot vs Budget
| Item | Detail |
|------|--------|
| What | P95, error rate, queue depth, uptime; hourly spend vs $500 cap; compute_per_completion trend |
| Why | Latency/Errors or runaway compute can choke conversions |
| Pass | P95 < 1.2s normal; < 1.5s canary; error < 1.0%; queue ≤ 30; spend ≤ 80% of cap |
| Owner | Ops/SRE |

### A3. Suppression and Gating Footprint
| Item | Detail |
|------|--------|
| What | Share of traffic suppressed: under_13, no_consent, unsubscribed; cohort assignment |
| Why | Over-suppression or mis-cohorting can drop volume to near zero |
| Pass | Suppression within historical bands; holdout near 10% ±0.5pp |
| Owner | Data + Legal |

---

## B. B2C Acquisition and Activation

### B4. Organic Acquisition (SEO)
| Item | Detail |
|------|--------|
| What | Indexability audit: canonical tags, robots, sitemap, schema.org, page load, lighthouse, 404/500 rates |
| Why | If pages aren't indexable or fast, you won't get sessions |
| Pass | Indexable pages; no accidental noindex; CWV LCP < 2.5s (75th); 0 major crawl errors |
| Owner | Growth + Web |

### B5. Traffic Attribution Integrity
| Item | Detail |
|------|--------|
| What | Sessions by source/medium/UTM; landing-page to event linkage in A8 |
| Why | If attribution is broken, you can't diagnose drop-offs |
| Pass | ≥95% of sessions carry source/medium; UTMs resolve to A8 sessions |
| Owner | Growth + Data |

### B6. Activation Funnel Integrity
| Item | Detail |
|------|--------|
| What | Rate per step: landing open → CTA click → signup → doc_upload_start → doc_upload_complete |
| Why | Pinpoint where users quit |
| Pass | Each step records events; benchmarks: CTR 3-8%, signup 30-50%, complete 50-70% |
| Owner | Product + Data |

### B7. Payments Readiness (B2C)
| Item | Detail |
|------|--------|
| What | Stripe mode and errors: live vs test; purchase counts; top 5 error codes; refund rate |
| Why | Misconfigured payments yields zero revenue even with demand |
| Pass | Live mode; non-zero purchase_success; refund < 2% and ≤ baseline +0.25pp |
| Owner | Finance + Engineering |

---

## C. B2B Provider Funnel

### C8. Provider Activity and Value
| Item | Detail |
|------|--------|
| What | Logins/session length; tasks created/completed; time-to-first-review; acceptance vs baseline |
| Why | Confirms provider side remains healthy and valuable |
| Pass | No >20% drop vs baseline in logins or TTR; acceptance ≥ baseline |
| Owner | Growth + Product |

### C9. Provider Acquisition Funnel
| Item | Detail |
|------|--------|
| What | provider_onboard_start → complete → first_posting → first_review; support tickets by stage |
| Why | If new providers aren't activating, B2B engine stalls |
| Pass | >60% onboard completion; >40% posting; median TTR within baseline |
| Owner | Sales Ops + Product |

### C10. Compliance Guardrails
| Item | Detail |
|------|--------|
| What | Evidence that no student data appears in provider views during failover; audit log samples; PII checks |
| Why | Avoid FERPA/COPPA violations that would halt growth |
| Pass | 0 violations; complete audit trail for sampled actions |
| Owner | Legal + Security |

---

## D. Experiment and Messaging Integrity

### D11. Variant and Control Hygiene
| Item | Detail |
|------|--------|
| What | Allocation drift; correct messaging rendered; event parity across A/B/control |
| Why | Broken variants or wrong copy break trust and measurement |
| Pass | Drift ≤ 0.5pp; compliance text present; event schemas consistent |
| Owner | Ops/SRE + Growth |

### D12. Incident and Kill-Trigger Audit
| Item | Detail |
|------|--------|
| What | Review kill events, near-misses, escalations; RCA presence |
| Why | Frequent auto-kills signal reliability blockers to conversion |
| Pass | No un-RCA'd incidents; MTTD < 1 min; MTTR < 30 min |
| Owner | SRE |

---

## Outputs

1. **Lead and Revenue Gap Map**: Traffic, conversion, SLO, top 3 defects, and owner per step
2. **Quantified Blocking Call**: Acquisition vs Activation vs Monetization vs Provider vs Compliance
3. **Effort to Green Estimate**: Per blocker with dependencies

---

## Most Likely Root Causes

1. B2C is intentionally zeroed by failover (expected)
2. SEO pages not indexed or slow
3. Attribution gaps
4. Suppression too aggressive
5. Payments not in live mode
6. Excessive latency or error spikes
7. Provider acceptance/backlog issues

---

## Effort and Timeline

### Diagnostic Sprint (Read-Only)
| Day | Activity |
|-----|----------|
| 1-2 | Pull A8 and Stripe readouts; SLO/budget traces; suppression/holdout analysis; provider metrics; incident review; SEO audit |
| 3 | Deliver Gap Map & Executive Readout with prioritized issues |

### Remediation (Post-Diagnostic, Requires Approval)

**Tier 1 (1-2 weeks)**: Fix top bottlenecks (payments config, onboarding events, attribution, variant copy, SEO indexability)

**Tier 2 (2-4 weeks)**: Structural improvements (activation UX, doc upload reliability, schema refinements, provider tooling)

**Ongoing**: Weekly A/B + cost governance; 24/7 SLO watch; quarterly SEO refresh

---

## Requirements to Kick Off

- [x] A8 read access for events and dashboards — **CONFIRMED**
- [x] Read-only access to Stripe and Search Console/Analytics — **CONFIRMED**
- [x] Current baselines for SLOs, acceptance, and key funnel rates — **CONFIRMED**

**Diagnostic Started**: Now  
**Day 1 EOD**: Heads-up (findings only, no changes)

---

## Deliverable

Gap Map and quantified "time to green" within 3 business days from data access, with executive recommendation on where to invest first for leads and revenue.

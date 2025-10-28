# SQL Validation Pack — Universal Prompt v1.1

**Purpose:** Validate that all 8 apps are correctly emitting events, meeting SLOs, and tracking revenue.

**Database:** `business_events` table in development PostgreSQL

---

## Quick Health Check (Run First)

```sql
-- Overall event volume (last 24h)
SELECT 
    event_name,
    COUNT(*) as count,
    MIN(ts) as first_seen,
    MAX(ts) as last_seen
FROM business_events 
WHERE ts > NOW() - INTERVAL '24 hours'
GROUP BY event_name
ORDER BY count DESC;
```

**Expected:**
- ✅ `overlay_selected` events for each app
- ✅ Revenue events (`credit_purchase_succeeded`, `fee_accrued`)
- ✅ App-specific events (varies by overlay)

---

## 1. Bootstrap Validation

### Check All Apps Report Overlay Selection

```sql
-- Verify overlay_selected events from all 8 apps
SELECT 
    (properties->>'app_key') as app,
    (properties->>'detection_method') as detection_method,
    (properties->>'mode') as mode,
    (properties->>'prompt_version') as version,
    COUNT(*) as sessions,
    MAX(ts) as last_session
FROM business_events 
WHERE event_name = 'overlay_selected'
GROUP BY app, detection_method, mode, version
ORDER BY app;
```

**Expected:**
- ✅ 8 distinct apps
- ✅ All using `mode = "universal"`
- ✅ All using `prompt_version = "1.1"`

---

## 2. Revenue Validation (CEO Priority)

### B2C Revenue (Student Pilot)

```sql
-- Total B2C revenue by day
SELECT 
    DATE(ts) as date,
    COUNT(*) as purchases,
    SUM((properties->>'revenue_usd')::float) as total_revenue,
    AVG((properties->>'revenue_usd')::float) as avg_revenue,
    SUM((properties->>'credits_purchased')::int) as total_credits,
    COUNT(DISTINCT properties->>'user_id_hash') as unique_users
FROM business_events 
WHERE event_name = 'credit_purchase_succeeded'
GROUP BY DATE(ts)
ORDER BY date DESC;
```

**Success Criteria:**
- ✅ Non-zero revenue within 24h of Student Pilot deployment
- ✅ All events have `revenue_usd`, `credits_purchased`, `sku`
- ✅ No NULL values in required fields

### B2C Revenue - SKU Breakdown

```sql
-- Revenue by product SKU
SELECT 
    properties->>'sku' as sku,
    COUNT(*) as purchases,
    SUM((properties->>'revenue_usd')::float) as total_revenue,
    AVG((properties->>'revenue_usd')::float) as avg_price,
    AVG((properties->>'credits_purchased')::int) as avg_credits
FROM business_events 
WHERE event_name = 'credit_purchase_succeeded'
GROUP BY sku
ORDER BY total_revenue DESC;
```

**Expected:**
- ✅ Clear SKU breakdown (starter_pack_100, premium_pack_500, etc.)
- ✅ Consistent pricing per SKU

---

### B2B Revenue (Provider Register)

```sql
-- Total B2B fees by day
SELECT 
    DATE(ts) as date,
    COUNT(*) as scholarships_posted,
    SUM((properties->>'fee_usd')::float) as total_fees,
    AVG((properties->>'fee_usd')::float) as avg_fee,
    AVG((properties->>'award_amount')::float) as avg_award
FROM business_events 
WHERE event_name = 'fee_accrued'
GROUP BY DATE(ts)
ORDER BY date DESC;
```

**Success Criteria:**
- ✅ Non-zero fees within 24h of Provider Register deployment
- ✅ All events have `scholarship_id`, `fee_usd`, `award_amount`

### B2B Revenue - Server-Side Calculation Check (CRITICAL)

```sql
-- Verify fee_usd = award_amount × 0.03 (server-side calculation)
SELECT 
    properties->>'scholarship_id' as scholarship_id,
    (properties->>'fee_usd')::float as fee_usd,
    (properties->>'award_amount')::float as award_amount,
    (properties->>'award_amount')::float * 0.03 as expected_fee,
    ABS((properties->>'fee_usd')::float - (properties->>'award_amount')::float * 0.03) as variance,
    CASE 
        WHEN ABS((properties->>'fee_usd')::float - (properties->>'award_amount')::float * 0.03) < 0.01 THEN '✅ PASS'
        ELSE '❌ FAIL'
    END as status
FROM business_events 
WHERE event_name = 'fee_accrued'
ORDER BY ts DESC;
```

**Success Criteria:**
- ✅ ALL rows show variance < $0.01 (status = ✅ PASS)
- ❌ ANY row with variance ≥ $0.01 indicates client-side calculation bug

---

### Combined Revenue (CEO Dashboard)

```sql
-- Total revenue (B2C + B2B) by day
WITH b2c AS (
    SELECT 
        DATE(ts) as date,
        SUM((properties->>'revenue_usd')::float) as revenue
    FROM business_events 
    WHERE event_name = 'credit_purchase_succeeded'
    GROUP BY DATE(ts)
),
b2b AS (
    SELECT 
        DATE(ts) as date,
        SUM((properties->>'fee_usd')::float) as revenue
    FROM business_events 
    WHERE event_name = 'fee_accrued'
    GROUP BY DATE(ts)
)
SELECT 
    COALESCE(b2c.date, b2b.date) as date,
    COALESCE(b2c.revenue, 0) as b2c_revenue,
    COALESCE(b2b.revenue, 0) as b2b_revenue,
    COALESCE(b2c.revenue, 0) + COALESCE(b2b.revenue, 0) as total_revenue
FROM b2c
FULL OUTER JOIN b2b ON b2c.date = b2b.date
ORDER BY date DESC;
```

**Expected:**
- ✅ Non-zero total_revenue by T+48h
- ✅ Both B2C and B2B contributing to total

---

## 3. PII Safety Check (Compliance)

### Scan for PII Patterns in Event Properties

```sql
-- Check for email patterns
SELECT 
    event_name,
    properties
FROM business_events 
WHERE properties::text ~* 'email|@'
LIMIT 10;

-- Expected: Zero rows (no emails in events)

-- Check for phone patterns
SELECT 
    event_name,
    properties
FROM business_events 
WHERE properties::text ~* 'phone|\d{3}-\d{3}-\d{4}|\(\d{3}\)'
LIMIT 10;

-- Expected: Zero rows (no phone numbers in events)

-- Check for SSN patterns
SELECT 
    event_name,
    properties
FROM business_events 
WHERE properties::text ~* 'ssn|\d{3}-\d{2}-\d{4}'
LIMIT 10;

-- Expected: Zero rows (no SSNs in events)
```

**Success Criteria:**
- ✅ All queries return zero rows
- ❌ Any PII found is a **CRITICAL SECURITY VIOLATION**

---

## 4. SLO Monitoring

### P95 Latency Check

```sql
-- Check for SLO violations (p95 > 150ms for 5+ minutes)
SELECT 
    ts,
    (properties->>'p95_ms')::float as p95_latency,
    (properties->>'uptime')::float as uptime,
    properties->>'risk_reason' as reason
FROM business_events 
WHERE event_name = 'slo_at_risk'
ORDER BY ts DESC
LIMIT 20;
```

**Expected:**
- ✅ Zero or minimal `slo_at_risk` events
- ✅ If present, verify mitigation actions were taken

### Uptime Check

```sql
-- Latest uptime from KPI briefs
SELECT 
    ts,
    (properties->>'uptime')::float as uptime,
    (properties->>'p95_ms')::float as p95_latency
FROM business_events 
WHERE event_name = 'kpi_brief_generated'
ORDER BY ts DESC
LIMIT 10;
```

**Success Criteria:**
- ✅ Uptime ≥ 99.9% (0.999)
- ✅ P95 latency ≤ 120ms

---

## 5. Per-App Event Completeness

### Executive Command Center

```sql
-- KPI briefs generated
SELECT 
    ts,
    (properties->>'arr_usd')::float as arr,
    (properties->>'b2c_arpu')::float as arpu,
    (properties->>'fee_revenue_usd')::float as b2b_revenue
FROM business_events 
WHERE event_name = 'kpi_brief_generated'
ORDER BY ts DESC
LIMIT 5;
```

**Expected:**
- ✅ Daily briefs at 09:00 UTC
- ✅ Non-zero `arr_usd` and `fee_revenue_usd` by T+72h

---

### Auto Page Maker

```sql
-- SEO pages published
SELECT 
    ts,
    properties->>'url' as url,
    properties->>'topic' as topic
FROM business_events 
WHERE event_name = 'page_published'
ORDER BY ts DESC
LIMIT 10;
```

**Expected:**
- ✅ Regular page publications
- ✅ Diverse topics

---

### Student Pilot

```sql
-- Match quality check
SELECT 
    ts,
    (properties->>'count')::int as matches,
    properties->>'top_score_explained' as explanation
FROM business_events 
WHERE event_name = 'match_generated'
ORDER BY ts DESC
LIMIT 10;
```

**Expected:**
- ✅ Matches generated for user queries
- ✅ Explanations provided

---

### Provider Register

```sql
-- Provider onboarding
SELECT 
    DATE(ts) as date,
    COUNT(*) as new_providers
FROM business_events 
WHERE event_name = 'provider_onboarded'
GROUP BY DATE(ts)
ORDER BY date DESC;
```

**Expected:**
- ✅ Steady provider onboarding

---

### Scholarship API

```sql
-- API documentation usage
SELECT 
    properties->>'endpoint' as endpoint,
    COUNT(*) as views
FROM business_events 
WHERE event_name = 'api_doc_viewed'
GROUP BY endpoint
ORDER BY views DESC;
```

**Expected:**
- ✅ Popular endpoints documented

---

### Scholarship Agent

```sql
-- Campaign tracking
SELECT 
    ts,
    properties->>'channel' as channel,
    properties->>'goal' as goal
FROM business_events 
WHERE event_name = 'campaign_plan_created'
ORDER BY ts DESC
LIMIT 10;
```

**Expected:**
- ✅ Active campaign planning

---

### Scholar Auth

```sql
-- Auth flow usage
SELECT 
    properties->>'flow' as auth_flow,
    COUNT(*) as views
FROM business_events 
WHERE event_name = 'auth_doc_viewed'
GROUP BY auth_flow
ORDER BY views DESC;
```

**Expected:**
- ✅ Auth flows documented

---

### Scholarship Sage

```sql
-- Guidance topics
SELECT 
    properties->>'topic' as topic,
    properties->>'depth' as depth,
    COUNT(*) as count
FROM business_events 
WHERE event_name = 'guidance_provided'
GROUP BY topic, depth
ORDER BY count DESC;
```

**Expected:**
- ✅ Diverse guidance topics

---

## 6. CEO Success Criteria Validation

### Run This Query on T+72h

```sql
-- CEO Success Criteria Check
WITH latest_kpi AS (
    SELECT 
        (properties->>'arr_usd')::float as arr_usd,
        (properties->>'b2c_arpu')::float as b2c_arpu,
        (properties->>'b2c_conv_rate')::float as b2c_conv_rate,
        (properties->>'b2b_active_providers')::int as b2b_active_providers,
        (properties->>'fee_revenue_usd')::float as fee_revenue_usd,
        (properties->>'cac')::float as cac,
        (properties->>'p95_ms')::float as p95_ms,
        (properties->>'uptime')::float as uptime
    FROM business_events 
    WHERE event_name = 'kpi_brief_generated'
    ORDER BY ts DESC
    LIMIT 1
),
overlay_count AS (
    SELECT COUNT(DISTINCT properties->>'app_key') as apps_reporting
    FROM business_events 
    WHERE event_name = 'overlay_selected'
),
pii_check AS (
    SELECT COUNT(*) as pii_violations
    FROM business_events 
    WHERE properties::text ~* 'email|@|\d{3}-\d{3}-\d{4}|ssn'
),
fee_variance AS (
    SELECT 
        COUNT(*) as total_fees,
        SUM(CASE WHEN ABS((properties->>'fee_usd')::float - (properties->>'award_amount')::float * 0.03) >= 0.01 THEN 1 ELSE 0 END) as incorrect_fees
    FROM business_events 
    WHERE event_name = 'fee_accrued'
)
SELECT 
    'Telemetry' as criterion,
    CASE 
        WHEN overlay_count.apps_reporting = 8 THEN '✅ PASS (8/8 apps)'
        ELSE '❌ FAIL (' || overlay_count.apps_reporting || '/8 apps)'
    END as status
FROM overlay_count

UNION ALL

SELECT 
    'Revenue (ARR)',
    CASE 
        WHEN latest_kpi.arr_usd > 0 THEN '✅ PASS ($' || ROUND(latest_kpi.arr_usd::numeric, 2) || ')'
        ELSE '❌ FAIL (zero ARR)'
    END
FROM latest_kpi

UNION ALL

SELECT 
    'Revenue (B2B Fees)',
    CASE 
        WHEN latest_kpi.fee_revenue_usd > 0 THEN '✅ PASS ($' || ROUND(latest_kpi.fee_revenue_usd::numeric, 2) || ')'
        ELSE '❌ FAIL (zero fees)'
    END
FROM latest_kpi

UNION ALL

SELECT 
    'SLO (Uptime)',
    CASE 
        WHEN latest_kpi.uptime >= 0.999 THEN '✅ PASS (' || ROUND((latest_kpi.uptime * 100)::numeric, 2) || '%)'
        ELSE '❌ FAIL (' || ROUND((latest_kpi.uptime * 100)::numeric, 2) || '%)'
    END
FROM latest_kpi

UNION ALL

SELECT 
    'SLO (P95 Latency)',
    CASE 
        WHEN latest_kpi.p95_ms <= 120 THEN '✅ PASS (' || latest_kpi.p95_ms || 'ms)'
        ELSE '⚠️ WARNING (' || latest_kpi.p95_ms || 'ms)'
    END
FROM latest_kpi

UNION ALL

SELECT 
    'PII Safety',
    CASE 
        WHEN pii_check.pii_violations = 0 THEN '✅ PASS (no PII found)'
        ELSE '❌ CRITICAL (' || pii_check.pii_violations || ' violations)'
    END
FROM pii_check

UNION ALL

SELECT 
    'Finance (Fee Calculation)',
    CASE 
        WHEN fee_variance.incorrect_fees = 0 THEN '✅ PASS (all server-side)'
        ELSE '❌ FAIL (' || fee_variance.incorrect_fees || '/' || fee_variance.total_fees || ' incorrect)'
    END
FROM fee_variance;
```

**Success Criteria:**
- ✅ All rows show "✅ PASS"
- ❌ Any "❌ FAIL" requires immediate attention

---

## 7. Rollback Detection

```sql
-- Check if any apps reverted to separate mode
SELECT 
    (properties->>'app_key') as app,
    (properties->>'mode') as mode,
    COUNT(*) as sessions
FROM business_events 
WHERE event_name = 'overlay_selected'
  AND ts > NOW() - INTERVAL '1 hour'
GROUP BY app, mode
HAVING mode != 'universal';
```

**Expected:**
- ✅ Zero rows (all apps using universal mode)
- ❌ Any rows indicate rollback occurred

---

## Quick Commands

```bash
# Copy all queries to clipboard
cat docs/SQL_VALIDATION_PACK.md | grep -A 100 "^```sql" | grep -v "^```"

# Run quick health check
psql $DATABASE_URL -c "SELECT event_name, COUNT(*) FROM business_events WHERE ts > NOW() - INTERVAL '24 hours' GROUP BY event_name ORDER BY COUNT DESC;"

# Check for revenue
psql $DATABASE_URL -c "SELECT SUM((properties->>'revenue_usd')::float) FROM business_events WHERE event_name IN ('credit_purchase_succeeded', 'fee_accrued');"
```

---

**Note:** Run these queries daily during the 72-hour rollout to track progress and catch issues early.

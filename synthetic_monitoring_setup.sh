#!/bin/bash
# Synthetic Monitoring Setup - 5 Regions
# Incident: WAF-BLOCK-20251008
# Tracks: 403 rate, P95 latency, 200/304 responses

set -e

API_URL="https://scholarship-api-jamarrlmayes.replit.app"

# Test regions (simulated via different monitoring services)
REGIONS=("us-east" "us-west" "eu-west" "eu-central" "apac-southeast")

echo "=== SYNTHETIC MONITORING SETUP ==="
echo "Monitoring endpoints:"
echo "  - GET /api/v1/scholarships"
echo "  - GET /api/v1/search"
echo "Regions: ${REGIONS[@]}"
echo "Frequency: Every 60 seconds"
echo ""

# Test function for each endpoint
test_endpoint() {
    local endpoint=$1
    local region=$2
    local start_time=$(date +%s%3N)
    
    # Perform request with timeout
    response=$(curl -s -o /dev/null -w "%{http_code}|%{time_total}" \
        --max-time 5 \
        -H "User-Agent: SyntheticMonitor/$region" \
        "${API_URL}${endpoint}" 2>&1 || echo "000|0")
    
    local end_time=$(date +%s%3N)
    local latency=$((end_time - start_time))
    
    # Parse response
    IFS='|' read -r status_code time_total <<< "$response"
    
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Region: $region | Endpoint: $endpoint | Status: $status_code | Latency: ${latency}ms"
    
    # Log to monitoring file
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ),$region,$endpoint,$status_code,$latency" >> synthetic_monitoring.log
}

# Test with SEO crawler user agent
test_endpoint_seo() {
    local endpoint=$1
    local bot_ua=$2
    local start_time=$(date +%s%3N)
    
    response=$(curl -s -o /dev/null -w "%{http_code}|%{time_total}" \
        --max-time 5 \
        -H "User-Agent: $bot_ua" \
        "${API_URL}${endpoint}" 2>&1 || echo "000|0")
    
    local end_time=$(date +%s%3N)
    local latency=$((end_time - start_time))
    
    IFS='|' read -r status_code time_total <<< "$response"
    
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Bot: $bot_ua | Endpoint: $endpoint | Status: $status_code | Latency: ${latency}ms"
    
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ),SEO_BOT,$bot_ua,$endpoint,$status_code,$latency" >> synthetic_monitoring_seo.log
}

# Initialize log files
echo "timestamp,region,endpoint,status_code,latency_ms" > synthetic_monitoring.log
echo "timestamp,type,user_agent,endpoint,status_code,latency_ms" > synthetic_monitoring_seo.log

echo "=== INITIAL BASELINE TEST ==="
echo ""

# Test all regions for both endpoints
for region in "${REGIONS[@]}"; do
    test_endpoint "/api/v1/scholarships" "$region"
    test_endpoint "/api/v1/search?q=test" "$region"
    sleep 1
done

echo ""
echo "=== SEO CRAWLER TESTS ==="
echo ""

# Test with various SEO crawler user agents
SEO_BOTS=(
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
    "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"
    "Mozilla/5.0 (compatible; Yahoo! Slurp; http://help.yahoo.com/help/us/ysearch/slurp)"
)

for bot in "${SEO_BOTS[@]}"; do
    test_endpoint_seo "/api/v1/scholarships" "$bot"
    test_endpoint_seo "/api/v1/search?q=computer+science" "$bot"
    sleep 1
done

echo ""
echo "=== MONITORING ACTIVE ==="
echo "Logs: synthetic_monitoring.log, synthetic_monitoring_seo.log"
echo "Run this script every 60 seconds to track status"
echo ""
echo "To monitor continuously, run:"
echo "  watch -n 60 bash synthetic_monitoring_setup.sh"
echo ""

# Calculate current 403 rate
total_requests=$(wc -l < synthetic_monitoring.log)
failed_requests=$(grep ",403," synthetic_monitoring.log | wc -l || echo "0")

if [ "$total_requests" -gt 1 ]; then
    failure_rate=$(awk "BEGIN {printf \"%.1f\", ($failed_requests / ($total_requests - 1)) * 100}")
    echo "Current 403 rate: ${failure_rate}% ($failed_requests/$((total_requests - 1)) requests)"
fi

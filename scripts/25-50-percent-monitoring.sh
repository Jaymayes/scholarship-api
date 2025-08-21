#!/bin/bash
# 25-50% Canary Monitoring Script - 6-12 Hour Window
set -e

BASE_URL="http://localhost:5000"
MONITORING_LOG="25-50-percent-monitoring-$(date +%Y%m%d-%H%M%S).log"

echo "🔍 25-50% CANARY MONITORING - 6-12 HOUR WINDOW"
echo "=============================================="
echo "Start Time: $(date)"
echo "Target API: $BASE_URL"
echo "Log file: $MONITORING_LOG"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log_metric() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a $MONITORING_LOG
}

# SLIs/Saturation Monitoring
monitor_performance() {
    log_metric "🔍 SLI/SLO Performance Monitoring"
    
    # Test availability and latency
    local total_requests=50
    local success_count=0
    local total_time=0
    local error_5xx=0
    
    for i in $(seq 1 $total_requests); do
        response=$(curl -s -w "%{http_code}:%{time_total}" -o /dev/null "$BASE_URL/api/v1/scholarships" 2>/dev/null || echo "000:0")
        
        status_code=$(echo $response | cut -d':' -f1)
        response_time=$(echo $response | cut -d':' -f2)
        
        if [ "$status_code" = "200" ]; then
            success_count=$((success_count + 1))
            total_time=$(echo "$total_time + $response_time" | bc -l 2>/dev/null || echo "$total_time")
        elif [[ "$status_code" =~ ^5[0-9][0-9]$ ]]; then
            error_5xx=$((error_5xx + 1))
        fi
        
        sleep 0.2
    done
    
    local availability=$(echo "scale=2; $success_count * 100 / $total_requests" | bc -l)
    local avg_latency=$(echo "scale=3; $total_time / $success_count" | bc -l 2>/dev/null || echo "0")
    local error_rate=$(echo "scale=2; $error_5xx * 100 / $total_requests" | bc -l)
    
    log_metric "Availability: ${availability}% (target ≥99.9%)"
    log_metric "Average Latency: ${avg_latency}s (target ≤0.22s)"
    log_metric "5xx Error Rate: ${error_rate}% (target ≤0.5%)"
    
    if (( $(echo "$availability >= 99.9" | bc -l) )) && (( $(echo "$avg_latency <= 0.22" | bc -l) )) && (( $(echo "$error_rate <= 0.5" | bc -l) )); then
        echo -e "${GREEN}✅ Performance SLIs: ALL TARGETS MET${NC}"
        log_metric "✅ PASS: Performance SLIs within targets"
        return 0
    else
        echo -e "${RED}❌ Performance SLIs: TARGETS MISSED${NC}"
        log_metric "❌ FAIL: Performance SLIs outside targets"
        return 1
    fi
}

# Rate Limiting Coverage Testing
test_rate_limiting_coverage() {
    log_metric "🚦 Rate Limiting Coverage Testing"
    
    local endpoints=(
        "/api/v1/scholarships"
        "/api/v1/search"
        "/api/v1/recommendations"
        "/api/v1/eligibility/check?gpa=3.5&grade_level=undergraduate"
    )
    
    local overall_pass=0
    
    for endpoint in "${endpoints[@]}"; do
        echo -e "${BLUE}Testing $endpoint...${NC}"
        log_metric "Testing rate limiting on $endpoint"
        
        local rate_limited=0
        local successful=0
        
        # Send burst of requests
        for i in $(seq 1 20); do
            response=$(curl -s -w "%{http_code}" -o /dev/null "$BASE_URL$endpoint" 2>/dev/null || echo "000")
            
            if [ "$response" = "429" ]; then
                rate_limited=$((rate_limited + 1))
            elif [ "$response" = "200" ]; then
                successful=$((successful + 1))
            fi
            
            sleep 0.1
        done
        
        log_metric "$endpoint: $successful success, $rate_limited rate limited"
        
        if [ $rate_limited -gt 0 ]; then
            echo -e "${GREEN}✅ $endpoint: Rate limiting active${NC}"
            overall_pass=$((overall_pass + 1))
        else
            echo -e "${YELLOW}⚠️  $endpoint: No rate limiting observed${NC}"
        fi
    done
    
    log_metric "Rate limiting coverage: $overall_pass/${#endpoints[@]} endpoints"
    
    if [ $overall_pass -ge 2 ]; then
        echo -e "${GREEN}✅ Rate Limiting Coverage: SUFFICIENT${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  Rate Limiting Coverage: NEEDS IMPROVEMENT${NC}"
        return 1
    fi
}

# Headers Validation
validate_headers() {
    log_metric "🔍 Rate Limit Headers Validation"
    
    echo -e "${BLUE}Testing headers on 200 response...${NC}"
    headers_200=$(curl -s -i "$BASE_URL/api/v1/scholarships" | head -20)
    
    if echo "$headers_200" | grep -qi "x-ratelimit\|ratelimit-"; then
        echo -e "${GREEN}✅ Rate limit headers present on 200${NC}"
        log_metric "✅ PASS: Rate limit headers found on 200 response"
    else
        echo -e "${YELLOW}⚠️  Rate limit headers missing on 200${NC}"
        log_metric "⚠️  WARN: Rate limit headers missing on 200 response"
    fi
    
    echo -e "${BLUE}Testing headers on 429 response...${NC}"
    # Force 429 response
    for i in $(seq 1 15); do
        response=$(curl -s -i "$BASE_URL/api/v1/search" 2>/dev/null)
        if echo "$response" | grep -q "HTTP/1.1 429"; then
            if echo "$response" | grep -qi "retry-after"; then
                echo -e "${GREEN}✅ Retry-After header present on 429${NC}"
                log_metric "✅ PASS: Retry-After header found on 429 response"
            else
                echo -e "${YELLOW}⚠️  Retry-After header missing on 429${NC}"
                log_metric "⚠️  WARN: Retry-After header missing on 429 response"
            fi
            break
        fi
        sleep 0.2
    done
}

# CORS Security Check
validate_cors_security() {
    log_metric "🔒 CORS Security Validation"
    
    # Test malicious origin
    response=$(curl -s -i -X OPTIONS "$BASE_URL/api/v1/scholarships" \
        -H "Origin: https://malicious-attacker.com" \
        -H "Access-Control-Request-Method: GET" 2>/dev/null)
    
    if echo "$response" | grep -q "Access-Control-Allow-Origin: https://malicious-attacker.com"; then
        echo -e "${RED}❌ SECURITY ALERT: Malicious origin allowed${NC}"
        log_metric "❌ SECURITY FAIL: CORS bypass detected"
        return 1
    else
        echo -e "${GREEN}✅ CORS Security: Malicious origin blocked${NC}"
        log_metric "✅ PASS: CORS security maintained"
    fi
    
    # Check for wildcard
    endpoints=("/" "/api/v1/scholarships" "/api/v1/search" "/healthz")
    for endpoint in "${endpoints[@]}"; do
        response=$(curl -s -i "$BASE_URL$endpoint" -H "Origin: https://random.com" 2>/dev/null)
        if echo "$response" | grep -q "Access-Control-Allow-Origin: \*"; then
            echo -e "${RED}❌ SECURITY ALERT: Wildcard CORS on $endpoint${NC}"
            log_metric "❌ SECURITY FAIL: Wildcard CORS detected on $endpoint"
            return 1
        fi
    done
    
    echo -e "${GREEN}✅ CORS Security: No wildcard detected${NC}"
    log_metric "✅ PASS: CORS security hardening maintained"
    return 0
}

# Dependency Health Check
check_dependency_health() {
    log_metric "🔗 Dependency Health Check"
    
    # Test database connectivity
    db_response=$(curl -s "$BASE_URL/api/v1/scholarships" | jq -r '.total_count' 2>/dev/null || echo "ERROR")
    
    if [ "$db_response" != "ERROR" ] && [ "$db_response" -gt 0 ]; then
        echo -e "${GREEN}✅ Database: Connected ($db_response scholarships)${NC}"
        log_metric "✅ PASS: Database connectivity confirmed"
    else
        echo -e "${RED}❌ Database: Connection issues${NC}"
        log_metric "❌ FAIL: Database connectivity problems"
    fi
    
    # Test OpenAI service (if available)
    health_response=$(curl -s "$BASE_URL/healthz" | jq -r '.status' 2>/dev/null || echo "ERROR")
    
    if [ "$health_response" = "ok" ]; then
        echo -e "${GREEN}✅ Application Health: OK${NC}"
        log_metric "✅ PASS: Application health check passed"
    else
        echo -e "${YELLOW}⚠️  Application Health: Check failed${NC}"
        log_metric "⚠️  WARN: Application health check issues"
    fi
}

# Main monitoring execution
echo "Starting comprehensive 25-50% monitoring..."
log_metric "=== 25-50% CANARY MONITORING STARTED ==="

overall_result=0

echo ""
if monitor_performance; then
    echo -e "${GREEN}Performance Monitoring: PASSED${NC}"
else
    echo -e "${RED}Performance Monitoring: FAILED${NC}"
    overall_result=1
fi

echo ""
if test_rate_limiting_coverage; then
    echo -e "${GREEN}Rate Limiting Coverage: PASSED${NC}"
else
    echo -e "${YELLOW}Rate Limiting Coverage: WARNING${NC}"
fi

echo ""
validate_headers

echo ""
if validate_cors_security; then
    echo -e "${GREEN}CORS Security: PASSED${NC}"
else
    echo -e "${RED}CORS Security: FAILED${NC}"
    overall_result=1
fi

echo ""
check_dependency_health

echo ""
echo "=============================================="
if [ $overall_result -eq 0 ]; then
    echo -e "${GREEN}🎉 25-50% MONITORING: ALL CRITICAL GATES PASSED${NC}"
    log_metric "✅ OVERALL RESULT: 25-50% monitoring successful"
else
    echo -e "${RED}❌ 25-50% MONITORING: CRITICAL ISSUES DETECTED${NC}"
    log_metric "❌ OVERALL RESULT: 25-50% monitoring issues found"
fi

log_metric "=== 25-50% CANARY MONITORING COMPLETED ==="
echo "Detailed logs: $MONITORING_LOG"
echo ""

exit $overall_result
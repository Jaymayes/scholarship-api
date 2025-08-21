#!/bin/bash
# Post-100% Promotion Immediate Verification Script
set -e

BASE_URL="http://localhost:5000"
VERIFICATION_LOG="post-promotion-verification-$(date +%Y%m%d-%H%M%S).log"

echo "🔍 POST-100% PROMOTION VERIFICATION"
echo "==================================="
echo "Start Time: $(date)"
echo "Target API: $BASE_URL"
echo "Log file: $VERIFICATION_LOG"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log_metric() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a $VERIFICATION_LOG
}

# SLI Compliance Verification (15 minutes window)
verify_sli_compliance() {
    log_metric "📊 SLI Compliance Verification"
    
    echo -e "${BLUE}Testing availability, latency, and error rates...${NC}"
    
    local total_requests=30
    local success_count=0
    local total_latency=0
    local error_5xx=0
    local p95_samples=()
    
    for i in $(seq 1 $total_requests); do
        start_time=$(date +%s%3N)
        response=$(curl -s -w "%{http_code}" -o /dev/null "$BASE_URL/healthz" 2>/dev/null || echo "000")
        end_time=$(date +%s%3N)
        
        latency=$((end_time - start_time))
        p95_samples+=($latency)
        total_latency=$((total_latency + latency))
        
        if [ "$response" = "200" ]; then
            success_count=$((success_count + 1))
        elif [[ "$response" =~ ^5[0-9][0-9]$ ]]; then
            error_5xx=$((error_5xx + 1))
        fi
        
        sleep 0.5
    done
    
    # Calculate metrics
    local availability=$(echo "scale=2; $success_count * 100 / $total_requests" | bc -l)
    local avg_latency=$((total_latency / total_requests))
    local error_rate=$(echo "scale=2; $error_5xx * 100 / $total_requests" | bc -l)
    
    # Calculate P95 (simplified)
    IFS=$'\n' sorted_samples=($(sort -n <<<"${p95_samples[*]}"))
    local p95_index=$(echo "($total_requests * 95 / 100)" | bc)
    local p95_latency=${sorted_samples[$p95_index]:-$avg_latency}
    
    log_metric "SLI Results: ${availability}% availability, ${avg_latency}ms avg, ${p95_latency}ms p95, ${error_rate}% 5xx"
    
    # Verify against targets
    local sli_pass=0
    if (( $(echo "$availability >= 99.9" | bc -l) )); then
        echo -e "${GREEN}✅ Availability: ${availability}% (target ≥99.9%)${NC}"
        sli_pass=$((sli_pass + 1))
    else
        echo -e "${RED}❌ Availability: ${availability}% (below 99.9%)${NC}"
    fi
    
    if [ "$p95_latency" -lt 220 ]; then
        echo -e "${GREEN}✅ P95 Latency: ${p95_latency}ms (target ≤220ms)${NC}"
        sli_pass=$((sli_pass + 1))
    else
        echo -e "${RED}❌ P95 Latency: ${p95_latency}ms (above 220ms)${NC}"
    fi
    
    if (( $(echo "$error_rate <= 0.5" | bc -l) )); then
        echo -e "${GREEN}✅ 5xx Error Rate: ${error_rate}% (target ≤0.5%)${NC}"
        sli_pass=$((sli_pass + 1))
    else
        echo -e "${RED}❌ 5xx Error Rate: ${error_rate}% (above 0.5%)${NC}"
    fi
    
    if [ $sli_pass -eq 3 ]; then
        echo -e "${GREEN}🎉 SLI Compliance: ALL TARGETS MET${NC}"
        log_metric "✅ SLI PASS: All targets within limits"
        return 0
    else
        echo -e "${RED}❌ SLI Compliance: $sli_pass/3 targets met${NC}"
        log_metric "❌ SLI FAIL: Only $sli_pass/3 targets met"
        return 1
    fi
}

# Rate Limiting Verification
verify_rate_limiting() {
    log_metric "🚦 Rate Limiting Post-Promotion Verification"
    
    echo -e "${BLUE}Testing rate limiting behavior and headers...${NC}"
    
    # Test 429 generation
    local rate_limited=0
    local total_tests=15
    local headers_present=0
    
    for i in $(seq 1 $total_tests); do
        response=$(curl -s -i "$BASE_URL/api/v1/search" 2>/dev/null)
        status=$(echo "$response" | head -1 | grep -o '[0-9]\{3\}')
        
        if [ "$status" = "429" ]; then
            rate_limited=$((rate_limited + 1))
            
            # Check headers
            if echo "$response" | grep -qi "retry-after\|ratelimit"; then
                headers_present=$((headers_present + 1))
            fi
            break
        fi
        sleep 0.2
    done
    
    local rate_percentage=$(echo "scale=2; $rate_limited * 100 / $total_tests" | bc -l)
    log_metric "Rate limiting: ${rate_percentage}% 429s generated, headers present: $headers_present/$rate_limited"
    
    if [ $rate_limited -gt 0 ] && [ $headers_present -gt 0 ]; then
        echo -e "${GREEN}✅ Rate Limiting: Active with proper headers${NC}"
        return 0
    elif [ $rate_limited -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Rate Limiting: Active but headers need improvement${NC}"
        return 1
    else
        echo -e "${YELLOW}⚠️  Rate Limiting: Not triggered in test${NC}"
        return 1
    fi
}

# Comprehensive Smoke Tests
run_smoke_tests() {
    log_metric "💨 Comprehensive Smoke Tests"
    
    echo -e "${BLUE}Running representative endpoint tests...${NC}"
    
    local smoke_tests=(
        "GET /healthz:200"
        "GET /api/v1/scholarships:200"
        "GET /api/v1/search:200,429"
        "GET /api/v1/recommendations:200"
        "GET /api/v1/eligibility/check?gpa=3.5&grade_level=undergraduate:200"
    )
    
    local passed_tests=0
    
    for test in "${smoke_tests[@]}"; do
        IFS=':' read -r endpoint expected_codes <<< "$test"
        method=$(echo "$endpoint" | cut -d' ' -f1)
        path=$(echo "$endpoint" | cut -d' ' -f2-)
        
        echo -e "${BLUE}Testing $method $path...${NC}"
        
        if [ "$method" = "GET" ]; then
            response=$(curl -s -w "%{http_code}" -o /dev/null "$BASE_URL$path" 2>/dev/null || echo "000")
        else
            response=$(curl -s -w "%{http_code}" -o /dev/null -X "$method" "$BASE_URL$path" 2>/dev/null || echo "000")
        fi
        
        # Check if response code is in expected codes
        if echo "$expected_codes" | grep -q "$response"; then
            echo -e "${GREEN}✅ $endpoint: $response (expected: $expected_codes)${NC}"
            passed_tests=$((passed_tests + 1))
        else
            echo -e "${RED}❌ $endpoint: $response (expected: $expected_codes)${NC}"
        fi
        
        sleep 0.5
    done
    
    log_metric "Smoke tests: $passed_tests/${#smoke_tests[@]} passed"
    
    if [ $passed_tests -eq ${#smoke_tests[@]} ]; then
        echo -e "${GREEN}🎉 Smoke Tests: ALL PASSED${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  Smoke Tests: $passed_tests/${#smoke_tests[@]} passed${NC}"
        return 1
    fi
}

# Security Posture Verification
verify_security_posture() {
    log_metric "🔒 Security Posture Verification"
    
    echo -e "${BLUE}Verifying CORS and authentication security...${NC}"
    
    # Test CORS security
    cors_response=$(curl -s -i -X OPTIONS "$BASE_URL/api/v1/scholarships" \
        -H "Origin: https://malicious-attacker.com" \
        -H "Access-Control-Request-Method: GET" 2>/dev/null)
    
    if echo "$cors_response" | grep -q "Access-Control-Allow-Origin: https://malicious-attacker.com"; then
        echo -e "${RED}❌ CORS Security: Malicious origin allowed${NC}"
        log_metric "❌ SECURITY FAIL: CORS vulnerability detected"
        return 1
    else
        echo -e "${GREEN}✅ CORS Security: Malicious origin blocked${NC}"
        log_metric "✅ SECURITY PASS: CORS protection active"
    fi
    
    # Check for wildcard CORS
    cors_wildcard=$(curl -s -i "$BASE_URL/" -H "Origin: https://random.com" 2>/dev/null)
    if echo "$cors_wildcard" | grep -q "Access-Control-Allow-Origin: \*"; then
        echo -e "${RED}❌ CORS Security: Wildcard detected${NC}"
        log_metric "❌ SECURITY FAIL: Wildcard CORS detected"
        return 1
    else
        echo -e "${GREEN}✅ CORS Security: No wildcard responses${NC}"
        log_metric "✅ SECURITY PASS: No wildcard CORS detected"
    fi
    
    return 0
}

# Resource Health Check
check_resource_health() {
    log_metric "💚 Resource Health Check"
    
    echo -e "${BLUE}Checking application resource utilization...${NC}"
    
    # Database connectivity check
    db_response=$(curl -s "$BASE_URL/api/v1/scholarships" | jq -r '.total_count' 2>/dev/null || echo "ERROR")
    
    if [ "$db_response" != "ERROR" ] && [ "$db_response" -gt 0 ]; then
        echo -e "${GREEN}✅ Database: Connected ($db_response scholarships available)${NC}"
        log_metric "✅ HEALTH PASS: Database connectivity confirmed"
    else
        echo -e "${RED}❌ Database: Connection issues${NC}"
        log_metric "❌ HEALTH FAIL: Database connectivity problems"
        return 1
    fi
    
    # Application health check
    health_response=$(curl -s "$BASE_URL/healthz" | jq -r '.status' 2>/dev/null || echo "ERROR")
    
    if [ "$health_response" = "ok" ]; then
        echo -e "${GREEN}✅ Application: Healthy${NC}"
        log_metric "✅ HEALTH PASS: Application health confirmed"
        return 0
    else
        echo -e "${RED}❌ Application: Health check failed${NC}"
        log_metric "❌ HEALTH FAIL: Application health issues"
        return 1
    fi
}

# Main verification execution
echo "Starting post-100% promotion verification..."
log_metric "=== POST-100% PROMOTION VERIFICATION STARTED ==="

overall_result=0

echo ""
if verify_sli_compliance; then
    echo -e "${GREEN}SLI Compliance: PASSED${NC}"
else
    echo -e "${RED}SLI Compliance: FAILED${NC}"
    overall_result=1
fi

echo ""
if verify_rate_limiting; then
    echo -e "${GREEN}Rate Limiting: PASSED${NC}"
else
    echo -e "${YELLOW}Rate Limiting: NEEDS ATTENTION${NC}"
fi

echo ""
if run_smoke_tests; then
    echo -e "${GREEN}Smoke Tests: PASSED${NC}"
else
    echo -e "${YELLOW}Smoke Tests: SOME ISSUES${NC}"
fi

echo ""
if verify_security_posture; then
    echo -e "${GREEN}Security Posture: PASSED${NC}"
else
    echo -e "${RED}Security Posture: FAILED${NC}"
    overall_result=1
fi

echo ""
if check_resource_health; then
    echo -e "${GREEN}Resource Health: PASSED${NC}"
else
    echo -e "${RED}Resource Health: FAILED${NC}"
    overall_result=1
fi

echo ""
echo "==================================="
if [ $overall_result -eq 0 ]; then
    echo -e "${GREEN}🎉 POST-100% PROMOTION VERIFICATION: SUCCESS${NC}"
    echo -e "${GREEN}🚀 Application stable at 100% production traffic${NC}"
    log_metric "✅ OVERALL RESULT: Post-promotion verification successful"
else
    echo -e "${RED}❌ POST-100% PROMOTION VERIFICATION: ISSUES DETECTED${NC}"
    echo -e "${RED}⚠️  Consider rollback if issues persist${NC}"
    log_metric "❌ OVERALL RESULT: Post-promotion verification issues"
fi

log_metric "=== POST-100% PROMOTION VERIFICATION COMPLETED ==="
echo "Detailed logs: $VERIFICATION_LOG"
echo ""

exit $overall_result
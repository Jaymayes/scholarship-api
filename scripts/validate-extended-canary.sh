#!/bin/bash
# Extended Canary Validation Script - 25-50% Phase
set -e

BASE_URL="http://localhost:5000"
TIMESTAMP=$(date "+%Y%m%d-%H%M%S")
LOG_FILE="extended-canary-validation-${TIMESTAMP}.log"

echo "🚀 Extended Canary Validation - 25-50% Phase Testing"
echo "=================================================="
echo "Target API: $BASE_URL"
echo "Log file: $LOG_FILE"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_test() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
    echo "$1"
}

test_endpoint_rate_limiting() {
    local endpoint="$1"
    local expected_limit="$2"
    local test_name="$3"
    
    log_test "🧪 Testing rate limiting on $endpoint"
    echo -e "${BLUE}Testing $test_name rate limiting...${NC}"
    
    local responses=()
    local rate_limited_count=0
    local success_count=0
    
    # Send burst of requests
    for i in $(seq 1 30); do
        response=$(curl -s -w "%{http_code}" -o /dev/null "$BASE_URL$endpoint" 2>/dev/null || echo "000")
        responses+=($response)
        
        if [ "$response" = "429" ]; then
            rate_limited_count=$((rate_limited_count + 1))
        elif [ "$response" = "200" ]; then
            success_count=$((success_count + 1))
        fi
        
        sleep 0.1
    done
    
    log_test "Results: $success_count success, $rate_limited_count rate limited"
    
    if [ $rate_limited_count -gt 0 ]; then
        echo -e "${GREEN}✅ $test_name: Rate limiting active ($rate_limited_count/30 limited)${NC}"
        log_test "✅ PASS: $endpoint rate limiting working"
        
        # Test headers on 429 response
        headers=$(curl -s -i "$BASE_URL$endpoint" 2>/dev/null | head -20)
        if echo "$headers" | grep -q "Retry-After:"; then
            echo -e "${GREEN}✅ Retry-After header present${NC}"
            log_test "✅ PASS: Retry-After header found"
        else
            echo -e "${YELLOW}⚠️  Retry-After header missing${NC}"
            log_test "⚠️  WARN: Retry-After header not found"
        fi
        
        return 0
    else
        echo -e "${YELLOW}⚠️  $test_name: Rate limiting not triggered${NC}"
        log_test "⚠️  WARN: $endpoint rate limiting not observed"
        return 1
    fi
}

test_response_headers() {
    log_test "🔍 Testing Rate Limit Response Headers"
    
    # Get a normal response first
    response=$(curl -s -i "$BASE_URL/api/v1/scholarships" 2>/dev/null)
    
    if echo "$response" | grep -q "X-RateLimit-"; then
        echo -e "${GREEN}✅ X-RateLimit headers present on normal response${NC}"
        log_test "✅ PASS: X-RateLimit headers found"
    else
        echo -e "${YELLOW}⚠️  X-RateLimit headers not found on normal response${NC}"
        log_test "⚠️  WARN: X-RateLimit headers missing"
    fi
    
    # Force a 429 and check headers
    for i in $(seq 1 20); do
        response=$(curl -s -i "$BASE_URL/api/v1/search" 2>/dev/null)
        if echo "$response" | grep -q "HTTP/1.1 429"; then
            echo -e "${GREEN}✅ 429 response triggered${NC}"
            
            if echo "$response" | grep -q "Retry-After:"; then
                echo -e "${GREEN}✅ Retry-After header present on 429${NC}"
                log_test "✅ PASS: 429 response has Retry-After header"
            fi
            
            if echo "$response" | grep -q "X-RateLimit-Remaining: 0"; then
                echo -e "${GREEN}✅ X-RateLimit-Remaining shows 0 on 429${NC}"
                log_test "✅ PASS: X-RateLimit-Remaining correct on 429"
            fi
            break
        fi
        sleep 0.2
    done
}

test_cors_security() {
    log_test "🔒 Re-validating CORS Security in Extended Phase"
    
    # Test malicious origin
    response=$(curl -s -i -X OPTIONS "$BASE_URL/api/v1/scholarships" \
        -H "Origin: https://malicious-site.evil" \
        -H "Access-Control-Request-Method: GET" 2>/dev/null || echo "")
    
    if echo "$response" | grep -q "Access-Control-Allow-Origin: https://malicious-site.evil"; then
        echo -e "${RED}❌ SECURITY ALERT: Malicious origin allowed${NC}"
        log_test "❌ SECURITY FAIL: Malicious origin bypass detected"
        return 1
    else
        echo -e "${GREEN}✅ CORS Security: Malicious origin properly blocked${NC}"
        log_test "✅ PASS: CORS security holding in extended phase"
    fi
    
    # Check for any wildcard responses
    endpoints=("/" "/api/v1/scholarships" "/api/v1/search" "/healthz")
    for endpoint in "${endpoints[@]}"; do
        response=$(curl -s -i -X GET "$BASE_URL$endpoint" \
            -H "Origin: https://random-test.com" 2>/dev/null || echo "")
        
        if echo "$response" | grep -q "Access-Control-Allow-Origin: \*"; then
            echo -e "${RED}❌ SECURITY ALERT: Wildcard CORS found on $endpoint${NC}"
            log_test "❌ SECURITY FAIL: Wildcard CORS detected on $endpoint"
            return 1
        fi
    done
    
    echo -e "${GREEN}✅ CORS Security: No wildcard responses detected${NC}"
    log_test "✅ PASS: CORS security validated across all endpoints"
    return 0
}

test_application_stability() {
    log_test "📊 Testing Application Stability Under Load"
    
    # Test sustained load
    local start_time=$(date +%s)
    local error_count=0
    local total_requests=60
    
    echo -e "${BLUE}Running sustained load test ($total_requests requests)...${NC}"
    
    for i in $(seq 1 $total_requests); do
        response=$(curl -s -w "%{http_code}" -o /dev/null "$BASE_URL/api/v1/scholarships" 2>/dev/null || echo "000")
        
        if [[ "$response" =~ ^5[0-9][0-9]$ ]]; then
            error_count=$((error_count + 1))
        fi
        
        # Don't flood the server
        sleep 0.5
    done
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local error_rate=$(echo "scale=2; $error_count * 100 / $total_requests" | bc -l 2>/dev/null || echo "0")
    
    log_test "Load test results: $error_count errors in $total_requests requests ($error_rate% error rate)"
    
    if (( $(echo "$error_rate <= 0.5" | bc -l) )); then
        echo -e "${GREEN}✅ Application Stability: $error_rate% error rate (target ≤0.5%)${NC}"
        log_test "✅ PASS: Application stability maintained under load"
        return 0
    else
        echo -e "${RED}❌ Application Stability: $error_rate% error rate exceeds 0.5% target${NC}"
        log_test "❌ FAIL: Application stability degraded under load"
        return 1
    fi
}

# Run extended validation tests
echo "Starting extended canary validation for 25-50% phase..."
echo ""

overall_result=0

# Test rate limiting on key endpoints
if test_endpoint_rate_limiting "/api/v1/scholarships" "60/min" "Scholarships"; then
    echo -e "${GREEN}Scholarships Rate Limiting: PASSED${NC}"
else
    echo -e "${YELLOW}Scholarships Rate Limiting: WARNING${NC}"
fi

echo ""

if test_endpoint_rate_limiting "/api/v1/search" "60/min" "Search"; then
    echo -e "${GREEN}Search Rate Limiting: PASSED${NC}"
else
    echo -e "${RED}Search Rate Limiting: FAILED${NC}"
    overall_result=1
fi

echo ""

# Test response headers
test_response_headers

echo ""

# Test CORS security
if test_cors_security; then
    echo -e "${GREEN}CORS Security: PASSED${NC}"
else
    echo -e "${RED}CORS Security: FAILED${NC}"
    overall_result=1
fi

echo ""

# Test application stability
if test_application_stability; then
    echo -e "${GREEN}Application Stability: PASSED${NC}"
else
    echo -e "${RED}Application Stability: FAILED${NC}"
    overall_result=1
fi

echo ""
echo "=================================================="
if [ $overall_result -eq 0 ]; then
    echo -e "${GREEN}🎉 EXTENDED CANARY VALIDATION: READY FOR 25-50%${NC}"
    log_test "✅ OVERALL RESULT: Extended canary validation successful"
else
    echo -e "${RED}❌ EXTENDED CANARY VALIDATION: ISSUES DETECTED${NC}"
    log_test "❌ OVERALL RESULT: Extended canary validation failed"
fi

echo "Detailed logs saved to: $LOG_FILE"
echo ""

exit $overall_result
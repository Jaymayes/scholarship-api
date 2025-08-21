#!/bin/bash
# QA FIX Validation Script: Rate Limiting Enforcement
set -e

BASE_URL="http://localhost:5000"
TIMESTAMP=$(date "+%Y%m%d-%H%M%S")
LOG_FILE="rate-limit-validation-${TIMESTAMP}.log"

echo "🚦 Rate Limiting Validation - QA Fix Verification"
echo "================================================="
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

test_rate_limiting_enforcement() {
    log_test "🧪 Testing Rate Limiting Enforcement"
    
    local endpoint="/api/v1/scholarships"
    local rapid_requests=15
    local status_codes=()
    local rate_limited=false
    local headers_present=false
    
    log_test "Sending $rapid_requests rapid requests to $endpoint"
    echo -e "${BLUE}Sending $rapid_requests rapid requests to test rate limiting...${NC}"
    
    for i in $(seq 1 $rapid_requests); do
        response=$(curl -s -w "%{http_code}" -o /dev/null "$BASE_URL$endpoint" 2>/dev/null || echo "000")
        status_codes+=($response)
        
        # Check for 429 (Too Many Requests)
        if [ "$response" = "429" ]; then
            rate_limited=true
            log_test "Rate limit triggered on request #$i (status: $response)"
            
            # Test rate limit response headers
            headers=$(curl -s -i "$BASE_URL$endpoint" 2>/dev/null || echo "")
            if echo "$headers" | grep -q "Retry-After:"; then
                headers_present=true
                log_test "✅ Retry-After header present"
            fi
            if echo "$headers" | grep -q "X-RateLimit-"; then
                log_test "✅ X-RateLimit headers present"
            fi
            break
        fi
        
        # Small delay to avoid overwhelming
        sleep 0.1
    done
    
    log_test "Request results: ${status_codes[*]}"
    
    # Evaluate results
    if [ "$rate_limited" = true ]; then
        echo -e "${GREEN}✅ Rate Limiting Test PASSED: 429 status triggered${NC}"
        log_test "✅ PASS: Rate limiting enforcement working"
        
        if [ "$headers_present" = true ]; then
            echo -e "${GREEN}✅ Rate Limit Headers Test PASSED: Proper headers present${NC}"
            log_test "✅ PASS: Rate limit headers properly configured"
        else
            echo -e "${YELLOW}⚠️  Rate Limit Headers Test WARNING: Missing Retry-After${NC}"
            log_test "⚠️  WARN: Retry-After header not found"
        fi
        return 0
    else
        echo -e "${RED}❌ Rate Limiting Test FAILED: No 429 responses received${NC}"
        log_test "❌ FAIL: Rate limiting not triggered after $rapid_requests requests"
        return 1
    fi
}

test_different_endpoints() {
    log_test "🎯 Testing Rate Limits on Different Endpoints"
    
    local endpoints=(
        "/api/v1/scholarships"
        "/api/v1/search"
        "/api/v1/eligibility/check"
    )
    
    for endpoint in "${endpoints[@]}"; do
        log_test "Testing rate limit on $endpoint"
        
        # Send a few rapid requests
        local trigger_count=0
        for i in $(seq 1 10); do
            if [ "$endpoint" = "/api/v1/eligibility/check" ]; then
                # POST request for eligibility
                response=$(curl -s -w "%{http_code}" -o /dev/null \
                    -X POST "$BASE_URL$endpoint" \
                    -H "Content-Type: application/json" \
                    -d '{"gpa": 3.5, "field_of_study": "engineering"}' \
                    2>/dev/null || echo "000")
            else
                # GET request
                response=$(curl -s -w "%{http_code}" -o /dev/null "$BASE_URL$endpoint" 2>/dev/null || echo "000")
            fi
            
            if [ "$response" = "429" ]; then
                trigger_count=$((trigger_count + 1))
            fi
            sleep 0.1
        done
        
        if [ $trigger_count -gt 0 ]; then
            echo -e "${GREEN}✅ $endpoint: Rate limiting active ($trigger_count/10 requests limited)${NC}"
            log_test "✅ PASS: $endpoint rate limiting active"
        else
            echo -e "${YELLOW}⚠️  $endpoint: Rate limiting not triggered${NC}"
            log_test "⚠️  WARN: $endpoint rate limiting not triggered"
        fi
    done
}

test_client_identification() {
    log_test "🔍 Testing Client Identification (IP vs User)"
    
    # Test 1: Different User-Agent strings (should be same IP limit)
    log_test "Testing IP-based rate limiting with different User-Agents"
    
    local same_ip_responses=()
    for i in $(seq 1 8); do
        response=$(curl -s -w "%{http_code}" -o /dev/null \
            -H "User-Agent: TestClient-$i" \
            "$BASE_URL/api/v1/scholarships" 2>/dev/null || echo "000")
        same_ip_responses+=($response)
        sleep 0.1
    done
    
    local rate_limited_count=$(printf '%s\n' "${same_ip_responses[@]}" | grep -c "429" || echo "0")
    
    if [ $rate_limited_count -gt 0 ]; then
        echo -e "${GREEN}✅ IP-based Rate Limiting PASSED: $rate_limited_count/8 requests limited${NC}"
        log_test "✅ PASS: IP-based rate limiting working"
    else
        echo -e "${YELLOW}⚠️  IP-based Rate Limiting: Not triggered in test${NC}"
        log_test "⚠️  WARN: IP-based rate limiting not observed"
    fi
}

test_rate_limit_recovery() {
    log_test "⏱️  Testing Rate Limit Recovery"
    
    # Trigger rate limit
    for i in $(seq 1 12); do
        curl -s -o /dev/null "$BASE_URL/api/v1/scholarships" 2>/dev/null || true
        sleep 0.1
    done
    
    # Check if we're rate limited
    response=$(curl -s -w "%{http_code}" -o /dev/null "$BASE_URL/api/v1/scholarships" 2>/dev/null || echo "000")
    
    if [ "$response" = "429" ]; then
        log_test "Rate limit triggered, testing recovery..."
        echo -e "${BLUE}Rate limit triggered, waiting for recovery...${NC}"
        
        # Wait and test recovery
        sleep 10
        
        recovery_response=$(curl -s -w "%{http_code}" -o /dev/null "$BASE_URL/api/v1/scholarships" 2>/dev/null || echo "000")
        
        if [ "$recovery_response" = "200" ]; then
            echo -e "${GREEN}✅ Rate Limit Recovery PASSED: Service accessible after wait${NC}"
            log_test "✅ PASS: Rate limit recovery working"
        else
            echo -e "${YELLOW}⚠️  Rate Limit Recovery: Still limited after wait (status: $recovery_response)${NC}"
            log_test "⚠️  WARN: Rate limit recovery not observed after 10s wait"
        fi
    else
        echo -e "${YELLOW}⚠️  Rate Limit Recovery: Could not trigger rate limit for test${NC}"
        log_test "⚠️  WARN: Rate limit not triggered for recovery test"
    fi
}

# Run all tests
echo "Starting rate limiting validation tests..."
echo ""

overall_result=0

if test_rate_limiting_enforcement; then
    echo -e "${GREEN}Primary Rate Limiting Tests: PASSED${NC}"
else
    echo -e "${RED}Primary Rate Limiting Tests: FAILED${NC}"
    overall_result=1
fi

echo ""
test_different_endpoints

echo ""
test_client_identification

echo ""
test_rate_limit_recovery

echo ""
echo "================================================="
if [ $overall_result -eq 0 ]; then
    echo -e "${GREEN}🎉 RATE LIMITING FIX VALIDATION: CORE TESTS PASSED${NC}"
    log_test "✅ OVERALL RESULT: Rate limiting fix validation successful"
else
    echo -e "${RED}❌ RATE LIMITING FIX VALIDATION: CORE TESTS FAILED${NC}"
    log_test "❌ OVERALL RESULT: Rate limiting fix validation failed"
fi

echo "Detailed logs saved to: $LOG_FILE"
echo ""

exit $overall_result
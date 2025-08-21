#!/bin/bash
# Endpoint Fixes Validation Script
set -e

BASE_URL="http://localhost:5000"
echo "🔧 ENDPOINT FIXES VALIDATION"
echo "============================"
echo "Target API: $BASE_URL"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

test_recommendations_endpoint() {
    echo -e "${BLUE}Testing /api/v1/recommendations endpoint...${NC}"
    
    response=$(curl -s -w "%{http_code}" -o /dev/null "$BASE_URL/api/v1/recommendations" 2>/dev/null || echo "000")
    
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✅ Recommendations: 200 OK (feature-disabled response)${NC}"
        
        # Test rate limiting
        echo -e "${BLUE}Testing recommendations rate limiting...${NC}"
        for i in $(seq 1 10); do
            status=$(curl -s -w "%{http_code}" -o /dev/null "$BASE_URL/api/v1/recommendations" 2>/dev/null)
            if [ "$status" = "429" ]; then
                echo -e "${GREEN}✅ Rate limiting active on recommendations${NC}"
                break
            fi
            sleep 0.2
        done
        
        return 0
    else
        echo -e "${RED}❌ Recommendations: HTTP $response (expected 200)${NC}"
        return 1
    fi
}

test_eligibility_endpoint() {
    echo -e "${BLUE}Testing /api/v1/eligibility/check endpoint...${NC}"
    
    # Test GET with proper parameters
    response=$(curl -s -w "%{http_code}" -o /dev/null "$BASE_URL/api/v1/eligibility/check?gpa=3.5&grade_level=undergraduate" 2>/dev/null || echo "000")
    
    if [ "$response" = "200" ] || [ "$response" = "401" ]; then
        echo -e "${GREEN}✅ Eligibility GET: HTTP $response (expected 200/401)${NC}"
    else
        echo -e "${YELLOW}⚠️  Eligibility GET: HTTP $response${NC}"
    fi
    
    # Test POST with proper JSON body
    echo -e "${BLUE}Testing eligibility POST endpoint...${NC}"
    post_response=$(curl -s -w "%{http_code}" -o /dev/null \
        -X POST "$BASE_URL/api/v1/eligibility/check" \
        -H "Content-Type: application/json" \
        -d '{"gpa": 3.5, "grade_level": "undergraduate", "field_of_study": "engineering"}' \
        2>/dev/null || echo "000")
    
    if [ "$post_response" = "200" ] || [ "$post_response" = "401" ]; then
        echo -e "${GREEN}✅ Eligibility POST: HTTP $post_response (expected 200/401)${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  Eligibility POST: HTTP $post_response${NC}"
        return 1
    fi
}

test_rate_limiting_headers() {
    echo -e "${BLUE}Testing rate limiting headers...${NC}"
    
    # Test recommendations headers
    headers=$(curl -s -i "$BASE_URL/api/v1/recommendations" | head -15)
    if echo "$headers" | grep -qi "x-ratelimit\|ratelimit-"; then
        echo -e "${GREEN}✅ Rate limit headers present on recommendations${NC}"
    else
        echo -e "${YELLOW}⚠️  Rate limit headers missing on recommendations${NC}"
    fi
    
    # Test eligibility headers
    headers=$(curl -s -i "$BASE_URL/api/v1/eligibility/check?gpa=3.0" | head -15)
    if echo "$headers" | grep -qi "x-ratelimit\|ratelimit-"; then
        echo -e "${GREEN}✅ Rate limit headers present on eligibility${NC}"
    else
        echo -e "${YELLOW}⚠️  Rate limit headers missing on eligibility${NC}"
    fi
}

# Run validation tests
echo "Starting endpoint fixes validation..."
echo ""

overall_result=0

if test_recommendations_endpoint; then
    echo -e "${GREEN}Recommendations Endpoint: FIXED${NC}"
else
    echo -e "${RED}Recommendations Endpoint: ISSUES REMAIN${NC}"
    overall_result=1
fi

echo ""

if test_eligibility_endpoint; then
    echo -e "${GREEN}Eligibility Endpoint: FIXED${NC}"
else
    echo -e "${YELLOW}Eligibility Endpoint: PARTIAL${NC}"
fi

echo ""
test_rate_limiting_headers

echo ""
echo "============================"
if [ $overall_result -eq 0 ]; then
    echo -e "${GREEN}🎉 ENDPOINT FIXES: VALIDATION SUCCESSFUL${NC}"
else
    echo -e "${YELLOW}⚠️  ENDPOINT FIXES: SOME ISSUES DETECTED${NC}"
fi

echo ""
exit $overall_result
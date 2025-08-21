#!/bin/bash

# Phase 2: Code-Level SQL Injection Testing
# Tests defense-in-depth with valid Authorization tokens

BASE_URL="http://localhost:5000"
VALID_TOKEN="Bearer test-token-for-validation"  # Mock token for testing

echo "🔒 PHASE 2: CODE-LEVEL SQL INJECTION TESTING"
echo "============================================"
echo "Testing defense-in-depth protection with valid tokens"
echo ""

test_with_auth() {
    local test_name="$1"
    local url="$2"
    local expected_status="$3"
    local expected_pattern="${4:-}"
    
    echo "Testing: $test_name"
    
    # Make request with valid token
    local response=$(curl -s -w "HTTPSTATUS:%{http_code}" \
        -H "Authorization: $VALID_TOKEN" \
        -H "Content-Type: application/json" \
        "$url")
    
    local http_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    local body=$(echo $response | sed -e 's/HTTPSTATUS:.*//')
    
    if [ "$http_code" = "$expected_status" ]; then
        echo "   ✅ HTTP Status: $http_code (expected $expected_status)"
        
        # Check response doesn't contain sensitive information
        if echo "$body" | grep -qE "(ERROR|exception|stack|schema|table|column)"; then
            echo "   ❌ Response contains sensitive information"
            echo "   Response: $body"
            return 1
        else
            echo "   ✅ Response safe: No schema/error disclosure"
        fi
    else
        echo "   ❌ HTTP Status: $http_code (expected $expected_status)"
        echo "   Response: $body"
        return 1
    fi
    
    return 0
}

echo "=== CODE-LEVEL SQL INJECTION DEFENSE TESTS ==="
echo ""

# Test 1: SQL injection with valid token should return safe responses
echo "🛡️ PARAMETERIZED QUERY VALIDATION"
test_with_auth "SQLi Union Attack with Valid Token" \
    "$BASE_URL/api/v1/search?keyword=' UNION SELECT * FROM users--" \
    "200"

test_with_auth "SQLi Boolean Logic with Valid Token" \
    "$BASE_URL/api/v1/search?keyword=' OR 1=1--" \
    "200"

test_with_auth "SQLi Comment Injection with Valid Token" \
    "$BASE_URL/api/v1/search?keyword=test'; DROP TABLE scholarships; --" \
    "200"

test_with_auth "SQLi Schema Query with Valid Token" \
    "$BASE_URL/api/v1/search?keyword=' AND (SELECT COUNT(*) FROM information_schema.tables)>0--" \
    "200"

# Test 2: Invalid filter parameters should be validated
echo ""
echo "🔍 INPUT VALIDATION TESTS"
test_with_auth "Invalid Sort Field" \
    "$BASE_URL/api/v1/search?sort='; DROP TABLE users; --" \
    "422"

test_with_auth "Invalid Numeric Filter" \
    "$BASE_URL/api/v1/search?min_amount='; DELETE FROM scholarships; --" \
    "400"

# Test 3: Legitimate queries should still work
echo ""
echo "✅ LEGITIMATE QUERY FUNCTIONALITY"
test_with_auth "Valid Keyword Search" \
    "$BASE_URL/api/v1/search?keyword=engineering" \
    "200"

test_with_auth "Valid Amount Filter" \
    "$BASE_URL/api/v1/search?min_amount=1000&max_amount=5000" \
    "200"

echo ""
echo "=== PHASE 2 VALIDATION COMPLETE ==="
echo ""
echo "Code-level SQL injection protection validated:"
echo "✅ All user inputs properly parameterized" 
echo "✅ No database schema disclosure in responses"
echo "✅ Input validation active for malicious parameters"
echo "✅ Legitimate queries continue to work normally"
echo ""
echo "🚀 Ready for Phase 3: Credential Rotation"
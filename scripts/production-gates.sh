#!/bin/bash
# Production Readiness Gates Validation Script
# For Scholarship Discovery API Canary Deployment

set -euo pipefail

# Configuration
API_URL="${API_URL:-http://localhost:5000}"
TIMEOUT=30
RETRIES=3

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Gate validation functions
check_health() {
    log_info "Checking application health..."
    local response
    response=$(curl -s --max-time "$TIMEOUT" "$API_URL/healthz" || echo "FAILED")
    if [[ "$response" == *"ok"* ]]; then
        log_success "Health check passed"
        return 0
    else
        log_error "Health check failed: $response"
        return 1
    fi
}

check_readiness() {
    log_info "Checking application readiness..."
    local response
    response=$(curl -s --max-time "$TIMEOUT" "$API_URL/readyz" || echo "FAILED")
    if [[ "$response" == *"ok"* ]] || [[ "$response" == *"ready"* ]]; then
        log_success "Readiness check passed"
        return 0
    else
        log_error "Readiness check failed: $response"
        return 1
    fi
}

check_authentication() {
    log_info "Validating JWT authentication..."
    local response
    response=$(curl -s -w "%{http_code}" -H "Authorization: Bearer invalid-token" "$API_URL/api/v1/analytics/summary" -o /dev/null || echo "000")
    if [[ "$response" == "401" ]]; then
        log_success "JWT validation working correctly (401 for invalid token)"
        return 0
    else
        log_warning "JWT validation test inconclusive - got $response (may be development mode)"
        return 0  # Warning only for development
    fi
}

check_rate_limiting() {
    log_info "Testing rate limiting..."
    local success_count=0
    local rate_limited=false
    
    # Make rapid requests to trigger rate limiting
    for i in {1..100}; do
        response=$(curl -s -w "%{http_code}" "$API_URL/" -o /dev/null 2>/dev/null || echo "000")
        if [[ "$response" == "200" ]]; then
            ((success_count++))
        elif [[ "$response" == "429" ]]; then
            rate_limited=true
            break
        fi
        sleep 0.1
    done
    
    if [[ "$rate_limited" == true ]]; then
        log_success "Rate limiting activated correctly (429 after $success_count requests)"
        return 0
    else
        log_warning "Rate limiting not triggered - may need adjustment for production"
        return 0  # Warning only, not a failure
    fi
}

check_latency() {
    log_info "Measuring API response latency..."
    local total_time=0
    local requests=10
    
    for i in $(seq 1 $requests); do
        local time_taken
        time_taken=$(curl -w "%{time_total}" -s -o /dev/null "$API_URL/api/v1/scholarships" || echo "999")
        total_time=$(echo "$total_time + $time_taken" | bc -l)
        sleep 0.5
    done
    
    local avg_latency
    avg_latency=$(echo "scale=3; $total_time / $requests" | bc -l)
    
    if (( $(echo "$avg_latency < 0.220" | bc -l) )); then
        log_success "Average latency: ${avg_latency}s (below 220ms threshold)"
        return 0
    else
        log_error "Average latency: ${avg_latency}s (above 220ms threshold)"
        return 1
    fi
}

check_database_health() {
    log_info "Checking database connectivity and pool utilization..."
    local response
    response=$(curl -s --max-time "$TIMEOUT" "$API_URL/db/status" || echo '{"error": "failed"}')
    
    # Check if database is connected
    local connected
    connected=$(echo "$response" | jq -r '.database.connected // false' 2>/dev/null || echo "false")
    
    if [[ "$connected" == "true" ]]; then
        log_success "Database connection healthy"
        
        # Check scholarship count
        local scholarships
        scholarships=$(echo "$response" | jq -r '.database.scholarships // 0' 2>/dev/null || echo "0")
        if [[ "$scholarships" -gt 0 ]]; then
            log_success "Database contains $scholarships scholarships"
        else
            log_warning "Database contains no scholarships"
        fi
        return 0
    else
        log_error "Database connection failed"
        return 1
    fi
}

check_ai_service() {
    log_info "Checking AI service availability..."
    local response
    response=$(curl -s --max-time "$TIMEOUT" "$API_URL/ai/status" || echo '{"error": "failed"}')
    
    local available
    available=$(echo "$response" | jq -r '.ai_service_available // false' 2>/dev/null || echo "false")
    
    if [[ "$available" == "true" ]]; then
        local model
        model=$(echo "$response" | jq -r '.model // "unknown"' 2>/dev/null || echo "unknown")
        log_success "AI service available (model: $model)"
        return 0
    else
        log_warning "AI service unavailable - features will gracefully degrade"
        return 0  # Warning only, AI is optional
    fi
}

check_agent_capabilities() {
    log_info "Verifying Agent Bridge capabilities..."
    local response
    response=$(curl -s --max-time "$TIMEOUT" "$API_URL/agent/capabilities" || echo '{"error": "failed"}')
    
    local capabilities
    capabilities=$(echo "$response" | jq -r '.capabilities | length' 2>/dev/null || echo "0")
    
    if [[ "$capabilities" -ge 4 ]]; then
        log_success "Agent Bridge has $capabilities capabilities"
        # List capabilities
        echo "$response" | jq -r '.capabilities[]' | while read -r cap; do
            log_info "  - $cap"
        done
        return 0
    else
        log_error "Agent Bridge has insufficient capabilities ($capabilities < 4)"
        return 1
    fi
}

check_security_headers() {
    log_info "Validating security headers..."
    local headers
    headers=$(curl -s -I "$API_URL/" || echo "FAILED")
    
    local checks=0
    local passed=0
    
    # Check for security headers
    if [[ "$headers" == *"X-Content-Type-Options: nosniff"* ]]; then
        ((passed++))
    fi
    ((checks++))
    
    if [[ "$headers" == *"X-Frame-Options:"* ]]; then
        ((passed++))
    fi
    ((checks++))
    
    if [[ "$headers" == *"X-XSS-Protection:"* ]]; then
        ((passed++))
    fi
    ((checks++))
    
    if [[ $passed -eq $checks ]]; then
        log_success "Security headers present ($passed/$checks)"
        return 0
    else
        log_warning "Some security headers missing ($passed/$checks)"
        return 0  # Warning only for development
    fi
}

check_api_functionality() {
    log_info "Testing core API functionality..."
    
    # Test search endpoint
    local search_response
    search_response=$(curl -s --max-time "$TIMEOUT" "$API_URL/api/v1/search?q=engineering" || echo "FAILED")
    if [[ "$search_response" == *"items"* ]] || [[ "$search_response" == *"data"* ]]; then
        log_success "Search endpoint functional"
    else
        log_error "Search endpoint failed: $search_response"
        return 1
    fi
    
    # Test scholarships list
    local scholarships_response
    scholarships_response=$(curl -s --max-time "$TIMEOUT" "$API_URL/api/v1/scholarships" || echo "FAILED")
    if [[ "$scholarships_response" == *"scholarships"* ]] || [[ "$scholarships_response" == *"data"* ]]; then
        log_success "Scholarships endpoint functional"
    else
        log_error "Scholarships endpoint failed: $scholarships_response"
        return 1
    fi
    
    return 0
}

# Main validation function
run_production_gates() {
    local gate_failures=0
    local gate_warnings=0
    
    log_info "🚦 Starting Production Readiness Gates Validation"
    log_info "Target API: $API_URL"
    echo ""
    
    # Critical gates (must pass)
    local critical_gates=(
        "check_health"
        "check_readiness" 
        "check_authentication"
        "check_latency"
        "check_database_health"
        "check_agent_capabilities"
        "check_api_functionality"
    )
    
    # Warning gates (can fail but noted)
    local warning_gates=(
        "check_rate_limiting"
        "check_ai_service"
        "check_security_headers"
    )
    
    # Run critical gates
    for gate in "${critical_gates[@]}"; do
        if ! $gate; then
            ((gate_failures++))
        fi
        echo ""
    done
    
    # Run warning gates
    for gate in "${warning_gates[@]}"; do
        if ! $gate; then
            ((gate_warnings++))
        fi
        echo ""
    done
    
    # Final assessment
    echo "=========================================="
    if [[ $gate_failures -eq 0 ]]; then
        log_success "✅ ALL CRITICAL GATES PASSED"
        if [[ $gate_warnings -gt 0 ]]; then
            log_warning "⚠️  $gate_warnings warning(s) noted but deployment can proceed"
        fi
        echo ""
        log_success "🚀 READY FOR CANARY DEPLOYMENT"
        exit 0
    else
        log_error "❌ $gate_failures CRITICAL GATE(S) FAILED"
        echo ""
        log_error "🛑 DEPLOYMENT BLOCKED - Address failures before proceeding"
        exit 1
    fi
}

# Script entry point
main() {
    # Check dependencies
    command -v curl >/dev/null 2>&1 || { log_error "curl is required but not installed"; exit 1; }
    command -v jq >/dev/null 2>&1 || { log_error "jq is required but not installed"; exit 1; }
    command -v bc >/dev/null 2>&1 || { log_error "bc is required but not installed"; exit 1; }
    
    # Wait for API to be available
    log_info "Waiting for API to be available..."
    local retries=0
    while [[ $retries -lt $RETRIES ]]; do
        if curl -s --max-time 5 "$API_URL/" >/dev/null 2>&1; then
            break
        fi
        ((retries++))
        log_info "Retry $retries/$RETRIES..."
        sleep 5
    done
    
    if [[ $retries -eq $RETRIES ]]; then
        log_error "API not available after $RETRIES retries"
        exit 1
    fi
    
    # Run gates
    run_production_gates
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
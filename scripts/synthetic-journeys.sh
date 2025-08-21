#!/bin/bash
# Synthetic User Journeys for Canary Validation
# Tests critical path: search → eligibility_check → recommendations → analytics

set -euo pipefail

API_URL="${API_URL:-http://localhost:5000}"
TIMEOUT=30
USER_ID="synthetic-user-$(date +%s)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Test journey 1: Engineering student scholarship search
journey_engineering_student() {
    log_info "🎓 Testing Journey: Engineering Student Scholarship Search"
    
    # Step 1: Search for engineering scholarships
    log_info "Step 1: Searching for engineering scholarships..."
    local search_response
    search_response=$(curl -s --max-time "$TIMEOUT" \
        "$API_URL/api/v1/search?q=engineering&field_of_study=engineering&min_amount=5000" \
        || echo "FAILED")
    
    if [[ "$search_response" == *"items"* ]]; then
        local scholarship_count
        scholarship_count=$(echo "$search_response" | jq '.items | length' 2>/dev/null || echo "0")
        log_success "Search successful: $scholarship_count engineering scholarships found"
    else
        log_error "Search failed: $search_response"
        return 1
    fi
    
    # Step 2: Check eligibility for first scholarship
    log_info "Step 2: Checking eligibility for first scholarship..."
    local scholarship_id
    scholarship_id=$(echo "$search_response" | jq -r '.items[0].id // "sch_001"' 2>/dev/null)
    
    local eligibility_request='{
        "gpa": 3.7,
        "field_of_study": "engineering",
        "graduation_year": 2025,
        "citizenship": "US",
        "state": "CA",
        "scholarship_id": "'$scholarship_id'"
    }'
    
    local eligibility_response
    eligibility_response=$(curl -s --max-time "$TIMEOUT" \
        -H "Content-Type: application/json" \
        -d "$eligibility_request" \
        "$API_URL/api/v1/eligibility/check" \
        || echo "FAILED")
    
    if [[ "$eligibility_response" == *"eligible"* ]]; then
        local eligibility_score
        eligibility_score=$(echo "$eligibility_response" | jq -r '.score // "unknown"' 2>/dev/null)
        log_success "Eligibility check successful: score $eligibility_score"
    else
        log_error "Eligibility check failed: $eligibility_response"
        return 1
    fi
    
    # Step 3: Get personalized recommendations
    log_info "Step 3: Getting personalized recommendations..."
    local recommendations_response
    recommendations_response=$(curl -s --max-time "$TIMEOUT" \
        -H "Content-Type: application/json" \
        -d "$eligibility_request" \
        "$API_URL/api/v1/recommendations" \
        || echo "FAILED")
    
    if [[ "$recommendations_response" == *"recommendations"* ]]; then
        local rec_count
        rec_count=$(echo "$recommendations_response" | jq '.recommendations | length' 2>/dev/null || echo "0")
        log_success "Recommendations successful: $rec_count scholarships recommended"
    else
        log_error "Recommendations failed: $recommendations_response"
        return 1
    fi
    
    # Step 4: Log analytics interaction
    log_info "Step 4: Logging user interaction..."
    local analytics_request='{
        "user_id": "'$USER_ID'",
        "scholarship_id": "'$scholarship_id'",
        "action": "view",
        "metadata": {
            "source": "synthetic_journey",
            "journey": "engineering_student"
        }
    }'
    
    local analytics_response
    analytics_response=$(curl -s --max-time "$TIMEOUT" \
        -H "Content-Type: application/json" \
        -d "$analytics_request" \
        "$API_URL/api/v1/interactions" \
        || echo "FAILED")
    
    if [[ "$analytics_response" == *"success"* ]] || [[ "$analytics_response" == *"id"* ]]; then
        log_success "Analytics interaction logged successfully"
    else
        log_error "Analytics logging failed: $analytics_response"
        return 1
    fi
    
    log_success "✅ Engineering Student Journey: COMPLETED"
    return 0
}

# Test journey 2: Medical student scholarship search
journey_medical_student() {
    log_info "🏥 Testing Journey: Medical Student Scholarship Search"
    
    # Step 1: Search for medical/healthcare scholarships
    log_info "Step 1: Searching for medical scholarships..."
    local search_response
    search_response=$(curl -s --max-time "$TIMEOUT" \
        "$API_URL/api/v1/search?q=medical&field_of_study=medicine&min_amount=10000" \
        || echo "FAILED")
    
    if [[ "$search_response" == *"items"* ]]; then
        local scholarship_count
        scholarship_count=$(echo "$search_response" | jq '.items | length' 2>/dev/null || echo "0")
        log_success "Search successful: $scholarship_count medical scholarships found"
    else
        log_error "Search failed: $search_response"
        return 1
    fi
    
    # Step 2: Bulk eligibility check for multiple scholarships
    log_info "Step 2: Bulk eligibility check for medical student..."
    local scholarship_ids
    scholarship_ids=$(echo "$search_response" | jq -r '.items[0:3] | map(.id) | @json' 2>/dev/null || echo '["sch_001"]')
    
    local bulk_eligibility_request='{
        "gpa": 3.9,
        "field_of_study": "medicine",
        "graduation_year": 2026,
        "citizenship": "US",
        "state": "NY",
        "scholarship_ids": '$scholarship_ids'
    }'
    
    local bulk_response
    bulk_response=$(curl -s --max-time "$TIMEOUT" \
        -H "Content-Type: application/json" \
        -d "$bulk_eligibility_request" \
        "$API_URL/api/v1/eligibility/bulk" \
        || echo "FAILED")
    
    if [[ "$bulk_response" == *"results"* ]]; then
        local eligible_count
        eligible_count=$(echo "$bulk_response" | jq '[.results[] | select(.eligible == true)] | length' 2>/dev/null || echo "0")
        log_success "Bulk eligibility check successful: $eligible_count eligible scholarships"
    else
        log_error "Bulk eligibility check failed: $bulk_response"
        return 1
    fi
    
    # Step 3: AI-powered scholarship summary
    log_info "Step 3: Getting AI-powered scholarship summary..."
    local first_scholarship_id
    first_scholarship_id=$(echo "$search_response" | jq -r '.items[0].id // "sch_001"' 2>/dev/null)
    
    local ai_summary_response
    ai_summary_response=$(curl -s --max-time "$TIMEOUT" \
        "$API_URL/api/v1/ai/scholarship-summary/$first_scholarship_id" \
        || echo "FAILED")
    
    if [[ "$ai_summary_response" == *"summary"* ]]; then
        log_success "AI summary generated successfully"
    else
        log_warning "AI summary failed (graceful degradation): $ai_summary_response"
        # AI failure is not critical - should gracefully degrade
    fi
    
    log_success "✅ Medical Student Journey: COMPLETED"
    return 0
}

# Test journey 3: Agent Bridge orchestration
journey_agent_orchestration() {
    log_info "🤖 Testing Journey: Agent Bridge Orchestration"
    
    # Step 1: Agent health check
    log_info "Step 1: Checking Agent Bridge health..."
    local agent_health
    agent_health=$(curl -s --max-time "$TIMEOUT" "$API_URL/agent/health" || echo "FAILED")
    
    if [[ "$agent_health" == *"healthy"* ]] || [[ "$agent_health" == *"status"* ]]; then
        log_success "Agent Bridge health check passed"
    else
        log_error "Agent Bridge health check failed: $agent_health"
        return 1
    fi
    
    # Step 2: Agent capabilities verification
    log_info "Step 2: Verifying Agent Bridge capabilities..."
    local capabilities
    capabilities=$(curl -s --max-time "$TIMEOUT" "$API_URL/agent/capabilities" || echo "FAILED")
    
    if [[ "$capabilities" == *"capabilities"* ]]; then
        local capability_count
        capability_count=$(echo "$capabilities" | jq '.capabilities | length' 2>/dev/null || echo "0")
        log_success "Agent capabilities verified: $capability_count capabilities active"
    else
        log_error "Agent capabilities check failed: $capabilities"
        return 1
    fi
    
    # Step 3: Simulate agent task execution
    log_info "Step 3: Simulating agent task execution..."
    local task_request='{
        "task_id": "test-task-'$(date +%s)'",
        "capability": "scholarship_api.search",
        "parameters": {
            "query": "engineering scholarships",
            "filters": {
                "min_amount": 5000
            }
        },
        "requester": "command_center_test"
    }'
    
    local task_response
    task_response=$(curl -s --max-time "$TIMEOUT" \
        -H "Content-Type: application/json" \
        -d "$task_request" \
        "$API_URL/agent/execute" \
        || echo "FAILED")
    
    if [[ "$task_response" == *"result"* ]] || [[ "$task_response" == *"success"* ]]; then
        log_success "Agent task execution successful"
    else
        log_error "Agent task execution failed: $task_response"
        return 1
    fi
    
    log_success "✅ Agent Bridge Orchestration Journey: COMPLETED"
    return 0
}

# Performance stress test
journey_performance_stress() {
    log_info "⚡ Testing Journey: Performance Stress Test"
    
    # Concurrent requests to test performance under load
    local concurrent_requests=10
    local pids=()
    
    log_info "Executing $concurrent_requests concurrent requests..."
    
    for i in $(seq 1 $concurrent_requests); do
        {
            local start_time=$(date +%s%N)
            curl -s --max-time "$TIMEOUT" "$API_URL/api/v1/search?q=test$i" >/dev/null
            local end_time=$(date +%s%N)
            local duration=$(( (end_time - start_time) / 1000000 ))  # milliseconds
            echo "$duration" > "/tmp/perf_$i.txt"
        } &
        pids+=($!)
    done
    
    # Wait for all requests to complete
    for pid in "${pids[@]}"; do
        wait "$pid"
    done
    
    # Calculate performance metrics
    local total_time=0
    local max_time=0
    local request_count=0
    
    for i in $(seq 1 $concurrent_requests); do
        if [[ -f "/tmp/perf_$i.txt" ]]; then
            local time
            time=$(cat "/tmp/perf_$i.txt")
            total_time=$((total_time + time))
            if [[ $time -gt $max_time ]]; then
                max_time=$time
            fi
            request_count=$((request_count + 1))
            rm -f "/tmp/perf_$i.txt"
        fi
    done
    
    if [[ $request_count -gt 0 ]]; then
        local avg_time=$((total_time / request_count))
        log_success "Performance test completed: ${request_count} requests, avg ${avg_time}ms, max ${max_time}ms"
        
        if [[ $max_time -lt 5000 ]]; then  # 5 seconds max
            log_success "Performance within acceptable limits"
        else
            log_warning "Performance may be degraded - max response time ${max_time}ms"
        fi
    else
        log_error "Performance test failed - no successful requests"
        return 1
    fi
    
    log_success "✅ Performance Stress Test Journey: COMPLETED"
    return 0
}

# Run all synthetic journeys
run_all_journeys() {
    log_info "🚀 Starting Synthetic User Journeys Validation"
    echo "Target API: $API_URL"
    echo "Test User ID: $USER_ID"
    echo ""
    
    local journey_results=()
    local total_journeys=0
    local passed_journeys=0
    
    # Execute all journeys
    local journeys=(
        "journey_engineering_student"
        "journey_medical_student" 
        "journey_agent_orchestration"
        "journey_performance_stress"
    )
    
    for journey in "${journeys[@]}"; do
        echo ""
        if $journey; then
            journey_results+=("✅ $journey: PASSED")
            ((passed_journeys++))
        else
            journey_results+=("❌ $journey: FAILED")
        fi
        ((total_journeys++))
    done
    
    # Final summary
    echo ""
    echo "=========================================="
    echo "🎯 SYNTHETIC JOURNEYS SUMMARY"
    echo "=========================================="
    
    for result in "${journey_results[@]}"; do
        echo "$result"
    done
    
    echo ""
    echo "Results: $passed_journeys/$total_journeys journeys passed"
    
    if [[ $passed_journeys -eq $total_journeys ]]; then
        log_success "✅ ALL SYNTHETIC JOURNEYS PASSED"
        echo ""
        log_success "🚀 CANARY DEPLOYMENT VALIDATION SUCCESSFUL"
        return 0
    else
        log_error "❌ SOME SYNTHETIC JOURNEYS FAILED"
        echo ""
        log_error "🛑 CANARY DEPLOYMENT VALIDATION FAILED"
        return 1
    fi
}

# Script usage
usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Synthetic user journeys for canary deployment validation

OPTIONS:
    -h, --help          Show this help message
    -u, --url URL       API base URL (default: http://localhost:5000)
    -j, --journey NAME  Run specific journey only
    -v, --verbose       Enable verbose output

AVAILABLE JOURNEYS:
    engineering_student     Engineering student scholarship search
    medical_student        Medical student scholarship search  
    agent_orchestration    Agent Bridge orchestration test
    performance_stress     Concurrent performance test
    all                   Run all journeys (default)

EXAMPLES:
    $0                                    # Run all journeys
    $0 --journey engineering_student      # Run specific journey
    $0 --url https://api.example.com      # Use production URL

EOF
}

# Parse command line arguments
SPECIFIC_JOURNEY=""
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -u|--url)
            API_URL="$2"
            shift 2
            ;;
        -j|--journey)
            SPECIFIC_JOURNEY="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -*)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
        *)
            log_error "Unexpected argument: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate dependencies
command -v curl >/dev/null 2>&1 || { log_error "curl is required"; exit 1; }
command -v jq >/dev/null 2>&1 || { log_error "jq is required"; exit 1; }

# Execute journeys
if [[ -n "$SPECIFIC_JOURNEY" ]]; then
    case "$SPECIFIC_JOURNEY" in
        "engineering_student")
            journey_engineering_student
            ;;
        "medical_student")
            journey_medical_student
            ;;
        "agent_orchestration")
            journey_agent_orchestration
            ;;
        "performance_stress")
            journey_performance_stress
            ;;
        "all")
            run_all_journeys
            ;;
        *)
            log_error "Unknown journey: $SPECIFIC_JOURNEY"
            usage
            exit 1
            ;;
    esac
else
    run_all_journeys
fi
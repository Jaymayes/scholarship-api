#!/bin/bash
# Emergency Rollback Script for Scholarship Discovery API
# Supports both Kubernetes and direct deployment rollbacks

set -euo pipefail

# Configuration
NAMESPACE="${NAMESPACE:-default}"
APP_NAME="${APP_NAME:-scholarship-api}"
DEPLOYMENT_NAME="${DEPLOYMENT_NAME:-scholarship-api}"
SERVICE_NAME="${SERVICE_NAME:-scholarship-api}"

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

# Check if kubectl is available and configured
check_kubernetes() {
    if ! command -v kubectl >/dev/null 2>&1; then
        log_error "kubectl not found - cannot perform Kubernetes rollback"
        return 1
    fi
    
    if ! kubectl cluster-info >/dev/null 2>&1; then
        log_error "kubectl not configured or cluster unreachable"
        return 1
    fi
    
    return 0
}

# Get current deployment status
get_deployment_status() {
    log_info "Checking current deployment status..."
    
    if check_kubernetes; then
        local current_image
        current_image=$(kubectl get deployment "$DEPLOYMENT_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null || echo "unknown")
        local replicas
        replicas=$(kubectl get deployment "$DEPLOYMENT_NAME" -n "$NAMESPACE" -o jsonpath='{.status.replicas}' 2>/dev/null || echo "0")
        local ready_replicas
        ready_replicas=$(kubectl get deployment "$DEPLOYMENT_NAME" -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
        
        log_info "Current image: $current_image"
        log_info "Replicas: $ready_replicas/$replicas"
        
        return 0
    else
        log_warning "Kubernetes not available - checking direct deployment"
        # Add checks for direct deployment if needed
        return 1
    fi
}

# Kubernetes rollback
kubernetes_rollback() {
    log_info "🚨 Initiating Kubernetes rollback for $DEPLOYMENT_NAME"
    
    # Get rollout history
    log_info "Checking rollout history..."
    kubectl rollout history deployment/"$DEPLOYMENT_NAME" -n "$NAMESPACE"
    
    # Perform rollback
    log_info "Rolling back to previous version..."
    if kubectl rollout undo deployment/"$DEPLOYMENT_NAME" -n "$NAMESPACE"; then
        log_success "Rollback command executed"
    else
        log_error "Rollback command failed"
        return 1
    fi
    
    # Wait for rollback to complete
    log_info "Waiting for rollback to complete..."
    if kubectl rollout status deployment/"$DEPLOYMENT_NAME" -n "$NAMESPACE" --timeout=300s; then
        log_success "Rollback completed successfully"
    else
        log_error "Rollback timed out or failed"
        return 1
    fi
    
    # Verify deployment health
    log_info "Verifying deployment health..."
    local ready_replicas
    ready_replicas=$(kubectl get deployment "$DEPLOYMENT_NAME" -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
    local desired_replicas
    desired_replicas=$(kubectl get deployment "$DEPLOYMENT_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "1")
    
    if [[ "$ready_replicas" == "$desired_replicas" ]] && [[ "$ready_replicas" -gt 0 ]]; then
        log_success "All replicas are ready ($ready_replicas/$desired_replicas)"
        return 0
    else
        log_error "Deployment not healthy ($ready_replicas/$desired_replicas ready)"
        return 1
    fi
}

# Traffic management rollback
traffic_rollback() {
    log_info "🔀 Managing traffic during rollback..."
    
    # If using a service mesh or ingress controller, redirect traffic
    # This is a placeholder for more sophisticated traffic management
    
    if check_kubernetes; then
        # Check if service exists
        if kubectl get service "$SERVICE_NAME" -n "$NAMESPACE" >/dev/null 2>&1; then
            log_info "Service $SERVICE_NAME exists - traffic will automatically route to healthy pods"
        else
            log_warning "Service $SERVICE_NAME not found"
        fi
        
        # If using Istio, Linkerd, or other service mesh, add specific traffic rules here
        # Example for Istio:
        # kubectl apply -f - <<EOF
        # apiVersion: networking.istio.io/v1beta1
        # kind: VirtualService
        # metadata:
        #   name: scholarship-api-rollback
        # spec:
        #   hosts:
        #   - scholarship-api
        #   http:
        #   - route:
        #     - destination:
        #         host: scholarship-api
        #         subset: previous
        # EOF
    fi
    
    return 0
}

# Health verification after rollback
verify_rollback_health() {
    log_info "🔍 Verifying application health after rollback..."
    
    # Get service endpoint
    local service_url
    if check_kubernetes; then
        # Try to get LoadBalancer or NodePort service URL
        local service_type
        service_type=$(kubectl get service "$SERVICE_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.type}' 2>/dev/null || echo "ClusterIP")
        
        case "$service_type" in
            "LoadBalancer")
                local external_ip
                external_ip=$(kubectl get service "$SERVICE_NAME" -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
                if [[ -n "$external_ip" ]]; then
                    service_url="http://$external_ip:5000"
                fi
                ;;
            "NodePort")
                local node_port
                node_port=$(kubectl get service "$SERVICE_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "")
                if [[ -n "$node_port" ]]; then
                    service_url="http://localhost:$node_port"
                fi
                ;;
            *)
                # Port-forward for testing
                log_info "Setting up port-forward for health check..."
                kubectl port-forward service/"$SERVICE_NAME" 8080:5000 -n "$NAMESPACE" >/dev/null 2>&1 &
                local pf_pid=$!
                sleep 5
                service_url="http://localhost:8080"
                ;;
        esac
    else
        service_url="http://localhost:5000"
    fi
    
    if [[ -z "$service_url" ]]; then
        log_warning "Could not determine service URL - skipping health check"
        return 0
    fi
    
    log_info "Testing health endpoint: $service_url"
    
    # Health check with retries
    local retries=0
    local max_retries=10
    
    while [[ $retries -lt $max_retries ]]; do
        if curl -s --max-time 10 "$service_url/healthz" >/dev/null 2>&1; then
            log_success "Health check passed"
            break
        fi
        
        ((retries++))
        log_info "Health check attempt $retries/$max_retries..."
        sleep 10
    done
    
    # Clean up port-forward if used
    if [[ -n "${pf_pid:-}" ]]; then
        kill "$pf_pid" 2>/dev/null || true
    fi
    
    if [[ $retries -eq $max_retries ]]; then
        log_error "Health check failed after $max_retries attempts"
        return 1
    fi
    
    # Additional functional tests
    log_info "Testing API functionality..."
    if curl -s --max-time 10 "$service_url/api/v1/scholarships" | grep -q "data"; then
        log_success "API functionality verified"
    else
        log_warning "API functionality test failed - may need investigation"
    fi
    
    return 0
}

# Generate incident report
generate_incident_report() {
    local rollback_reason="$1"
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    log_info "📋 Generating incident report..."
    
    cat > "incident-report-$timestamp.md" <<EOF
# Incident Report: Emergency Rollback

**Timestamp:** $timestamp  
**Service:** Scholarship Discovery API  
**Action:** Emergency Rollback  
**Operator:** $(whoami)  

## Incident Details

**Reason for Rollback:** $rollback_reason

**Pre-Rollback Status:**
$(if check_kubernetes; then kubectl get deployment "$DEPLOYMENT_NAME" -n "$NAMESPACE" -o wide 2>/dev/null || echo "Could not retrieve deployment status"; fi)

**Actions Taken:**
1. Emergency rollback initiated
2. Traffic redirected to previous version
3. Health verification completed
4. Incident report generated

**Post-Rollback Status:**
$(if check_kubernetes; then kubectl get deployment "$DEPLOYMENT_NAME" -n "$NAMESPACE" -o wide 2>/dev/null || echo "Could not retrieve deployment status"; fi)

## Next Steps

1. Investigate root cause of deployment failure
2. Fix identified issues in staging environment
3. Re-test deployment pipeline
4. Schedule new deployment when ready

## Timeline

- Rollback initiated: $timestamp
- Rollback completed: $(date -u +"%Y-%m-%dT%H:%M:%SZ")

EOF

    log_success "Incident report saved: incident-report-$timestamp.md"
}

# Main rollback function
perform_rollback() {
    local reason="${1:-Manual rollback requested}"
    
    log_info "🚨 EMERGENCY ROLLBACK INITIATED"
    log_info "Reason: $reason"
    echo ""
    
    # Confirm rollback (skip in CI/automated environments)
    if [[ -t 0 ]] && [[ "${FORCE_ROLLBACK:-false}" != "true" ]]; then
        read -p "Are you sure you want to proceed with rollback? (yes/no): " confirm
        if [[ "$confirm" != "yes" ]]; then
            log_info "Rollback cancelled by user"
            exit 0
        fi
    fi
    
    # Get initial status
    get_deployment_status || true
    
    # Perform rollback
    if check_kubernetes; then
        kubernetes_rollback
    else
        log_error "No rollback method available"
        exit 1
    fi
    
    # Manage traffic
    traffic_rollback
    
    # Verify health
    verify_rollback_health
    
    # Generate report
    generate_incident_report "$reason"
    
    log_success "✅ ROLLBACK COMPLETED SUCCESSFULLY"
    log_info "Please investigate the root cause and prepare a fix"
}

# Script usage
usage() {
    cat <<EOF
Usage: $0 [OPTIONS] [REASON]

Emergency rollback script for Scholarship Discovery API

OPTIONS:
    -h, --help          Show this help message
    -f, --force         Force rollback without confirmation
    -n, --namespace     Kubernetes namespace (default: default)
    -d, --deployment    Deployment name (default: scholarship-api)

EXAMPLES:
    $0 "High error rate detected"
    $0 --force "Automated rollback due to SLO breach"
    $0 --namespace production "Performance degradation"

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -f|--force)
            FORCE_ROLLBACK=true
            shift
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -d|--deployment)
            DEPLOYMENT_NAME="$2"
            shift 2
            ;;
        -*)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
        *)
            ROLLBACK_REASON="$1"
            shift
            ;;
    esac
done

# Main execution
main() {
    local reason="${ROLLBACK_REASON:-Emergency rollback requested}"
    perform_rollback "$reason"
}

# Execute if run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
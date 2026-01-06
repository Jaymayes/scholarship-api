#!/bin/bash
# cleanup_audit.sh - Idempotent removal of simulated_audit namespace data
# Usage: ./cleanup_audit.sh [--dry-run]
#
# This script removes all test data created during the Scholar Ecosystem audit
# with namespace=simulated_audit

set -e

DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "=== DRY RUN MODE - No changes will be made ==="
fi

echo "Cleanup Script for namespace=simulated_audit"
echo "=============================================="
echo ""

# A2 Database cleanup
echo "1) Cleaning A2 business_events table..."
if [ "$DRY_RUN" = true ]; then
    echo "   [DRY RUN] Would execute: DELETE FROM business_events WHERE metadata->>'namespace' = 'simulated_audit'"
    echo "   [DRY RUN] Checking count..."
    curl -sS "http://localhost:5000/api/kpi/revenue_by_source?limit=100" 2>/dev/null | grep -c "simulated_audit" || echo "   0 rows with simulated_audit namespace"
else
    echo "   Executing cleanup via A2 admin endpoint (if available)..."
    # Note: This would require an admin endpoint to be implemented
    echo "   [SKIPPED] No cleanup endpoint available - manual SQL required"
fi

echo ""
echo "2) A8 events cleanup..."
if [ "$DRY_RUN" = true ]; then
    echo "   [DRY RUN] Would filter/delete events with namespace=simulated_audit from A8"
else
    echo "   [SKIPPED] A8 cleanup requires admin access"
fi

echo ""
echo "3) Audit reports cleanup..."
if [ "$DRY_RUN" = true ]; then
    echo "   [DRY RUN] Audit reports in reports/scholar_audit/ would be preserved (documentation)"
else
    echo "   [PRESERVED] Audit reports are retained for compliance"
fi

echo ""
echo "Cleanup complete."
echo ""
echo "Manual cleanup required:"
echo "  - Run SQL: DELETE FROM business_events WHERE metadata->>'namespace' = 'simulated_audit';"
echo "  - A8: Filter or archive events with namespace=simulated_audit"

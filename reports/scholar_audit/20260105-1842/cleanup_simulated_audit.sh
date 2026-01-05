#!/bin/bash
# Cleanup script for simulated_audit namespace test data
# Usage: ./cleanup_simulated_audit.sh [--dry-run]

set -e

DRY_RUN=false
if [ "$1" == "--dry-run" ]; then
    DRY_RUN=true
    echo "=== DRY RUN MODE ==="
fi

echo "Cleanup: simulated_audit namespace"
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# A2 Local Database Cleanup
echo "=== A2 Local Database ==="
if [ "$DRY_RUN" == "true" ]; then
    echo "Would execute: DELETE FROM business_events WHERE payload->>'namespace' = 'simulated_audit'"
else
    psql "$DATABASE_URL" -c "DELETE FROM business_events WHERE payload->>'namespace' = 'simulated_audit'" 2>/dev/null || echo "No business_events table or no matching records"
fi

# A8 Event Store Cleanup (requires A8 access)
echo ""
echo "=== A8 Event Store ==="
echo "NOTE: A8 cleanup requires direct database access to A8 project"
echo "Suggested SQL:"
echo "  DELETE FROM events WHERE payload->>'namespace' = 'simulated_audit';"
echo "  DELETE FROM events WHERE payload->>'simulated' = 'true';"

# Audit Report TTL
echo ""
echo "=== Audit Reports ==="
echo "Reports in /reports/scholar_audit/ have 14-day retention"
echo "To clean old reports:"
echo "  find /reports/scholar_audit -mtime +14 -type d -exec rm -rf {} +"

echo ""
echo "Cleanup complete (or dry-run preview complete)"

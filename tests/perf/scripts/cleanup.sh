#!/bin/bash
set -e

echo "========================================"
echo "A2 Performance Test Cleanup"
echo "========================================"
echo "Namespace: perf_test"
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "========================================"

cleanup_database() {
    echo ">>> Cleaning up perf_test namespace from database..."
    
    psql "$DATABASE_URL" -c "
        DELETE FROM business_events 
        WHERE payload->>'namespace' = 'perf_test' 
           OR payload->>'user_id' LIKE 'perf_test_%'
           OR payload->>'event_id' LIKE 'perf_test_%';
    " 2>/dev/null || echo "Note: business_events cleanup skipped (table may not exist or no matching records)"
    
    echo "<<< Database cleanup complete"
}

cleanup_reports() {
    echo ">>> Cleaning up old report files..."
    REPORTS_DIR="$(dirname "$0")/../reports"
    if [ -d "$REPORTS_DIR" ]; then
        find "$REPORTS_DIR" -name "*.json" -mtime +7 -delete 2>/dev/null || true
        echo "<<< Old reports cleaned (>7 days)"
    fi
}

echo ""
echo "DRY RUN MODE - No changes will be made"
echo "To execute cleanup, set DRY_RUN=false"
echo ""

if [ "${DRY_RUN:-true}" = "false" ]; then
    cleanup_database
    cleanup_reports
    echo ""
    echo "Cleanup complete!"
else
    echo "Would clean up:"
    echo "  - business_events with namespace=perf_test"
    echo "  - Report files older than 7 days"
    echo ""
    echo "Run with DRY_RUN=false to execute"
fi

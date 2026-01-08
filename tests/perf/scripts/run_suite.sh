#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PERF_DIR="$(dirname "$SCRIPT_DIR")"
REPORTS_DIR="$PERF_DIR/reports"
K6_DIR="$PERF_DIR/k6"

BASE_URL="${BASE_URL:-http://localhost:5000}"
VERSION="${VERSION:-$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')}"

mkdir -p "$REPORTS_DIR"

echo "========================================"
echo "A2 Performance Test Suite"
echo "========================================"
echo "BASE_URL: $BASE_URL"
echo "VERSION: $VERSION"
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "========================================"

run_test() {
    local test_name=$1
    local test_file=$2
    echo ""
    echo ">>> Running $test_name..."
    k6 run --env BASE_URL="$BASE_URL" --env VERSION="$VERSION" "$K6_DIR/$test_file" || {
        echo "!!! $test_name failed"
        return 1
    }
    echo "<<< $test_name complete"
}

case "${1:-smoke}" in
    smoke)
        run_test "Smoke Test" "a2_smoke.js"
        ;;
    baseline)
        run_test "Baseline Test" "a2_baseline.js"
        ;;
    ramp)
        run_test "Ramp Test" "a2_ramp.js"
        ;;
    spike)
        run_test "Spike Test" "a2_spike.js"
        ;;
    soak)
        run_test "Soak Test" "a2_soak.js"
        ;;
    burst)
        run_test "Burst Test" "a2_burst.js"
        ;;
    all)
        run_test "Smoke Test" "a2_smoke.js"
        run_test "Baseline Test" "a2_baseline.js"
        run_test "Ramp Test" "a2_ramp.js"
        run_test "Spike Test" "a2_spike.js"
        ;;
    *)
        echo "Usage: $0 {smoke|baseline|ramp|spike|soak|burst|all}"
        exit 1
        ;;
esac

echo ""
echo "========================================"
echo "Test suite complete. Reports in: $REPORTS_DIR"
echo "========================================"

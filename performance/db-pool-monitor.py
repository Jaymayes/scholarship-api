#!/usr/bin/env python3
"""
Priority 2 Day 2: Database Connection Pool Monitoring
Monitors DB connection pool saturation with <80% gate requirement
"""

import json
import os
import sys
import time
from datetime import datetime
from typing import Any

import psutil


def get_db_pool_metrics() -> dict[str, Any]:
    """Get database connection pool metrics"""
    try:
        # PostgreSQL connection monitoring via system processes
        postgres_processes = []

        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'postgres' in proc.info['name'].lower():
                    # Get connections separately to handle permissions issues
                    try:
                        connections = proc.connections() or []
                    except (psutil.AccessDenied, psutil.NoSuchProcess):
                        connections = []

                    postgres_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'connections': len(connections)
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Calculate pool utilization
        total_connections = sum(p['connections'] for p in postgres_processes)
        max_connections = int(os.getenv('DB_MAX_CONNECTIONS', '100'))  # Default PostgreSQL limit
        pool_utilization = (total_connections / max_connections) * 100

        return {
            'total_connections': total_connections,
            'max_connections': max_connections,
            'pool_utilization_percent': round(pool_utilization, 2),
            'postgres_processes': len(postgres_processes),
            'timestamp': datetime.now().isoformat(),
            'gate_passed': pool_utilization < 80  # Priority 2 Day 2 requirement
        }

    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'gate_passed': False
        }

def monitor_continuous(duration_seconds: int = 60, interval: int = 5):
    """Monitor DB pool continuously during load tests"""
    samples = []
    start_time = time.time()

    print(f"🔍 Monitoring DB connection pool for {duration_seconds}s (every {interval}s)")
    print("Timestamp,Total_Connections,Pool_Utilization_%,Gate_Passed")

    while time.time() - start_time < duration_seconds:
        metrics = get_db_pool_metrics()
        samples.append(metrics)

        if 'error' not in metrics:
            gate_status = "✅ PASS" if metrics['gate_passed'] else "❌ FAIL"
            print(f"{metrics['timestamp']},{metrics['total_connections']},{metrics['pool_utilization_percent']},{gate_status}")

            # Alert if pool utilization exceeds 80%
            if metrics['pool_utilization_percent'] >= 80:
                print(f"🚨 ALERT: DB pool utilization {metrics['pool_utilization_percent']}% exceeds 80% threshold!")
        else:
            print(f"{metrics['timestamp']},ERROR,ERROR,❌ FAIL")

        time.sleep(interval)

    # Generate summary
    successful_samples = [s for s in samples if 'error' not in s]
    if successful_samples:
        avg_utilization = sum(s['pool_utilization_percent'] for s in successful_samples) / len(successful_samples)
        max_utilization = max(s['pool_utilization_percent'] for s in successful_samples)
        gate_failures = sum(1 for s in successful_samples if not s['gate_passed'])

        summary = {
            'duration_seconds': duration_seconds,
            'total_samples': len(samples),
            'successful_samples': len(successful_samples),
            'avg_pool_utilization': round(avg_utilization, 2),
            'max_pool_utilization': max_utilization,
            'gate_failures': gate_failures,
            'gate_pass_rate': round((len(successful_samples) - gate_failures) / len(successful_samples) * 100, 2),
            'overall_gate_passed': gate_failures == 0 and max_utilization < 80
        }

        print("\n📊 DB Pool Monitoring Summary:")
        print(f"   Average utilization: {summary['avg_pool_utilization']}%")
        print(f"   Maximum utilization: {summary['max_pool_utilization']}%")
        print(f"   Gate pass rate: {summary['gate_pass_rate']}%")
        print(f"   Overall gate: {'✅ PASS' if summary['overall_gate_passed'] else '❌ FAIL'}")

        return summary

    return {'error': 'No successful samples collected'}

def validate_db_pool_gate() -> bool:
    """Validate DB connection pool is under 80% - for CI gates"""
    print("🔍 Validating DB connection pool utilization gate (<80%)")

    metrics = get_db_pool_metrics()

    if 'error' in metrics:
        print(f"❌ DB pool monitoring failed: {metrics['error']}")
        return False

    utilization = metrics['pool_utilization_percent']
    gate_passed = metrics['gate_passed']

    print(f"📊 Current DB pool utilization: {utilization}%")
    print("🎯 Gate requirement: <80%")

    if gate_passed:
        print(f"✅ GATE PASSED: DB pool utilization {utilization}% is within limits")
        return True
    print(f"❌ GATE FAILED: DB pool utilization {utilization}% exceeds 80% threshold")
    return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "monitor":
            duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60
            interval = int(sys.argv[3]) if len(sys.argv) > 3 else 5
            result = monitor_continuous(duration, interval)

            # Export for CI artifacts
            with open('db-pool-monitoring-results.json', 'w') as f:
                json.dump(result, f, indent=2)

            # Exit with appropriate code for CI
            sys.exit(0 if result.get('overall_gate_passed', False) else 1)

        elif command == "validate":
            gate_passed = validate_db_pool_gate()
            sys.exit(0 if gate_passed else 1)

        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    else:
        # Default: single check
        metrics = get_db_pool_metrics()
        print(json.dumps(metrics, indent=2))

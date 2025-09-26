#!/usr/bin/env python3
"""
Priority 2 Day 2: Resource Metrics Capture
Captures final resource metrics after performance testing
"""

import json
import os
import sys
from datetime import datetime
from statistics import mean, median

import psutil
import psycopg2


def capture_final_metrics():
    """Capture comprehensive resource metrics at end of performance test"""

    print("Capturing final resource metrics...", file=sys.stderr)

    metrics = {
        'capture_time': datetime.now().isoformat(),
        'system': {},
        'database': {},
        'application': {},
        'summary': {}
    }

    # System metrics
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        metrics['system'] = {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_mb': memory.available / 1024 / 1024,
            'memory_used_mb': memory.used / 1024 / 1024,
            'disk_usage_percent': (disk.used / disk.total) * 100,
            'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
        }
    except Exception as e:
        print(f"Error capturing system metrics: {e}", file=sys.stderr)
        metrics['system'] = {'error': str(e)}

    # Database metrics
    try:
        conn_str = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/scholarship_api_test')
        conn = psycopg2.connect(conn_str)
        cur = conn.cursor()

        # Connection statistics
        cur.execute("""
            SELECT
                count(*) FILTER (WHERE state = 'active') as active_connections,
                count(*) FILTER (WHERE state = 'idle') as idle_connections,
                count(*) as total_connections,
                current_setting('max_connections')::int as max_connections
            FROM pg_stat_activity
            WHERE datname = current_database()
        """)

        active, idle, total, max_conn = cur.fetchone()

        # Database performance statistics
        cur.execute("""
            SELECT
                schemaname,
                tablename,
                seq_scan,
                seq_tup_read,
                idx_scan,
                idx_tup_fetch,
                n_tup_ins,
                n_tup_upd,
                n_tup_del
            FROM pg_stat_user_tables
            ORDER BY seq_tup_read DESC
            LIMIT 5
        """)

        table_stats = cur.fetchall()

        # Query performance
        cur.execute("""
            SELECT
                calls,
                total_time,
                mean_time,
                query
            FROM pg_stat_statements
            WHERE query NOT LIKE '%pg_stat%'
            ORDER BY total_time DESC
            LIMIT 5
        """) if 'pg_stat_statements' in str(cur.mogrify("SELECT * FROM pg_extension")) else None

        query_stats = cur.fetchall() if cur.description else []

        metrics['database'] = {
            'connections': {
                'active': active,
                'idle': idle,
                'total': total,
                'max_connections': max_conn,
                'usage_percent': (total / max_conn) * 100 if max_conn > 0 else 0
            },
            'table_statistics': [
                {
                    'schema': row[0],
                    'table': row[1],
                    'seq_scans': row[2],
                    'seq_reads': row[3],
                    'index_scans': row[4],
                    'index_fetches': row[5],
                    'inserts': row[6],
                    'updates': row[7],
                    'deletes': row[8]
                } for row in table_stats
            ],
            'slow_queries': [
                {
                    'calls': row[0],
                    'total_time': row[1],
                    'mean_time': row[2],
                    'query': row[3][:100] + '...' if len(row[3]) > 100 else row[3]
                } for row in query_stats
            ]
        }

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error capturing database metrics: {e}", file=sys.stderr)
        metrics['database'] = {'error': str(e)}

    # Application metrics (from live monitoring if available)
    try:
        live_metrics_file = 'performance/results/resource-metrics-live.json'
        if os.path.exists(live_metrics_file):
            with open(live_metrics_file) as f:
                live_data = json.load(f)

            # Calculate summary statistics
            cpu_values = [m['system'] for m in live_data.get('cpu', [])]
            memory_values = [m['system_used_percent'] for m in live_data.get('memory', [])]
            db_usage_values = [m['usage_percent'] for m in live_data.get('db_connections', [])]

            metrics['application'] = {
                'monitoring_duration_seconds': len(cpu_values),
                'cpu_stats': {
                    'mean': mean(cpu_values) if cpu_values else 0,
                    'median': median(cpu_values) if cpu_values else 0,
                    'max': max(cpu_values) if cpu_values else 0,
                    'min': min(cpu_values) if cpu_values else 0
                },
                'memory_stats': {
                    'mean': mean(memory_values) if memory_values else 0,
                    'median': median(memory_values) if memory_values else 0,
                    'max': max(memory_values) if memory_values else 0,
                    'min': min(memory_values) if memory_values else 0
                },
                'db_connection_stats': {
                    'mean': mean(db_usage_values) if db_usage_values else 0,
                    'median': median(db_usage_values) if db_usage_values else 0,
                    'max': max(db_usage_values) if db_usage_values else 0,
                    'min': min(db_usage_values) if db_usage_values else 0
                }
            }

    except Exception as e:
        print(f"Error processing application metrics: {e}", file=sys.stderr)
        metrics['application'] = {'error': str(e)}

    # Generate summary for budget validation
    metrics['summary'] = {
        'cpu_usage_percent': metrics['system'].get('cpu_percent', 0),
        'memory_usage_percent': metrics['system'].get('memory_percent', 0),
        'db_pool_usage_percent': metrics['database'].get('connections', {}).get('usage_percent', 0),
        'performance_acceptable': True  # Will be determined by budget validator
    }

    # Performance thresholds check
    thresholds = {
        'cpu_max': 70,
        'memory_max': 80,
        'db_pool_max': 80
    }

    budget_violations = []

    if metrics['summary']['cpu_usage_percent'] > thresholds['cpu_max']:
        budget_violations.append(f"CPU usage {metrics['summary']['cpu_usage_percent']:.1f}% > {thresholds['cpu_max']}%")

    if metrics['summary']['memory_usage_percent'] > thresholds['memory_max']:
        budget_violations.append(f"Memory usage {metrics['summary']['memory_usage_percent']:.1f}% > {thresholds['memory_max']}%")

    if metrics['summary']['db_pool_usage_percent'] > thresholds['db_pool_max']:
        budget_violations.append(f"DB pool usage {metrics['summary']['db_pool_usage_percent']:.1f}% > {thresholds['db_pool_max']}%")

    if budget_violations:
        metrics['summary']['performance_acceptable'] = False
        metrics['summary']['budget_violations'] = budget_violations
        print(f"⚠️  Resource budget violations detected: {budget_violations}", file=sys.stderr)
    else:
        print("✅ All resource budgets within acceptable limits", file=sys.stderr)

    # Output JSON for CI processing
    print(json.dumps(metrics, indent=2))

    return metrics

if __name__ == '__main__':
    try:
        capture_final_metrics()
    except Exception as e:
        print(f"Error capturing metrics: {e}", file=sys.stderr)
        # Output minimal metrics structure for CI compatibility
        print(json.dumps({
            'error': str(e),
            'summary': {
                'cpu_usage_percent': 0,
                'memory_usage_percent': 0,
                'db_pool_usage_percent': 0,
                'performance_acceptable': False
            }
        }, indent=2))
        sys.exit(1)

#!/usr/bin/env python3
"""
Priority 2 Day 2: Performance Trend Tracker
Updates 10-run performance trend for CI trend analysis and regression detection
"""

import json
import csv
import argparse
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

def load_current_metrics(metrics_file: str) -> Dict[str, Any]:
    """Load current performance metrics"""
    
    with open(metrics_file, 'r') as f:
        metrics = json.load(f)
    
    return metrics

def load_trend_history(trend_file: str) -> List[Dict[str, Any]]:
    """Load existing trend history from CSV"""
    
    if not os.path.exists(trend_file):
        return []
    
    trend_data = []
    
    with open(trend_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert string values back to appropriate types
            processed_row = {}
            for key, value in row.items():
                if key == 'timestamp':
                    processed_row[key] = value
                elif key in ['overall_pass', 'p50_pass', 'p95_pass', 'p99_pass', 'error_rate_pass', 'zero_5xx_pass', 'db_pool_pass']:
                    processed_row[key] = value.lower() == 'true'
                else:
                    try:
                        processed_row[key] = float(value)
                    except ValueError:
                        processed_row[key] = value
            
            trend_data.append(processed_row)
    
    return trend_data

def extract_trend_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Extract key metrics for trend tracking"""
    
    timestamp = datetime.now().isoformat()
    
    trend_metrics = {
        'timestamp': timestamp,
        'test_date': datetime.now().strftime('%Y-%m-%d'),
        'test_time': datetime.now().strftime('%H:%M:%S'),
        
        # Latency metrics
        'p50_latency': metrics.get('latency', {}).get('p50', 0),
        'p95_latency': metrics.get('latency', {}).get('p95', 0),
        'p99_latency': metrics.get('latency', {}).get('p99', 0),
        'mean_latency': metrics.get('latency', {}).get('mean', 0),
        'max_latency': metrics.get('latency', {}).get('max', 0),
        
        # Reliability metrics
        'success_rate': metrics.get('reliability', {}).get('success_rate', 0),
        'error_rate': metrics.get('reliability', {}).get('error_rate', 0),
        'server_errors': metrics.get('reliability', {}).get('server_errors', 0),
        'total_requests': metrics.get('reliability', {}).get('total_requests', 0),
        
        # Throughput metrics
        'requests_per_second': metrics.get('throughput', {}).get('requests_per_second', 0),
        'test_duration': metrics.get('throughput', {}).get('test_duration_seconds', 0),
        
        # Resource metrics
        'cpu_usage': metrics.get('resources', {}).get('cpu_usage', 0),
        'memory_usage': metrics.get('resources', {}).get('memory_usage', 0),
        'db_pool_usage': metrics.get('resources', {}).get('db_pool_usage', 0),
        
        # Budget status
        'overall_pass': metrics.get('budget_status', {}).get('overall_pass', False),
        'p50_pass': metrics.get('budget_status', {}).get('p50_pass', False),
        'p95_pass': metrics.get('budget_status', {}).get('p95_pass', False),
        'p99_pass': metrics.get('budget_status', {}).get('p99_pass', False),
        'error_rate_pass': metrics.get('budget_status', {}).get('error_rate_pass', False),
        'zero_5xx_pass': metrics.get('budget_status', {}).get('zero_5xx_pass', False),
        'db_pool_pass': metrics.get('budget_status', {}).get('db_pool_pass', False),
    }
    
    return trend_metrics

def detect_regressions(current_metrics: Dict, trend_history: List[Dict], threshold: float = 0.2) -> List[str]:
    """Detect performance regressions compared to recent history"""
    
    if len(trend_history) < 3:
        return []  # Need sufficient history for comparison
    
    regressions = []
    
    # Calculate baseline from last 5 runs (excluding current)
    recent_runs = trend_history[-5:]
    
    key_metrics = [
        ('p95_latency', 'p95 latency', 'ms', 'increase'),
        ('p99_latency', 'p99 latency', 'ms', 'increase'),
        ('error_rate', 'error rate', '%', 'increase'),
        ('requests_per_second', 'throughput', 'RPS', 'decrease'),
        ('cpu_usage', 'CPU usage', '%', 'increase'),
        ('memory_usage', 'memory usage', '%', 'increase'),
    ]
    
    for metric_key, metric_name, unit, regression_type in key_metrics:
        if metric_key not in current_metrics:
            continue
        
        # Calculate baseline average
        baseline_values = [run.get(metric_key, 0) for run in recent_runs if metric_key in run]
        if not baseline_values:
            continue
        
        baseline_avg = sum(baseline_values) / len(baseline_values)
        current_value = current_metrics[metric_key]
        
        # Check for regression based on type
        if regression_type == 'increase':
            # Performance degradation = increase in latency, errors, resource usage
            if baseline_avg > 0:
                change_percent = (current_value - baseline_avg) / baseline_avg
                if change_percent > threshold:
                    regressions.append(
                        f"{metric_name} regression: {current_value:.1f}{unit} "
                        f"vs {baseline_avg:.1f}{unit} baseline (+{change_percent*100:.1f}%)"
                    )
        else:  # decrease
            # Performance degradation = decrease in throughput
            if baseline_avg > 0:
                change_percent = (baseline_avg - current_value) / baseline_avg
                if change_percent > threshold:
                    regressions.append(
                        f"{metric_name} regression: {current_value:.1f}{unit} "
                        f"vs {baseline_avg:.1f}{unit} baseline (-{change_percent*100:.1f}%)"
                    )
    
    return regressions

def save_updated_trend(trend_data: List[Dict], trend_file: str, max_runs: int = 10) -> None:
    """Save updated trend data to CSV, keeping only the last N runs"""
    
    # Keep only the most recent runs
    if len(trend_data) > max_runs:
        trend_data = trend_data[-max_runs:]
    
    if not trend_data:
        return
    
    # Ensure results directory exists
    os.makedirs(os.path.dirname(trend_file), exist_ok=True)
    
    # Write CSV with all metrics
    with open(trend_file, 'w', newline='') as f:
        fieldnames = trend_data[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(trend_data)
    
    print(f"Updated performance trend: {len(trend_data)} runs tracked", file=sys.stderr)

def generate_trend_summary(trend_data: List[Dict]) -> Dict[str, Any]:
    """Generate trend analysis summary"""
    
    if len(trend_data) < 2:
        return {'insufficient_data': True}
    
    recent_runs = trend_data[-5:] if len(trend_data) >= 5 else trend_data
    
    # Calculate trends for key metrics
    p95_values = [run.get('p95_latency', 0) for run in recent_runs]
    error_rates = [run.get('error_rate', 0) for run in recent_runs]
    success_rates = [run.get('overall_pass', False) for run in recent_runs]
    
    summary = {
        'total_runs': len(trend_data),
        'recent_runs_analyzed': len(recent_runs),
        'performance_trends': {
            'p95_latency_trend': 'improving' if len(p95_values) >= 2 and p95_values[-1] < p95_values[0] else 'stable' if len(p95_values) >= 2 and abs(p95_values[-1] - p95_values[0]) < 10 else 'declining',
            'error_rate_trend': 'improving' if len(error_rates) >= 2 and error_rates[-1] < error_rates[0] else 'stable' if len(error_rates) >= 2 and abs(error_rates[-1] - error_rates[0]) < 0.01 else 'declining',
            'avg_p95_latency': sum(p95_values) / len(p95_values) if p95_values else 0,
            'avg_error_rate': sum(error_rates) / len(error_rates) if error_rates else 0,
        },
        'reliability': {
            'success_rate_last_5_runs': (sum(1 for passed in success_rates if passed) / len(success_rates) * 100) if success_rates else 0,
            'consecutive_passes': len([run for run in trend_data[::-1] if run.get('overall_pass', False)]),
        }
    }
    
    return summary

def main():
    parser = argparse.ArgumentParser(description='Update performance trend tracking')
    parser.add_argument('--metrics', required=True, help='Path to current performance metrics JSON')
    parser.add_argument('--trend-file', required=True, help='Path to performance trend CSV file')
    parser.add_argument('--max-runs', type=int, default=10, help='Maximum number of runs to keep in trend')
    parser.add_argument('--regression-threshold', type=float, default=0.2, help='Regression detection threshold (20%)')
    
    args = parser.parse_args()
    
    try:
        # Load current metrics
        current_metrics = load_current_metrics(args.metrics)
        
        # Load existing trend history
        trend_history = load_trend_history(args.trend_file)
        
        # Extract trend metrics from current run
        trend_metrics = extract_trend_metrics(current_metrics)
        
        # Detect regressions before adding current run
        regressions = detect_regressions(trend_metrics, trend_history, args.regression_threshold)
        
        # Add current metrics to trend
        trend_history.append(trend_metrics)
        
        # Save updated trend
        save_updated_trend(trend_history, args.trend_file, args.max_runs)
        
        # Generate trend summary
        trend_summary = generate_trend_summary(trend_history)
        
        # Report results
        print(f"📊 Performance Trend Update Complete")
        print(f"   Total runs tracked: {len(trend_history)}")
        print(f"   Current p95 latency: {trend_metrics['p95_latency']:.1f}ms")
        print(f"   Current error rate: {trend_metrics['error_rate']:.3f}%")
        print(f"   Budget compliance: {'✅' if trend_metrics['overall_pass'] else '❌'}")
        
        if trend_summary.get('reliability'):
            print(f"   Success rate (last 5): {trend_summary['reliability']['success_rate_last_5_runs']:.1f}%")
            print(f"   Consecutive passes: {trend_summary['reliability']['consecutive_passes']}")
        
        # Report regressions
        if regressions:
            print(f"\n⚠️  Performance Regressions Detected:")
            for regression in regressions:
                print(f"   - {regression}")
            
            # Save regression report for CI
            os.makedirs('performance/results', exist_ok=True)
            with open('performance/results/regressions.json', 'w') as f:
                json.dump({
                    'regressions_detected': True,
                    'regression_count': len(regressions),
                    'regressions': regressions,
                    'threshold_percent': args.regression_threshold * 100
                }, f, indent=2)
        else:
            print(f"\n✅ No performance regressions detected")
            
            # Clean up regression file if exists
            regression_file = 'performance/results/regressions.json'
            if os.path.exists(regression_file):
                os.remove(regression_file)
        
        # Save trend summary for CI artifacts
        os.makedirs('performance/results', exist_ok=True)
        with open('performance/results/trend-summary.json', 'w') as f:
            json.dump(trend_summary, f, indent=2)
        
    except Exception as e:
        print(f"Error updating performance trend: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
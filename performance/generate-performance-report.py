#!/usr/bin/env python3
"""
Priority 2 Day 2: Performance Report Generator
Generates comprehensive HTML and JSON performance reports from k6 and resource metrics
"""

import json
import argparse
import os
import sys
from datetime import datetime
from statistics import mean, median, quantiles

def parse_k6_results(k6_file):
    """Parse k6 JSON results and extract key metrics"""
    
    print(f"Parsing k6 results from {k6_file}...", file=sys.stderr)
    
    with open(k6_file, 'r') as f:
        lines = f.readlines()
    
    metrics = {
        'latency': {},
        'throughput': {},
        'reliability': {},
        'raw_data': []
    }
    
    request_durations = []
    error_count = 0
    total_requests = 0
    status_codes = {}
    
    for line in lines:
        try:
            data = json.loads(line.strip())
            
            if data.get('type') == 'Point':
                metric_name = data.get('metric')
                value = data.get('data', {}).get('value', 0)
                
                # Collect HTTP request durations
                if metric_name == 'http_req_duration':
                    request_durations.append(value)
                
                # Count requests by status code
                elif metric_name == 'http_reqs':
                    total_requests += 1
                    tags = data.get('data', {}).get('tags', {})
                    status = tags.get('status', 'unknown')
                    status_codes[status] = status_codes.get(status, 0) + 1
                    
                    if int(status) >= 400:
                        error_count += 1
                
                metrics['raw_data'].append(data)
                
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            continue  # Skip malformed lines
    
    # Calculate latency percentiles
    if request_durations:
        metrics['latency'] = {
            'p50': median(request_durations),
            'p95': quantiles(request_durations, n=20)[18] if len(request_durations) >= 20 else max(request_durations),
            'p99': quantiles(request_durations, n=100)[98] if len(request_durations) >= 100 else max(request_durations),
            'mean': mean(request_durations),
            'min': min(request_durations),
            'max': max(request_durations),
            'count': len(request_durations)
        }
    
    # Calculate reliability metrics
    success_requests = sum(count for status, count in status_codes.items() if int(status) < 400)
    error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0
    success_rate = (success_requests / total_requests * 100) if total_requests > 0 else 0
    server_errors = sum(count for status, count in status_codes.items() if int(status) >= 500)
    
    metrics['reliability'] = {
        'total_requests': total_requests,
        'success_requests': success_requests,
        'error_requests': error_count,
        'success_rate': success_rate,
        'error_rate': error_rate,
        'server_errors': server_errors,
        'status_codes': status_codes
    }
    
    # Calculate throughput
    test_duration = max(
        (data.get('data', {}).get('time', 0) for data in metrics['raw_data'] 
         if data.get('type') == 'Point'), 
        default=1
    ) / 1000000000  # Convert nanoseconds to seconds
    
    metrics['throughput'] = {
        'requests_per_second': total_requests / test_duration if test_duration > 0 else 0,
        'test_duration_seconds': test_duration
    }
    
    print(f"Processed {total_requests} requests over {test_duration:.1f}s", file=sys.stderr)
    return metrics

def parse_resource_metrics(resource_file):
    """Parse resource metrics JSON"""
    
    print(f"Parsing resource metrics from {resource_file}...", file=sys.stderr)
    
    with open(resource_file, 'r') as f:
        resource_data = json.load(f)
    
    return {
        'cpu_usage': resource_data.get('summary', {}).get('cpu_usage_percent', 0),
        'memory_usage': resource_data.get('summary', {}).get('memory_usage_percent', 0),
        'db_pool_usage': resource_data.get('summary', {}).get('db_pool_usage_percent', 0),
        'system_details': resource_data.get('system', {}),
        'database_details': resource_data.get('database', {}),
        'application_details': resource_data.get('application', {}),
        'performance_acceptable': resource_data.get('summary', {}).get('performance_acceptable', True)
    }

def generate_html_report(metrics, resource_metrics, output_file):
    """Generate comprehensive HTML performance report"""
    
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Performance Test Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background: #f8f9fa; padding: 20px; border-radius: 5px; }}
            .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
            .metric-card {{ background: white; padding: 15px; border: 1px solid #ddd; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .metric-value {{ font-size: 2em; font-weight: bold; color: #28a745; }}
            .metric-label {{ color: #6c757d; font-size: 0.9em; }}
            .status-pass {{ color: #28a745; }}
            .status-fail {{ color: #dc3545; }}
            .table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
            .table th, .table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            .table th {{ background-color: #f8f9fa; }}
            .alert {{ padding: 10px; margin: 10px 0; border-radius: 4px; }}
            .alert-success {{ background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
            .alert-danger {{ background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 Performance Test Report</h1>
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            <p><strong>Test Duration:</strong> {metrics.get('throughput', {}).get('test_duration_seconds', 0):.1f} seconds</p>
            <p><strong>Total Requests:</strong> {metrics.get('reliability', {}).get('total_requests', 0):,}</p>
        </div>
        
        <h2>📊 Performance Budgets</h2>
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value {'status-pass' if metrics.get('latency', {}).get('p50', 999) <= 50 else 'status-fail'}">
                    {metrics.get('latency', {}).get('p50', 0):.1f}ms
                </div>
                <div class="metric-label">p50 Latency (≤ 50ms) {'✅' if metrics.get('latency', {}).get('p50', 999) <= 50 else '❌'}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-value {'status-pass' if metrics.get('latency', {}).get('p95', 999) <= 120 else 'status-fail'}">
                    {metrics.get('latency', {}).get('p95', 0):.1f}ms
                </div>
                <div class="metric-label">p95 Latency (≤ 120ms) {'✅' if metrics.get('latency', {}).get('p95', 999) <= 120 else '❌'}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-value {'status-pass' if metrics.get('latency', {}).get('p99', 999) <= 300 else 'status-fail'}">
                    {metrics.get('latency', {}).get('p99', 0):.1f}ms
                </div>
                <div class="metric-label">p99 Latency (≤ 300ms) {'✅' if metrics.get('latency', {}).get('p99', 999) <= 300 else '❌'}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-value {'status-pass' if metrics.get('reliability', {}).get('error_rate', 100) <= 0.1 else 'status-fail'}">
                    {metrics.get('reliability', {}).get('error_rate', 0):.3f}%
                </div>
                <div class="metric-label">Error Rate (≤ 0.1%) {'✅' if metrics.get('reliability', {}).get('error_rate', 100) <= 0.1 else '❌'}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-value {'status-pass' if metrics.get('reliability', {}).get('server_errors', 1) == 0 else 'status-fail'}">
                    {metrics.get('reliability', {}).get('server_errors', 0)}
                </div>
                <div class="metric-label">5xx Errors (0) {'✅' if metrics.get('reliability', {}).get('server_errors', 1) == 0 else '❌'}</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-value {'status-pass' if resource_metrics.get('db_pool_usage', 100) <= 80 else 'status-fail'}">
                    {resource_metrics.get('db_pool_usage', 0):.1f}%
                </div>
                <div class="metric-label">DB Pool Usage (≤ 80%) {'✅' if resource_metrics.get('db_pool_usage', 100) <= 80 else '❌'}</div>
            </div>
        </div>
        
        <h2>📈 Detailed Metrics</h2>
        
        <h3>Latency Distribution</h3>
        <table class="table">
            <tr><th>Percentile</th><th>Response Time</th></tr>
            <tr><td>p50 (median)</td><td>{metrics.get('latency', {}).get('p50', 0):.1f}ms</td></tr>
            <tr><td>p95</td><td>{metrics.get('latency', {}).get('p95', 0):.1f}ms</td></tr>
            <tr><td>p99</td><td>{metrics.get('latency', {}).get('p99', 0):.1f}ms</td></tr>
            <tr><td>Mean</td><td>{metrics.get('latency', {}).get('mean', 0):.1f}ms</td></tr>
            <tr><td>Min</td><td>{metrics.get('latency', {}).get('min', 0):.1f}ms</td></tr>
            <tr><td>Max</td><td>{metrics.get('latency', {}).get('max', 0):.1f}ms</td></tr>
        </table>
        
        <h3>Status Code Distribution</h3>
        <table class="table">
            <tr><th>Status Code</th><th>Count</th><th>Percentage</th></tr>
            {' '.join(f'<tr><td>{status}</td><td>{count}</td><td>{count/metrics.get("reliability", {}).get("total_requests", 1)*100:.1f}%</td></tr>' 
                     for status, count in metrics.get('reliability', {}).get('status_codes', {}).items())}
        </table>
        
        <h3>Resource Usage</h3>
        <table class="table">
            <tr><th>Resource</th><th>Usage</th><th>Status</th></tr>
            <tr><td>CPU</td><td>{resource_metrics.get('cpu_usage', 0):.1f}%</td><td>{'✅' if resource_metrics.get('cpu_usage', 100) <= 70 else '❌'}</td></tr>
            <tr><td>Memory</td><td>{resource_metrics.get('memory_usage', 0):.1f}%</td><td>{'✅' if resource_metrics.get('memory_usage', 100) <= 80 else '❌'}</td></tr>
            <tr><td>DB Connection Pool</td><td>{resource_metrics.get('db_pool_usage', 0):.1f}%</td><td>{'✅' if resource_metrics.get('db_pool_usage', 100) <= 80 else '❌'}</td></tr>
        </table>
        
        <h2>🎯 Performance Budget Summary</h2>
        <div class="alert {'alert-success' if all([
            metrics.get('latency', {}).get('p95', 999) <= 120,
            metrics.get('latency', {}).get('p99', 999) <= 300,
            metrics.get('reliability', {}).get('error_rate', 100) <= 0.1,
            metrics.get('reliability', {}).get('server_errors', 1) == 0,
            resource_metrics.get('db_pool_usage', 100) <= 80
        ]) else 'alert-danger'}">
            <strong>Overall Result:</strong> 
            {'✅ All performance budgets met!' if all([
                metrics.get('latency', {}).get('p95', 999) <= 120,
                metrics.get('latency', {}).get('p99', 999) <= 300,
                metrics.get('reliability', {}).get('error_rate', 100) <= 0.1,
                metrics.get('reliability', {}).get('server_errors', 1) == 0,
                resource_metrics.get('db_pool_usage', 100) <= 80
            ]) else '❌ Performance budget breach detected!'}
        </div>
        
        <div style="margin-top: 40px; padding: 20px; background: #f8f9fa; border-radius: 5px; text-align: center;">
            <p><em>Generated by Priority 2 Day 2 Performance Testing Framework</em></p>
            <p>🎯 Targets: p95 ≤ 120ms, p99 ≤ 300ms, Error Rate < 0.1%, Zero 5xx, DB Pool < 80%</p>
        </div>
    </body>
    </html>
    """
    
    with open(output_file, 'w') as f:
        f.write(html_template)
    
    print(f"HTML report generated: {output_file}", file=sys.stderr)

def generate_json_metrics(metrics, resource_metrics, output_file):
    """Generate JSON metrics for CI processing"""
    
    combined_metrics = {
        'timestamp': datetime.now().isoformat(),
        'latency': metrics.get('latency', {}),
        'reliability': metrics.get('reliability', {}),
        'throughput': metrics.get('throughput', {}),
        'resources': {
            'cpu_usage': resource_metrics.get('cpu_usage', 0),
            'memory_usage': resource_metrics.get('memory_usage', 0),
            'db_pool_usage': resource_metrics.get('db_pool_usage', 0)
        },
        'budget_status': {
            'p50_pass': metrics.get('latency', {}).get('p50', 999) <= 50,
            'p95_pass': metrics.get('latency', {}).get('p95', 999) <= 120,
            'p99_pass': metrics.get('latency', {}).get('p99', 999) <= 300,
            'error_rate_pass': metrics.get('reliability', {}).get('error_rate', 100) <= 0.1,
            'zero_5xx_pass': metrics.get('reliability', {}).get('server_errors', 1) == 0,
            'db_pool_pass': resource_metrics.get('db_pool_usage', 100) <= 80,
            'overall_pass': all([
                metrics.get('latency', {}).get('p95', 999) <= 120,
                metrics.get('latency', {}).get('p99', 999) <= 300,
                metrics.get('reliability', {}).get('error_rate', 100) <= 0.1,
                metrics.get('reliability', {}).get('server_errors', 1) == 0,
                resource_metrics.get('db_pool_usage', 100) <= 80
            ])
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(combined_metrics, f, indent=2)
    
    print(f"JSON metrics generated: {output_file}", file=sys.stderr)
    return combined_metrics

def main():
    parser = argparse.ArgumentParser(description='Generate performance test report from k6 and resource metrics')
    parser.add_argument('--k6-results', required=True, help='Path to k6 JSON results file')
    parser.add_argument('--resource-metrics', required=True, help='Path to resource metrics JSON file')
    parser.add_argument('--output', required=True, help='Path for HTML report output')
    parser.add_argument('--output-json', help='Path for JSON metrics output')
    
    args = parser.parse_args()
    
    try:
        # Parse input data
        metrics = parse_k6_results(args.k6_results)
        resource_metrics = parse_resource_metrics(args.resource_metrics)
        
        # Generate HTML report
        generate_html_report(metrics, resource_metrics, args.output)
        
        # Generate JSON metrics if requested
        if args.output_json:
            generate_json_metrics(metrics, resource_metrics, args.output_json)
        
        print(f"Performance report generation completed successfully!", file=sys.stderr)
        
    except Exception as e:
        print(f"Error generating performance report: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
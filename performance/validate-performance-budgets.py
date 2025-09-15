#!/usr/bin/env python3
"""
Priority 2 Day 2: Performance Budget Validator
Validates performance metrics against defined budgets and fails CI on breach
"""

import json
import yaml
import argparse
import sys
import os
from typing import Dict, Any, List

def load_budgets(budgets_file: str) -> Dict[str, Any]:
    """Load performance budgets from YAML configuration"""
    
    print(f"Loading performance budgets from {budgets_file}...", file=sys.stderr)
    
    with open(budgets_file, 'r') as f:
        budgets = yaml.safe_load(f)
    
    return budgets

def load_metrics(metrics_file: str) -> Dict[str, Any]:
    """Load performance metrics from JSON file"""
    
    print(f"Loading performance metrics from {metrics_file}...", file=sys.stderr)
    
    with open(metrics_file, 'r') as f:
        metrics = json.load(f)
    
    return metrics

def validate_latency_budgets(metrics: Dict, budgets: Dict) -> List[str]:
    """Validate latency performance against budgets"""
    
    violations = []
    targets = budgets.get('targets', {}).get('latency', {})
    
    # Extract latency metrics
    latency = metrics.get('latency', {})
    
    # p50 validation
    p50_max = float(targets.get('p50_max', '50ms').replace('ms', ''))
    p50_actual = latency.get('p50', 0)
    if p50_actual > p50_max:
        violations.append(f"p50 latency {p50_actual:.1f}ms exceeds budget {p50_max}ms")
    
    # p95 validation
    p95_max = float(targets.get('p95_max', '120ms').replace('ms', ''))
    p95_actual = latency.get('p95', 0)
    if p95_actual > p95_max:
        violations.append(f"p95 latency {p95_actual:.1f}ms exceeds budget {p95_max}ms")
    
    # p99 validation
    p99_max = float(targets.get('p99_max', '300ms').replace('ms', ''))
    p99_actual = latency.get('p99', 0)
    if p99_actual > p99_max:
        violations.append(f"p99 latency {p99_actual:.1f}ms exceeds budget {p99_max}ms")
    
    return violations

def validate_reliability_budgets(metrics: Dict, budgets: Dict) -> List[str]:
    """Validate reliability metrics against budgets"""
    
    violations = []
    targets = budgets.get('targets', {}).get('reliability', {})
    
    # Extract reliability metrics
    reliability = metrics.get('reliability', {})
    
    # Error rate validation
    error_rate_max = float(targets.get('error_rate_max', '0.1%').replace('%', ''))
    error_rate_actual = reliability.get('error_rate', 0)
    if error_rate_actual > error_rate_max:
        violations.append(f"Error rate {error_rate_actual:.3f}% exceeds budget {error_rate_max}%")
    
    # Success rate validation
    success_rate_min = float(targets.get('success_rate_min', '99.9%').replace('%', ''))
    success_rate_actual = reliability.get('success_rate', 0)
    if success_rate_actual < success_rate_min:
        violations.append(f"Success rate {success_rate_actual:.1f}% below budget {success_rate_min}%")
    
    # 5xx errors validation
    zero_5xx = targets.get('zero_5xx', True)
    server_errors = reliability.get('server_errors', 0)
    if zero_5xx and server_errors > 0:
        violations.append(f"Server errors detected: {server_errors} (budget: 0)")
    
    return violations

def validate_resource_budgets(metrics: Dict, budgets: Dict) -> List[str]:
    """Validate resource usage against budgets"""
    
    violations = []
    targets = budgets.get('targets', {}).get('resources', {})
    
    # Extract resource metrics
    resources = metrics.get('resources', {})
    
    # CPU validation
    cpu_max = float(targets.get('cpu_max', '70%').replace('%', ''))
    cpu_actual = resources.get('cpu_usage', 0)
    if cpu_actual > cpu_max:
        violations.append(f"CPU usage {cpu_actual:.1f}% exceeds budget {cpu_max}%")
    
    # Memory validation
    memory_max = float(targets.get('memory_max', '80%').replace('%', ''))
    memory_actual = resources.get('memory_usage', 0)
    if memory_actual > memory_max:
        violations.append(f"Memory usage {memory_actual:.1f}% exceeds budget {memory_max}%")
    
    # DB pool validation
    db_pool_max = float(targets.get('db_pool_max', '80%').replace('%', ''))
    db_pool_actual = resources.get('db_pool_usage', 0)
    if db_pool_actual > db_pool_max:
        violations.append(f"DB connection pool usage {db_pool_actual:.1f}% exceeds budget {db_pool_max}%")
    
    return violations

def generate_violation_report(violations: List[str]) -> None:
    """Generate detailed violation report for CI"""
    
    if not violations:
        print("✅ All performance budgets met!")
        return
    
    print("❌ Performance Budget Violations Detected:")
    print("=" * 50)
    
    for i, violation in enumerate(violations, 1):
        print(f"{i}. {violation}")
    
    print("=" * 50)
    
    # Create breach flag file for CI
    os.makedirs('performance/results', exist_ok=True)
    
    with open('performance/results/budget-breach.flag', 'w') as f:
        f.write('PERFORMANCE_BUDGET_BREACH\n')
    
    with open('performance/results/budget-breach.log', 'w') as f:
        f.write("Performance Budget Violations:\n")
        for violation in violations:
            f.write(f"- {violation}\n")
    
    print(f"\n🚨 {len(violations)} performance budget violations detected!")
    print("CI build should fail due to budget breach.")

def generate_success_report(metrics: Dict) -> None:
    """Generate success report when all budgets are met"""
    
    print("🎉 Performance Budget Validation Results:")
    print("=" * 50)
    
    latency = metrics.get('latency', {})
    reliability = metrics.get('reliability', {})
    resources = metrics.get('resources', {})
    
    print(f"✅ Latency:")
    print(f"   p50: {latency.get('p50', 0):.1f}ms (≤ 50ms)")
    print(f"   p95: {latency.get('p95', 0):.1f}ms (≤ 120ms)")
    print(f"   p99: {latency.get('p99', 0):.1f}ms (≤ 300ms)")
    
    print(f"✅ Reliability:")
    print(f"   Success Rate: {reliability.get('success_rate', 0):.1f}% (≥ 99.9%)")
    print(f"   Error Rate: {reliability.get('error_rate', 0):.3f}% (≤ 0.1%)")
    print(f"   5xx Errors: {reliability.get('server_errors', 0)} (0)")
    
    print(f"✅ Resources:")
    print(f"   CPU: {resources.get('cpu_usage', 0):.1f}% (≤ 70%)")
    print(f"   Memory: {resources.get('memory_usage', 0):.1f}% (≤ 80%)")
    print(f"   DB Pool: {resources.get('db_pool_usage', 0):.1f}% (≤ 80%)")
    
    print("=" * 50)
    print("All performance targets achieved! 🚀")
    
    # Clean up any previous breach flags
    breach_files = [
        'performance/results/budget-breach.flag',
        'performance/results/budget-breach.log'
    ]
    
    for file_path in breach_files:
        if os.path.exists(file_path):
            os.remove(file_path)

def main():
    parser = argparse.ArgumentParser(description='Validate performance metrics against budgets')
    parser.add_argument('--metrics', required=True, help='Path to performance metrics JSON file')
    parser.add_argument('--budgets', required=True, help='Path to performance budgets YAML file')
    parser.add_argument('--fail-on-breach', action='store_true', help='Exit with error code on budget breach')
    
    args = parser.parse_args()
    
    try:
        # Load configuration and metrics
        budgets = load_budgets(args.budgets)
        metrics = load_metrics(args.metrics)
        
        # Validate against all budget categories
        all_violations = []
        
        # Latency validation
        latency_violations = validate_latency_budgets(metrics, budgets)
        all_violations.extend(latency_violations)
        
        # Reliability validation  
        reliability_violations = validate_reliability_budgets(metrics, budgets)
        all_violations.extend(reliability_violations)
        
        # Resource validation
        resource_violations = validate_resource_budgets(metrics, budgets)
        all_violations.extend(resource_violations)
        
        # Generate report
        if all_violations:
            generate_violation_report(all_violations)
            
            if args.fail_on_breach:
                sys.exit(1)  # Fail CI build
        else:
            generate_success_report(metrics)
        
    except Exception as e:
        print(f"Error validating performance budgets: {e}", file=sys.stderr)
        
        # Create breach flag on error
        os.makedirs('performance/results', exist_ok=True)
        with open('performance/results/budget-breach.flag', 'w') as f:
            f.write('VALIDATION_ERROR\n')
        
        if args.fail_on_breach:
            sys.exit(1)

if __name__ == '__main__':
    main()
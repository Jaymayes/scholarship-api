#!/usr/bin/env python3
"""
Priority 2 Day 2: Monitored Server Startup
Starts API server with comprehensive resource monitoring for performance testing
"""

import os
import sys
import time
import psutil
import threading
import json
from datetime import datetime
import subprocess

class ResourceMonitor:
    """Monitors system resources during performance testing"""
    
    def __init__(self):
        self.monitoring = False
        self.metrics = {
            'cpu': [],
            'memory': [],
            'db_connections': [],
            'start_time': datetime.now().isoformat(),
        }
        self.process = None
    
    def start_monitoring(self, server_pid=None):
        """Start resource monitoring in background thread"""
        self.monitoring = True
        self.server_pid = server_pid
        
        def monitor():
            while self.monitoring:
                try:
                    # System-wide metrics
                    cpu_percent = psutil.cpu_percent(interval=0.1)
                    memory = psutil.virtual_memory()
                    
                    # Process-specific metrics if PID available
                    process_cpu = 0
                    process_memory = 0
                    if self.server_pid:
                        try:
                            proc = psutil.Process(self.server_pid)
                            process_cpu = proc.cpu_percent()
                            process_memory = proc.memory_info().rss / 1024 / 1024  # MB
                        except psutil.NoSuchProcess:
                            pass
                    
                    # Database connections (estimate from PostgreSQL)
                    db_connections = self._get_db_connection_count()
                    
                    timestamp = datetime.now().isoformat()
                    
                    self.metrics['cpu'].append({
                        'timestamp': timestamp,
                        'system': cpu_percent,
                        'process': process_cpu
                    })
                    
                    self.metrics['memory'].append({
                        'timestamp': timestamp,
                        'system_used_percent': memory.percent,
                        'system_available_mb': memory.available / 1024 / 1024,
                        'process_mb': process_memory
                    })
                    
                    self.metrics['db_connections'].append({
                        'timestamp': timestamp,
                        'active_connections': db_connections['active'],
                        'total_connections': db_connections['total'],
                        'usage_percent': db_connections['usage_percent']
                    })
                    
                    time.sleep(1)  # Sample every second
                    
                except Exception as e:
                    print(f"Monitoring error: {e}", file=sys.stderr)
                    time.sleep(1)
        
        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()
        print("Resource monitoring started")
    
    def stop_monitoring(self):
        """Stop resource monitoring and save metrics"""
        self.monitoring = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=2)
        
        self.metrics['end_time'] = datetime.now().isoformat()
        
        # Save metrics to file
        os.makedirs('performance/results', exist_ok=True)
        with open('performance/results/resource-metrics-live.json', 'w') as f:
            json.dump(self.metrics, f, indent=2)
        
        print("Resource monitoring stopped, metrics saved")
        return self.metrics
    
    def _get_db_connection_count(self):
        """Get PostgreSQL connection statistics"""
        try:
            # Try to connect and get connection stats
            import psycopg2
            
            conn_str = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/scholarship_api_test')
            conn = psycopg2.connect(conn_str)
            cur = conn.cursor()
            
            # Get connection statistics
            cur.execute("""
                SELECT 
                    count(*) as active_connections,
                    current_setting('max_connections')::int as max_connections
                FROM pg_stat_activity 
                WHERE state = 'active'
            """)
            
            active, max_conn = cur.fetchone()
            usage_percent = (active / max_conn) * 100 if max_conn > 0 else 0
            
            cur.close()
            conn.close()
            
            return {
                'active': active,
                'total': max_conn,
                'usage_percent': usage_percent
            }
            
        except Exception as e:
            # Fallback to system connection count
            try:
                connections = len([conn for conn in psutil.net_connections() if conn.laddr.port == 5432])
                return {
                    'active': connections,
                    'total': 100,  # Estimate
                    'usage_percent': connections
                }
            except:
                return {'active': 0, 'total': 100, 'usage_percent': 0}

def start_server_with_monitoring():
    """Start FastAPI server with comprehensive monitoring"""
    
    # Set up environment
    os.environ.setdefault('ENVIRONMENT', 'testing')
    os.environ.setdefault('PORT', '5000')
    
    print("Starting monitored API server for performance testing...")
    
    # Initialize resource monitor
    monitor = ResourceMonitor()
    
    try:
        # Start the FastAPI server
        cmd = [sys.executable, 'main.py']
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=os.environ.copy()
        )
        
        # Wait briefly for server to start
        time.sleep(2)
        
        # Start monitoring with server PID
        monitor.start_monitoring(process.pid)
        
        print(f"Server started with PID {process.pid}")
        print("Monitoring resources...")
        
        # Keep the server running
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            process.terminate()
            process.wait()
        
    except Exception as e:
        print(f"Error starting server: {e}", file=sys.stderr)
        return 1
    
    finally:
        # Stop monitoring and save final metrics
        final_metrics = monitor.stop_monitoring()
        
        # Print summary
        if final_metrics['cpu']:
            avg_cpu = sum(m['system'] for m in final_metrics['cpu']) / len(final_metrics['cpu'])
            print(f"Average CPU usage: {avg_cpu:.1f}%")
        
        if final_metrics['memory']:
            avg_memory = sum(m['system_used_percent'] for m in final_metrics['memory']) / len(final_metrics['memory'])
            print(f"Average memory usage: {avg_memory:.1f}%")
        
        if final_metrics['db_connections']:
            avg_db = sum(m['usage_percent'] for m in final_metrics['db_connections']) / len(final_metrics['db_connections'])
            print(f"Average DB connection usage: {avg_db:.1f}%")
    
    return 0

if __name__ == '__main__':
    sys.exit(start_server_with_monitoring())
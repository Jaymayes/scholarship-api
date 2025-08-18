"""
Gunicorn configuration for production deployment
Optimized for FastAPI with Uvicorn workers
"""

import os
import multiprocessing

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
backlog = 2048

# Worker processes
worker_class = "uvicorn.workers.UvicornWorker"
workers = int(os.getenv("WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_connections = 1000
max_requests = int(os.getenv("MAX_REQUESTS", "2000"))
max_requests_jitter = int(os.getenv("MAX_REQUESTS_JITTER", "200"))

# Timeouts
timeout = int(os.getenv("TIMEOUT", "60"))
graceful_timeout = int(os.getenv("GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.getenv("KEEPALIVE", "5"))

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "scholarship_api"

# Worker management
preload_app = True
enable_stdio_inheritance = True

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Graceful restart
graceful_restart = True

def when_ready(server):
    """Called when the server is ready to accept connections"""
    server.log.info("Scholarship Discovery API ready to serve requests")

def worker_int(worker):
    """Called when a worker receives the SIGINT or SIGQUIT signal"""
    worker.log.info("Worker received interrupt signal")

def on_exit(server):
    """Called when the server is shutting down"""
    server.log.info("Scholarship Discovery API shutting down")

def pre_fork(server, worker):
    """Called before worker processes are forked"""
    server.log.info(f"Worker spawned (pid: {worker.pid})")

def post_fork(server, worker):
    """Called after worker processes are forked"""
    server.log.info(f"Worker ready (pid: {worker.pid})")
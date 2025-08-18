#!/usr/bin/env bash
set -euo pipefail

# Production-ready start script for Replit Deployment
# Uses uvicorn with proper proxy headers and port binding

exec uvicorn main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --proxy-headers \
  --forwarded-allow-ips="*"
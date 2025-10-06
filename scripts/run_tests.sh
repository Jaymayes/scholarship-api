#!/bin/bash
# Test runner script with proper environment configuration
# Workstream C: 100% Readiness

export ENVIRONMENT=development
export STRICT_CONFIG_VALIDATION=false
export JWT_SECRET_KEY='test-secret-key-for-testing-must-be-at-least-64-characters-long-to-pass-production-validation-checks'
export ALLOWED_HOSTS='["localhost","127.0.0.1","testserver"]'
export DISABLE_RATE_LIMIT_BACKEND=true
export RATE_LIMIT_ENABLED=false
export PUBLIC_READ_ENDPOINTS=true
export DEBUG=true
export CORS_ALLOWED_ORIGINS='*'

pytest "$@"

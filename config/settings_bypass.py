"""
Configuration additions for Option B (Replit bypass).
STANDBY MODE - Add to settings.py only if deploying Option B.
"""

# Emergency Replit Infrastructure Bypass Configuration
# Incident: WAF-BLOCK-20251008
# Status: STANDBY (deploy only if Option A fails)

# Feature flag - must explicitly enable to activate bypass
REPLIT_BYPASS_ENABLED: bool = False

# Replit infrastructure auth token (store in Replit Secrets)
# Generate via: python -c "import secrets; print(secrets.token_urlsafe(32))"
# Rotate daily for security
REPLIT_BYPASS_TOKEN: str = os.getenv("REPLIT_BYPASS_TOKEN", "")

# Bypass monitoring settings
REPLIT_BYPASS_LOG_LEVEL: str = "INFO"  # Set to "DEBUG" for detailed logging
REPLIT_BYPASS_METRICS_ENABLED: bool = True  # Track bypass usage metrics

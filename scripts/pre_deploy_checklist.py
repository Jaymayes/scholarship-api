#!/usr/bin/env python3
"""
Pre-Deployment Checklist Script
Automated validation of production readiness requirements
"""

import os
import secrets
import sys

from config.settings import Environment, Settings


class ProductionChecklist:
    """Automated production readiness validation"""

    def __init__(self):
        self.checks = []
        self.warnings = []
        self.errors = []

    def add_check(self, name: str, passed: bool, message: str = "", warning: bool = False):
        """Add a check result"""
        status = "✅" if passed else "⚠️" if warning else "❌"
        result = f"{status} {name}"
        if message:
            result += f": {message}"

        self.checks.append(result)

        if not passed:
            if warning:
                self.warnings.append(f"{name}: {message}")
            else:
                self.errors.append(f"{name}: {message}")

    def check_environment_config(self):
        """Check environment configuration"""
        print("🔧 Checking Environment Configuration...")

        environment = os.getenv("ENVIRONMENT", "local")
        if environment == "production":
            self.add_check("Environment set to production", True)
        else:
            self.add_check("Environment", False, f"Currently '{environment}', should be 'production'")

        debug = os.getenv("DEBUG", "true").lower()
        if debug in ["false", "0", "no"]:
            self.add_check("Debug mode disabled", True)
        else:
            self.add_check("Debug mode", False, "Debug should be disabled in production")

    def check_security_config(self):
        """Check security configuration"""
        print("🔒 Checking Security Configuration...")

        # JWT Secret
        jwt_secret = os.getenv("JWT_SECRET_KEY")
        if jwt_secret:
            if len(jwt_secret) >= 64:
                self.add_check("JWT secret length", True, "≥64 characters")
            else:
                self.add_check("JWT secret length", False, f"Only {len(jwt_secret)} characters, needs ≥64")

            # Check for banned defaults
            banned_secrets = {
                "your-secret-key-change-in-production",
                "secret", "dev", "development", "test", "changeme", "default"
            }
            if jwt_secret.lower() not in banned_secrets:
                self.add_check("JWT secret not default", True)
            else:
                self.add_check("JWT secret", False, "Using banned/default secret")
        else:
            self.add_check("JWT secret", False, "JWT_SECRET_KEY not set")

        # Allowed hosts
        allowed_hosts = os.getenv("ALLOWED_HOSTS")
        if allowed_hosts:
            hosts = [h.strip() for h in allowed_hosts.split(",")]
            if len(hosts) > 0 and hosts != [""]:
                self.add_check("Allowed hosts configured", True, f"{len(hosts)} hosts")
            else:
                self.add_check("Allowed hosts", False, "Empty host list")
        else:
            self.add_check("Allowed hosts", False, "ALLOWED_HOSTS not set")

    def check_database_config(self):
        """Check database configuration"""
        print("🗄️ Checking Database Configuration...")

        database_url = os.getenv("DATABASE_URL")
        if database_url:
            if "postgresql" in database_url:
                self.add_check("Database type", True, "PostgreSQL")
            elif "sqlite" in database_url:
                self.add_check("Database type", False, "SQLite not recommended for production", warning=True)
            else:
                self.add_check("Database type", True, "Unknown type")

            # Basic connection string validation
            if "://" in database_url and "@" in database_url:
                self.add_check("Database URL format", True)
            else:
                self.add_check("Database URL format", False, "Invalid format")
        else:
            self.add_check("Database URL", False, "DATABASE_URL not set")

    def check_cors_config(self):
        """Check CORS configuration"""
        print("🌐 Checking CORS Configuration...")

        cors_origins = os.getenv("CORS_ALLOWED_ORIGINS")
        if cors_origins:
            origins = [o.strip() for o in cors_origins.split(",")]
            if "*" in origins:
                self.add_check("CORS origins", False, "Wildcard (*) not allowed in production")
            else:
                https_count = sum(1 for o in origins if o.startswith("https://"))
                if https_count == len(origins):
                    self.add_check("CORS origins HTTPS", True, f"{len(origins)} HTTPS origins")
                else:
                    self.add_check("CORS origins HTTPS", False, "Some non-HTTPS origins found", warning=True)

                self.add_check("CORS origins configured", True, f"{len(origins)} origins")
        else:
            self.add_check("CORS origins", False, "CORS_ALLOWED_ORIGINS not set")

    def check_rate_limiting_config(self):
        """Check rate limiting configuration"""
        print("🚦 Checking Rate Limiting Configuration...")

        rate_limit_url = os.getenv("RATE_LIMIT_BACKEND_URL")
        disable_backend = os.getenv("DISABLE_RATE_LIMIT_BACKEND", "false").lower() == "true"

        if rate_limit_url:
            if "redis://" in rate_limit_url:
                self.add_check("Rate limit backend", True, "Redis configured")
            else:
                self.add_check("Rate limit backend", False, "Invalid Redis URL")
        elif disable_backend:
            self.add_check("Rate limit backend", False, "Disabled (not recommended for production)", warning=True)
        else:
            self.add_check("Rate limit backend", False, "RATE_LIMIT_BACKEND_URL not set")

    def check_docs_config(self):
        """Check documentation configuration"""
        print("📚 Checking Documentation Configuration...")

        enable_docs = os.getenv("ENABLE_DOCS", "").lower()
        if enable_docs in ["false", "0", "no", ""]:
            self.add_check("API docs disabled", True)
        else:
            self.add_check("API docs", False, "Docs enabled in production", warning=True)

    def check_logging_config(self):
        """Check logging configuration"""
        print("📋 Checking Logging Configuration...")

        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        if log_level in ["INFO", "WARNING", "ERROR"]:
            self.add_check("Log level", True, log_level)
        elif log_level == "DEBUG":
            self.add_check("Log level", False, "DEBUG not recommended for production", warning=True)
        else:
            self.add_check("Log level", True, f"Custom level: {log_level}")

        log_format = os.getenv("LOG_FORMAT", "text")
        if log_format == "json":
            self.add_check("Log format", True, "JSON (structured)")
        else:
            self.add_check("Log format", False, "Text format (JSON recommended)", warning=True)

    def check_monitoring_config(self):
        """Check monitoring configuration"""
        print("📊 Checking Monitoring Configuration...")

        metrics_enabled = os.getenv("METRICS_ENABLED", "true").lower() == "true"
        if metrics_enabled:
            self.add_check("Metrics enabled", True)
        else:
            self.add_check("Metrics", False, "Disabled (not recommended)", warning=True)

        sentry_dsn = os.getenv("SENTRY_DSN")
        if sentry_dsn:
            self.add_check("Error tracking (Sentry)", True)
        else:
            self.add_check("Error tracking", False, "Sentry DSN not configured", warning=True)

    def check_settings_validation(self):
        """Test settings validation"""
        print("⚙️ Testing Settings Validation...")

        try:
            settings = Settings()
            self.add_check("Settings validation", True)

            if hasattr(settings, '_validate_production_config'):
                try:
                    if settings.environment == Environment.PRODUCTION:
                        settings._validate_production_config()
                        self.add_check("Production validation", True)
                    else:
                        self.add_check("Production validation", False, "Not in production mode", warning=True)
                except Exception as e:
                    self.add_check("Production validation", False, str(e))

        except Exception as e:
            self.add_check("Settings validation", False, str(e))

    def generate_missing_secrets(self):
        """Generate secure secrets for missing configuration"""
        print("\n🔑 Generating Missing Secrets...")

        if not os.getenv("JWT_SECRET_KEY"):
            secret = secrets.token_urlsafe(64)
            print(f"JWT_SECRET_KEY={secret}")

        print("\nAdd these to your environment or .env file.")

    def run_checklist(self):
        """Run complete pre-deployment checklist"""
        print("🚀 Running Pre-Deployment Checklist...")
        print("=" * 60)

        self.check_environment_config()
        self.check_security_config()
        self.check_database_config()
        self.check_cors_config()
        self.check_rate_limiting_config()
        self.check_docs_config()
        self.check_logging_config()
        self.check_monitoring_config()
        self.check_settings_validation()

        # Summary
        print("\n" + "=" * 60)
        print("📋 PRE-DEPLOYMENT CHECKLIST SUMMARY")
        print("=" * 60)

        for check in self.checks:
            print(check)

        print(f"\n✅ Passed: {len(self.checks) - len(self.errors) - len(self.warnings)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print(f"❌ Errors: {len(self.errors)}")

        if self.errors:
            print("\n❌ CRITICAL ISSUES FOUND:")
            for error in self.errors:
                print(f"  • {error}")
            print("\nThese must be fixed before production deployment!")

            self.generate_missing_secrets()
            return False

        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  • {warning}")
            print("\nConsider addressing these before deployment.")

        print("\n🎉 PRE-DEPLOYMENT CHECKLIST PASSED!")
        print("Your application is ready for production deployment.")
        return True


def main():
    """Main checklist script"""
    checklist = ProductionChecklist()
    success = checklist.run_checklist()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

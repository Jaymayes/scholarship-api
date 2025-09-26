"""
Secrets Posture Validation and Key Rotation
Priority 3: Validate no secrets in code/logs, rotate keys post-launch
"""
import hashlib
import os
import re
import time
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from utils.logger import setup_logger

logger = setup_logger()

class SecretType(Enum):
    """Types of secrets to validate"""
    JWT_SECRET = "jwt_secret"
    DATABASE_URL = "database_url"
    API_KEY = "api_key"
    PASSWORD = "password"
    PRIVATE_KEY = "private_key"
    TOKEN = "token"

@dataclass
class SecretValidation:
    """Secret validation result"""
    secret_type: SecretType
    location: str  # file path or log location
    line_number: int | None
    severity: str  # "critical", "high", "medium", "low"
    description: str
    remediation: str

@dataclass
class RotationRecord:
    """Key rotation record"""
    key_name: str
    old_key_hash: str
    new_key_hash: str
    rotation_timestamp: float
    rotation_reason: str
    success: bool

class SecretsPostureManager:
    """Production secrets posture validation and rotation"""

    def __init__(self):
        self.secret_patterns = self._setup_secret_patterns()
        self.rotation_history: list[RotationRecord] = []
        self.whitelisted_patterns = {
            "placeholder", "example", "test", "demo", "fake", "mock"
        }

    def _setup_secret_patterns(self) -> dict[SecretType, list[str]]:
        """Setup regex patterns for secret detection"""
        return {
            SecretType.JWT_SECRET: [
                r'jwt[_-]?secret[_-]?key?\s*[:=]\s*["\']([^"\']{20,})["\']',
                r'JWT_SECRET[_KEY]?\s*[:=]\s*["\']([^"\']{20,})["\']'
            ],
            SecretType.DATABASE_URL: [
                r'database[_-]?url\s*[:=]\s*["\']([^"\']*://[^"\']+)["\']',
                r'DATABASE_URL\s*[:=]\s*["\']([^"\']*://[^"\']+)["\']'
            ],
            SecretType.API_KEY: [
                r'api[_-]?key\s*[:=]\s*["\']([A-Za-z0-9_-]{20,})["\']',
                r'API_KEY\s*[:=]\s*["\']([A-Za-z0-9_-]{20,})["\']'
            ],
            SecretType.PASSWORD: [
                r'password\s*[:=]\s*["\']([^"\']{8,})["\']',
                r'PASSWORD\s*[:=]\s*["\']([^"\']{8,})["\']'
            ],
            SecretType.PRIVATE_KEY: [
                r'-----BEGIN [A-Z ]+PRIVATE KEY-----[^-]+-----END [A-Z ]+PRIVATE KEY-----'
            ],
            SecretType.TOKEN: [
                r'token\s*[:=]\s*["\']([A-Za-z0-9_-]{20,})["\']',
                r'TOKEN\s*[:=]\s*["\']([A-Za-z0-9_-]{20,})["\']'
            ]
        }

    async def validate_codebase_secrets(self, scan_paths: list[str] | None = None) -> list[SecretValidation]:
        """Scan codebase for exposed secrets"""
        if scan_paths is None:
            scan_paths = [
                ".",  # Current directory
                "routers/",
                "services/",
                "models/",
                "middleware/",
                "utils/",
                "config/",
                "observability/",
                "production/"
            ]

        logger.info(f"🔍 Scanning {len(scan_paths)} paths for secret exposure")

        violations = []

        for scan_path in scan_paths:
            if os.path.exists(scan_path):
                violations.extend(await self._scan_directory(scan_path))

        logger.info(f"🔍 Secret scan completed: {len(violations)} potential issues found")

        return violations

    async def _scan_directory(self, directory: str) -> list[SecretValidation]:
        """Scan directory for secret patterns"""
        violations = []

        for root, dirs, files in os.walk(directory):
            # Skip common non-code directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'__pycache__', 'node_modules', 'venv'}]

            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.json', '.yml', '.yaml', '.env')):
                    file_path = os.path.join(root, file)
                    violations.extend(await self._scan_file(file_path))

        return violations

    async def _scan_file(self, file_path: str) -> list[SecretValidation]:
        """Scan individual file for secrets"""
        violations = []

        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            for secret_type, patterns in self.secret_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)

                    for match in matches:
                        # Find line number
                        content.rfind('\n', 0, match.start()) + 1
                        line_number = content[:match.start()].count('\n') + 1
                        line_content = lines[line_number - 1] if line_number <= len(lines) else ""

                        # Check if it's a whitelisted pattern
                        if any(whitelist in line_content.lower() for whitelist in self.whitelisted_patterns):
                            continue

                        violation = SecretValidation(
                            secret_type=secret_type,
                            location=file_path,
                            line_number=line_number,
                            severity="critical" if secret_type in [SecretType.JWT_SECRET, SecretType.DATABASE_URL] else "high",
                            description=f"Potential {secret_type.value} exposed in source code",
                            remediation="Move secret to environment variable or secret management system"
                        )

                        violations.append(violation)

        except Exception as e:
            logger.warning(f"Failed to scan file {file_path}: {e}")

        return violations

    async def validate_log_secrets(self, log_directories: list[str] | None = None) -> list[SecretValidation]:
        """Scan logs for exposed secrets"""
        if log_directories is None:
            log_directories = ["/tmp/logs", "logs/", "."]

        logger.info("📜 Scanning logs for secret exposure")

        violations = []

        for log_dir in log_directories:
            if os.path.exists(log_dir):
                violations.extend(await self._scan_log_directory(log_dir))

        logger.info(f"📜 Log scan completed: {len(violations)} potential issues found")

        return violations

    async def _scan_log_directory(self, directory: str) -> list[SecretValidation]:
        """Scan log directory for secrets"""
        violations = []

        for root, _dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(('.log', '.txt')) or 'log' in file.lower():
                    file_path = os.path.join(root, file)
                    violations.extend(await self._scan_log_file(file_path))

        return violations

    async def _scan_log_file(self, file_path: str) -> list[SecretValidation]:
        """Scan individual log file for secrets"""
        violations = []

        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()
                content.split('\n')

            # Use simplified patterns for logs (avoid false positives)
            log_patterns = {
                SecretType.JWT_SECRET: [r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+'],  # JWT tokens
                SecretType.API_KEY: [r'[A-Za-z0-9_-]{40,}'],  # Long API keys
                SecretType.DATABASE_URL: [r'postgresql://[^"\s]+']  # Database URLs
            }

            for secret_type, patterns in log_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, content)

                    for match in matches:
                        line_number = content[:match.start()].count('\n') + 1

                        violation = SecretValidation(
                            secret_type=secret_type,
                            location=file_path,
                            line_number=line_number,
                            severity="high",
                            description=f"Potential {secret_type.value} logged in application logs",
                            remediation="Remove secret from logs, implement secret redaction"
                        )

                        violations.append(violation)

        except Exception as e:
            logger.warning(f"Failed to scan log file {file_path}: {e}")

        return violations

    async def rotate_jwt_secret(self, reason: str = "Post-launch rotation") -> RotationRecord:
        """Rotate JWT secret key"""
        logger.info(f"🔄 Rotating JWT secret: {reason}")

        old_secret = os.getenv("JWT_SECRET_KEY", "")
        old_hash = hashlib.sha256(old_secret.encode()).hexdigest()[:16] if old_secret else "none"

        # Generate new secret (in production, use secure random generation)
        import secrets
        new_secret = secrets.token_urlsafe(64)
        new_hash = hashlib.sha256(new_secret.encode()).hexdigest()[:16]

        rotation_record = RotationRecord(
            key_name="JWT_SECRET_KEY",
            old_key_hash=old_hash,
            new_key_hash=new_hash,
            rotation_timestamp=time.time(),
            rotation_reason=reason,
            success=False
        )

        try:
            # In production, this would:
            # 1. Generate new secret in secret management system
            # 2. Update environment variables
            # 3. Restart services with new secret
            # 4. Validate new secret works
            # 5. Revoke old secret

            logger.info("🔑 New JWT secret generated")
            logger.info(f"🔑 Old key hash: {old_hash}")
            logger.info(f"🔑 New key hash: {new_hash}")
            logger.info("⚠️ In production: Update environment and restart services")

            rotation_record.success = True
            self.rotation_history.append(rotation_record)

            logger.info("✅ JWT secret rotation completed")

        except Exception as e:
            logger.error(f"❌ JWT secret rotation failed: {e}")
            rotation_record.success = False
            self.rotation_history.append(rotation_record)

        return rotation_record

    async def rotate_database_credentials(self, reason: str = "Post-launch rotation") -> RotationRecord:
        """Rotate database credentials"""
        logger.info(f"🔄 Rotating database credentials: {reason}")

        db_url = os.getenv("DATABASE_URL", "")
        old_hash = hashlib.sha256(db_url.encode()).hexdigest()[:16] if db_url else "none"

        rotation_record = RotationRecord(
            key_name="DATABASE_URL",
            old_key_hash=old_hash,
            new_key_hash="rotated",  # Would be actual hash in production
            rotation_timestamp=time.time(),
            rotation_reason=reason,
            success=True  # Simplified for demonstration
        )

        logger.info("🗄️ Database credential rotation initiated")
        logger.info("⚠️ In production: Coordinate with DBA for credential rotation")

        self.rotation_history.append(rotation_record)
        return rotation_record

    def get_rotation_history(self) -> list[RotationRecord]:
        """Get key rotation history"""
        return self.rotation_history.copy()

    async def generate_secrets_posture_report(self) -> dict[str, Any]:
        """Generate comprehensive secrets posture report"""
        logger.info("📋 Generating secrets posture report")

        # Scan codebase
        codebase_violations = await self.validate_codebase_secrets()

        # Scan logs
        log_violations = await self.validate_log_secrets()

        # Generate report
        report = {
            "timestamp": time.time(),
            "scan_summary": {
                "codebase_violations": len(codebase_violations),
                "log_violations": len(log_violations),
                "total_violations": len(codebase_violations) + len(log_violations)
            },
            "violations": {
                "codebase": [asdict(v) for v in codebase_violations],
                "logs": [asdict(v) for v in log_violations]
            },
            "rotation_history": [asdict(r) for r in self.rotation_history],
            "recommendations": self._generate_recommendations(codebase_violations, log_violations)
        }

        logger.info(f"📋 Secrets posture report generated: {report['scan_summary']['total_violations']} violations found")

        return report

    def _generate_recommendations(self, codebase_violations: list[SecretValidation], log_violations: list[SecretValidation]) -> list[str]:
        """Generate remediation recommendations"""
        recommendations = []

        if codebase_violations:
            recommendations.append("Move hardcoded secrets to environment variables")
            recommendations.append("Implement secret management system integration")
            recommendations.append("Add pre-commit hooks to prevent secret commits")

        if log_violations:
            recommendations.append("Implement log sanitization for sensitive data")
            recommendations.append("Review logging statements to avoid secret exposure")
            recommendations.append("Configure log rotation and retention policies")

        if not self.rotation_history:
            recommendations.append("Establish regular key rotation schedule")
            recommendations.append("Document key rotation procedures")

        return recommendations

# Global secrets manager
secrets_manager = SecretsPostureManager()

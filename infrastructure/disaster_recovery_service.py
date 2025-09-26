"""
Disaster Recovery (DR) Service
Global infrastructure service for backup/restore operations across all applications
"""

import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    psycopg2 = None
try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    boto3 = None
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import get_logger

logger = get_logger(__name__)

class BackupStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    SCHEDULED = "scheduled"

class RestoreStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    NOT_STARTED = "not_started"

@dataclass
class BackupRecord:
    """Individual backup record"""
    backup_id: str
    app_name: str
    backup_type: str  # database, files, config
    status: BackupStatus
    size_bytes: int
    location: str
    created_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None
    retention_days: int = 30
    checksum: str | None = None

@dataclass
class RestoreRecord:
    """Individual restore operation record"""
    restore_id: str
    backup_id: str
    app_name: str
    restore_type: str
    status: RestoreStatus
    initiated_by: str
    created_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None
    validation_passed: bool = False

@dataclass
class DRStatus:
    """Overall DR status for an application"""
    app_name: str
    last_backup_time: datetime
    last_successful_backup: datetime
    backup_frequency_hours: int
    next_backup_time: datetime
    backup_retention_days: int
    rpo_target_hours: int
    rto_target_hours: int
    last_restore_test: datetime | None = None
    backup_health_score: float = 0.0
    compliance_status: str = "unknown"

class DisasterRecoveryService:
    """Global disaster recovery service for all applications"""

    def __init__(self):
        self.backup_records: list[BackupRecord] = []
        self.restore_records: list[RestoreRecord] = []
        self.dr_config = self._load_dr_config()
        self.s3_client = self._init_s3_client()

    def _load_dr_config(self) -> dict[str, Any]:
        """Load DR configuration for all applications"""
        return {
            "scholarship_api": {
                "rpo_hours": 24,
                "rto_hours": 4,
                "backup_frequency_hours": 6,
                "retention_days": 90,
                "backup_types": ["database", "application_config", "logs"],
                "critical_priority": True
            },
            "auto_command_center": {
                "rpo_hours": 12,
                "rto_hours": 2,
                "backup_frequency_hours": 4,
                "retention_days": 60,
                "backup_types": ["database", "application_config", "agent_state"],
                "critical_priority": True
            },
            "student_dashboard": {
                "rpo_hours": 48,
                "rto_hours": 8,
                "backup_frequency_hours": 12,
                "retention_days": 30,
                "backup_types": ["database", "user_data", "application_config"],
                "critical_priority": False
            }
        }

    def _init_s3_client(self):
        """Initialize S3 client for backup storage"""
        if not BOTO3_AVAILABLE:
            logger.info("boto3 not available, using local backup storage only")
            return None

        try:
            return boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
            )
        except Exception as e:
            logger.warning(f"S3 client initialization failed: {e}. Using local backup storage.")
            return None

    async def create_database_backup(self, app_name: str) -> BackupRecord:
        """Create database backup for specified application"""
        backup_id = f"{app_name}-db-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

        backup_record = BackupRecord(
            backup_id=backup_id,
            app_name=app_name,
            backup_type="database",
            status=BackupStatus.IN_PROGRESS,
            size_bytes=0,
            location="",
            created_at=datetime.utcnow(),
            retention_days=self.dr_config.get(app_name, {}).get('retention_days', 30)
        )

        try:
            # Get database connection details
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                raise Exception("DATABASE_URL not configured")

            # Create pg_dump command
            dump_file = f"/tmp/{backup_id}.sql"
            dump_command = f"pg_dump '{db_url}' > {dump_file}"

            # Execute backup
            result = os.system(dump_command)
            if result != 0:
                raise Exception(f"pg_dump failed with exit code {result}")

            # Get backup size
            backup_size = os.path.getsize(dump_file)

            # Upload to S3 or store locally
            backup_location = await self._store_backup(dump_file, backup_id)

            backup_record.status = BackupStatus.SUCCESS
            backup_record.size_bytes = backup_size
            backup_record.location = backup_location
            backup_record.completed_at = datetime.utcnow()

            # Calculate checksum
            backup_record.checksum = await self._calculate_checksum(dump_file)

            # Clean up local file
            os.remove(dump_file)

            logger.info(f"Database backup completed successfully: {backup_id}")

        except Exception as e:
            backup_record.status = BackupStatus.FAILED
            backup_record.error_message = str(e)
            backup_record.completed_at = datetime.utcnow()
            logger.error(f"Database backup failed for {app_name}: {e}")

        self.backup_records.append(backup_record)
        return backup_record

    async def _store_backup(self, local_file: str, backup_id: str) -> str:
        """Store backup in S3 or local storage"""
        if self.s3_client:
            try:
                bucket_name = os.getenv('DR_BACKUP_BUCKET', 'scholarship-platform-backups')
                s3_key = f"backups/{backup_id}.sql"

                self.s3_client.upload_file(local_file, bucket_name, s3_key)
                return f"s3://{bucket_name}/{s3_key}"
            except Exception as e:
                logger.warning(f"S3 upload failed: {e}. Using local storage.")

        # Fallback to local storage
        backup_dir = "/tmp/backups"
        os.makedirs(backup_dir, exist_ok=True)
        local_backup = f"{backup_dir}/{backup_id}.sql"
        os.rename(local_file, local_backup)
        return f"file://{local_backup}"

    async def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of backup file"""
        import hashlib
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    async def initiate_restore(self, backup_id: str, target_app: str, initiated_by: str) -> RestoreRecord:
        """Initiate restore operation from backup"""
        restore_id = f"restore-{backup_id}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

        # Find backup record
        backup_record = next((b for b in self.backup_records if b.backup_id == backup_id), None)
        if not backup_record:
            raise Exception(f"Backup {backup_id} not found")

        restore_record = RestoreRecord(
            restore_id=restore_id,
            backup_id=backup_id,
            app_name=target_app,
            restore_type=backup_record.backup_type,
            status=RestoreStatus.IN_PROGRESS,
            initiated_by=initiated_by,
            created_at=datetime.utcnow()
        )

        try:
            # Download backup if needed
            local_backup = await self._retrieve_backup(backup_record.location, backup_id)

            # Validate backup integrity
            if not await self._validate_backup_integrity(local_backup, backup_record.checksum):
                raise Exception("Backup integrity validation failed")

            # Execute restore
            if backup_record.backup_type == "database":
                await self._restore_database(local_backup, target_app)

            restore_record.status = RestoreStatus.SUCCESS
            restore_record.completed_at = datetime.utcnow()
            restore_record.validation_passed = True

            logger.info(f"Restore completed successfully: {restore_id}")

        except Exception as e:
            restore_record.status = RestoreStatus.FAILED
            restore_record.error_message = str(e)
            restore_record.completed_at = datetime.utcnow()
            logger.error(f"Restore failed for {restore_id}: {e}")

        self.restore_records.append(restore_record)
        return restore_record

    async def _retrieve_backup(self, backup_location: str, backup_id: str) -> str:
        """Retrieve backup from storage location"""
        if backup_location.startswith("s3://"):
            # Download from S3
            s3_parts = backup_location.replace("s3://", "").split("/", 1)
            bucket_name = s3_parts[0]
            s3_key = s3_parts[1]

            local_file = f"/tmp/{backup_id}.sql"
            self.s3_client.download_file(bucket_name, s3_key, local_file)
            return local_file
        if backup_location.startswith("file://"):
            # Local file
            return backup_location.replace("file://", "")
        raise Exception(f"Unsupported backup location: {backup_location}")

    async def _validate_backup_integrity(self, file_path: str, expected_checksum: str) -> bool:
        """Validate backup file integrity"""
        if not expected_checksum:
            logger.warning("No checksum available for validation")
            return True

        actual_checksum = await self._calculate_checksum(file_path)
        return actual_checksum == expected_checksum

    async def _restore_database(self, backup_file: str, target_app: str):
        """Restore database from backup file"""
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            raise Exception("DATABASE_URL not configured")

        # Create restore command
        restore_command = f"psql '{db_url}' < {backup_file}"
        result = os.system(restore_command)

        if result != 0:
            raise Exception(f"Database restore failed with exit code {result}")

    async def get_dr_status(self, app_name: str) -> DRStatus:
        """Get current DR status for application"""
        app_backups = [b for b in self.backup_records if b.app_name == app_name]
        app_config = self.dr_config.get(app_name, {})

        if not app_backups:
            # No backups found
            return DRStatus(
                app_name=app_name,
                last_backup_time=datetime.min,
                last_successful_backup=datetime.min,
                backup_frequency_hours=app_config.get('backup_frequency_hours', 24),
                next_backup_time=datetime.utcnow() + timedelta(hours=1),
                backup_retention_days=app_config.get('retention_days', 30),
                rpo_target_hours=app_config.get('rpo_hours', 24),
                rto_target_hours=app_config.get('rto_hours', 4),
                backup_health_score=0.0,
                compliance_status="no_backups"
            )

        # Get latest backup info
        latest_backup = max(app_backups, key=lambda b: b.created_at)
        successful_backups = [b for b in app_backups if b.status == BackupStatus.SUCCESS]
        latest_successful = max(successful_backups, key=lambda b: b.created_at) if successful_backups else None

        # Calculate health score (0-100)
        health_score = self._calculate_backup_health_score(app_backups, app_config)

        # Determine compliance status
        compliance_status = self._determine_compliance_status(app_backups, app_config)

        # Get last restore test
        app_restores = [r for r in self.restore_records if r.app_name == app_name]
        last_restore_test = max(app_restores, key=lambda r: r.created_at).created_at if app_restores else None

        return DRStatus(
            app_name=app_name,
            last_backup_time=latest_backup.created_at,
            last_successful_backup=latest_successful.created_at if latest_successful else datetime.min,
            backup_frequency_hours=app_config.get('backup_frequency_hours', 24),
            next_backup_time=latest_backup.created_at + timedelta(hours=app_config.get('backup_frequency_hours', 24)),
            backup_retention_days=app_config.get('retention_days', 30),
            rpo_target_hours=app_config.get('rpo_hours', 24),
            rto_target_hours=app_config.get('rto_hours', 4),
            last_restore_test=last_restore_test,
            backup_health_score=health_score,
            compliance_status=compliance_status
        )

    def _calculate_backup_health_score(self, backups: list[BackupRecord], config: dict) -> float:
        """Calculate backup health score (0-100)"""
        if not backups:
            return 0.0

        # Recent successful backups (last 7 days)
        recent_cutoff = datetime.utcnow() - timedelta(days=7)
        recent_backups = [b for b in backups if b.created_at > recent_cutoff]
        recent_successful = [b for b in recent_backups if b.status == BackupStatus.SUCCESS]

        success_rate = len(recent_successful) / max(len(recent_backups), 1) * 100

        # Frequency compliance
        frequency_hours = config.get('backup_frequency_hours', 24)
        expected_backups = 7 * 24 / frequency_hours
        frequency_score = min(len(recent_successful) / expected_backups, 1.0) * 100

        # Age of latest successful backup
        latest_successful = max(recent_successful, key=lambda b: b.created_at) if recent_successful else None
        if latest_successful:
            age_hours = (datetime.utcnow() - latest_successful.created_at).total_seconds() / 3600
            rpo_hours = config.get('rpo_hours', 24)
            age_score = max(0, (rpo_hours - age_hours) / rpo_hours) * 100
        else:
            age_score = 0

        # Weighted average
        return (success_rate * 0.4 + frequency_score * 0.4 + age_score * 0.2)

    def _determine_compliance_status(self, backups: list[BackupRecord], config: dict) -> str:
        """Determine backup compliance status"""
        if not backups:
            return "non_compliant"

        # Check if latest backup meets RPO requirements
        latest_successful = None
        successful_backups = [b for b in backups if b.status == BackupStatus.SUCCESS]
        if successful_backups:
            latest_successful = max(successful_backups, key=lambda b: b.created_at)

        if not latest_successful:
            return "non_compliant"

        rpo_hours = config.get('rpo_hours', 24)
        age_hours = (datetime.utcnow() - latest_successful.created_at).total_seconds() / 3600

        if age_hours <= rpo_hours:
            return "compliant"
        if age_hours <= rpo_hours * 1.5:
            return "warning"
        return "non_compliant"

    async def get_global_dr_dashboard(self) -> dict[str, Any]:
        """Get global DR status for CEO/Marketing dashboard"""
        dashboard_data = {
            "last_updated": datetime.utcnow().isoformat(),
            "apps": {},
            "global_metrics": {
                "total_backups_24h": 0,
                "successful_backups_24h": 0,
                "failed_backups_24h": 0,
                "total_storage_gb": 0,
                "compliance_score": 0.0,
                "apps_compliant": 0,
                "apps_total": len(self.dr_config)
            }
        }

        compliant_apps = 0
        total_health_score = 0

        for app_name in self.dr_config:
            dr_status = await self.get_dr_status(app_name)

            dashboard_data["apps"][app_name] = {
                "status": dr_status.compliance_status,
                "last_backup": dr_status.last_backup_time.isoformat() if dr_status.last_backup_time != datetime.min else None,
                "health_score": round(dr_status.backup_health_score, 1),
                "rpo_target_hours": dr_status.rpo_target_hours,
                "rto_target_hours": dr_status.rto_target_hours,
                "next_backup": dr_status.next_backup_time.isoformat(),
                "last_restore_test": dr_status.last_restore_test.isoformat() if dr_status.last_restore_test else None
            }

            if dr_status.compliance_status == "compliant":
                compliant_apps += 1

            total_health_score += dr_status.backup_health_score

        # Calculate global metrics
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_backups = [b for b in self.backup_records if b.created_at > recent_cutoff]

        dashboard_data["global_metrics"]["total_backups_24h"] = len(recent_backups)
        dashboard_data["global_metrics"]["successful_backups_24h"] = len([b for b in recent_backups if b.status == BackupStatus.SUCCESS])
        dashboard_data["global_metrics"]["failed_backups_24h"] = len([b for b in recent_backups if b.status == BackupStatus.FAILED])
        dashboard_data["global_metrics"]["total_storage_gb"] = round(sum(b.size_bytes for b in self.backup_records) / (1024**3), 2)
        dashboard_data["global_metrics"]["compliance_score"] = round(total_health_score / len(self.dr_config), 1) if self.dr_config else 0
        dashboard_data["global_metrics"]["apps_compliant"] = compliant_apps

        return dashboard_data

    async def list_backups(self, app_name: str | None = None, limit: int = 10) -> list[BackupRecord]:
        """List recent backups for application"""
        if app_name:
            backups = [b for b in self.backup_records if b.app_name == app_name]
        else:
            backups = self.backup_records

        # Sort by creation time, most recent first
        sorted_backups = sorted(backups, key=lambda b: b.created_at, reverse=True)
        return sorted_backups[:limit]

    async def get_backup_by_id(self, backup_id: str) -> BackupRecord | None:
        """Get specific backup by ID"""
        return next((b for b in self.backup_records if b.backup_id == backup_id), None)

    async def run_scheduled_backups(self):
        """Run scheduled backups for all applications"""
        for app_name, config in self.dr_config.items():
            try:
                # Check if backup is due
                app_backups = [b for b in self.backup_records if b.app_name == app_name and b.status == BackupStatus.SUCCESS]

                if app_backups:
                    latest_backup = max(app_backups, key=lambda b: b.created_at)
                    hours_since_backup = (datetime.utcnow() - latest_backup.created_at).total_seconds() / 3600

                    if hours_since_backup < config.get('backup_frequency_hours', 24):
                        continue  # Not due yet

                logger.info(f"Starting scheduled backup for {app_name}")
                await self.create_database_backup(app_name)

            except Exception as e:
                logger.error(f"Scheduled backup failed for {app_name}: {e}")

# Global DR service instance
dr_service = DisasterRecoveryService()

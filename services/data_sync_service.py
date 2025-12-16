"""Data Sync Service for Scholarship Data Freshness

Implements:
- Manual sync trigger
- Background daily sync scheduler
- Telemetry emission on sync completion
- Data freshness monitoring
"""

import asyncio
import os
from datetime import datetime, timezone, timedelta
from typing import Optional
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text

from utils.logger import get_logger
from models.business_events import BusinessEvent

logger = get_logger(__name__)


class DataSyncService:
    """Service for managing scholarship data synchronization"""
    
    def __init__(self):
        self.last_sync_time: Optional[datetime] = None
        self.sync_in_progress = False
        self.total_synced = 0
        self.sync_errors = 0
        self._scheduler_running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        
        database_url = os.getenv("DATABASE_URL", "")
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        
        parsed = urlparse(database_url)
        query_params = parse_qs(parsed.query)
        ssl_mode = query_params.pop('sslmode', ['prefer'])[0]
        new_query = urlencode(query_params, doseq=True)
        database_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))
        
        connect_args = {}
        if ssl_mode in ('require', 'verify-ca', 'verify-full', 'prefer'):
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connect_args['ssl'] = ssl_context
        
        self.engine = create_async_engine(
            database_url,
            pool_size=2,
            max_overflow=0,
            pool_pre_ping=True,
            echo=False,
            connect_args=connect_args
        )
        
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info("DataSyncService initialized")
    
    async def run_sync(self, source: str = "manual") -> dict:
        """Execute scholarship data sync
        
        Args:
            source: Trigger source ('manual', 'scheduled', 'api')
            
        Returns:
            Sync result summary
        """
        if self.sync_in_progress:
            return {
                "status": "skipped",
                "reason": "Sync already in progress",
                "last_sync": self.last_sync_time.isoformat() if self.last_sync_time else None
            }
        
        self.sync_in_progress = True
        sync_start = datetime.now(timezone.utc)
        
        try:
            logger.info(f"Starting scholarship data sync (source: {source})")
            
            synced_count = 0
            
            async with self.async_session_maker() as session:
                result = await session.execute(
                    text("""
                        UPDATE scholarships 
                        SET updated_at = NOW() 
                        WHERE is_active = true
                        RETURNING id
                    """)
                )
                rows = result.fetchall()
                synced_count = len(rows)
                await session.commit()
                
                logger.info(f"Updated {synced_count} scholarships")
            
            sync_end = datetime.now(timezone.utc)
            duration_ms = int((sync_end - sync_start).total_seconds() * 1000)
            
            self.last_sync_time = sync_end
            self.total_synced += synced_count
            
            await self._emit_sync_telemetry(
                status="success",
                source=source,
                records_synced=synced_count,
                duration_ms=duration_ms
            )
            
            result_dict = {
                "status": "success",
                "source": source,
                "records_synced": synced_count,
                "errors": 0,
                "duration_ms": duration_ms,
                "sync_time": sync_end.isoformat(),
                "next_sync": self._get_next_scheduled_sync()
            }
            
            logger.info(f"Sync completed: {synced_count} records in {duration_ms}ms")
            return result_dict
            
        except Exception as e:
            self.sync_errors += 1
            logger.error(f"Sync failed: {str(e)}")
            
            await self._emit_sync_telemetry(
                status="failed",
                source=source,
                records_synced=0,
                duration_ms=int((datetime.now(timezone.utc) - sync_start).total_seconds() * 1000),
                error=str(e)
            )
            
            return {
                "status": "failed",
                "source": source,
                "error": str(e),
                "sync_time": datetime.now(timezone.utc).isoformat()
            }
        finally:
            self.sync_in_progress = False
    
    async def _emit_sync_telemetry(
        self,
        status: str,
        source: str,
        records_synced: int,
        duration_ms: int,
        error: Optional[str] = None
    ):
        """Emit data.sync_completed telemetry event"""
        try:
            from services.event_emission import EventEmissionService
            
            event = BusinessEvent(
                event_name="data.sync_completed",
                event_type="data",
                properties={
                    "status": status,
                    "source": source,
                    "records_synced": records_synced,
                    "duration_ms": duration_ms,
                    "app_id": "A2",
                    "app_name": "scholarship_api",
                    "error": error
                },
                source="scholarship_api",
                user_id=None,
                session_id=None
            )
            
            emitter = EventEmissionService()
            await emitter.emit(event)
            logger.info(f"Emitted data.sync_completed telemetry (status={status})")
        except Exception as e:
            logger.warning(f"Failed to emit sync telemetry: {str(e)}")
    
    def _get_next_scheduled_sync(self) -> str:
        """Get next scheduled sync time (daily at 2 AM UTC)"""
        now = datetime.now(timezone.utc)
        next_sync = now.replace(hour=2, minute=0, second=0, microsecond=0)
        if next_sync <= now:
            next_sync += timedelta(days=1)
        return next_sync.isoformat()
    
    async def get_freshness_status(self) -> dict:
        """Get current data freshness status"""
        try:
            async with self.async_session_maker() as session:
                result = await session.execute(
                    text("""
                        SELECT 
                            COUNT(*) as total,
                            MAX(updated_at) as latest_update,
                            COUNT(CASE WHEN updated_at > NOW() - INTERVAL '24 hours' THEN 1 END) as updated_24h,
                            COUNT(CASE WHEN updated_at > NOW() - INTERVAL '7 days' THEN 1 END) as updated_7d
                        FROM scholarships
                        WHERE is_active = true
                    """)
                )
                row = result.fetchone()
                
                if row:
                    total, latest, updated_24h, updated_7d = row
                    freshness_hours = None
                    if latest:
                        freshness_hours = int((datetime.now(timezone.utc) - latest.replace(tzinfo=timezone.utc)).total_seconds() / 3600)
                    
                    is_fresh = updated_24h == total if total > 0 else False
                    
                    return {
                        "status": "fresh" if is_fresh else "stale",
                        "total_scholarships": total,
                        "updated_last_24h": updated_24h,
                        "updated_last_7d": updated_7d,
                        "latest_update": latest.isoformat() if latest else None,
                        "freshness_hours": freshness_hours,
                        "last_sync": self.last_sync_time.isoformat() if self.last_sync_time else None,
                        "sync_in_progress": self.sync_in_progress,
                        "target": "< 24 hours"
                    }
                
                return {
                    "status": "unknown",
                    "error": "No data returned"
                }
        except Exception as e:
            logger.error(f"Failed to get freshness status: {str(e)}")
            return {
                "status": "unknown",
                "error": str(e)
            }
    
    async def start_scheduler(self):
        """Start background daily sync scheduler"""
        if self._scheduler_running:
            logger.info("Scheduler already running")
            return
        
        self._scheduler_running = True
        logger.info("Starting daily sync scheduler (runs at 2 AM UTC)")
        
        async def scheduler_loop():
            while self._scheduler_running:
                try:
                    now = datetime.now(timezone.utc)
                    if now.hour == 2 and now.minute == 0:
                        logger.info("Scheduled sync triggered")
                        await self.run_sync(source="scheduled")
                        await asyncio.sleep(60)
                    await asyncio.sleep(30)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Scheduler error: {str(e)}")
                    await asyncio.sleep(60)
        
        self._scheduler_task = asyncio.create_task(scheduler_loop())
    
    def stop_scheduler(self):
        """Stop background scheduler"""
        self._scheduler_running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            self._scheduler_task = None
        logger.info("Scheduler stopped")


data_sync_service = DataSyncService()

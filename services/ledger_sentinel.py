"""
Ledger Liveness Sentinel - CEO Directive CIR-20260119-001

Writes heartbeat row to overnight_protocols_ledger every 10 minutes.
Alerts if last_written_at > 15 minutes.
"""
import asyncio
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger("scholarship_api.ledger_sentinel")

class LedgerSentinel:
    """Ledger liveness monitor with heartbeat writes."""
    
    HEARTBEAT_INTERVAL_SECONDS = 600  # 10 minutes
    STALE_THRESHOLD_SECONDS = 900     # 15 minutes
    
    def __init__(self):
        self.incident_id = os.environ.get("INCIDENT_ID", "CIR-20260119-001")
        self.last_heartbeat: Optional[datetime] = None
        self.heartbeat_count = 0
        self.running = False
        self._task: Optional[asyncio.Task] = None
        
    async def write_heartbeat(self, db_session) -> dict:
        """Write heartbeat row to overnight_protocols_ledger."""
        from sqlalchemy import text
        
        ts = datetime.now(timezone.utc)
        event_id = f"SENTINEL-{self.incident_id}-{ts.strftime('%Y%m%d%H%M%S')}"
        
        try:
            result = db_session.execute(text("""
                INSERT INTO overnight_protocols_ledger 
                (event_id, event_type, provider_id, status, description, metadata)
                VALUES (:event_id, 'sentinel_heartbeat', 'system', 'completed',
                        'Ledger liveness sentinel heartbeat',
                        :metadata)
                RETURNING id, event_id, created_at
            """), {
                "event_id": event_id,
                "metadata": f'{{"incident_id": "{self.incident_id}", "heartbeat_count": {self.heartbeat_count + 1}}}'
            })
            
            row = result.fetchone()
            db_session.commit()
            
            self.last_heartbeat = ts
            self.heartbeat_count += 1
            
            logger.info(f"SENTINEL_HEARTBEAT: id={row[0]}, event_id={row[1]}, ts={row[2]}")
            
            return {
                "status": "success",
                "id": row[0],
                "event_id": row[1],
                "created_at": str(row[2]),
                "heartbeat_count": self.heartbeat_count
            }
            
        except Exception as e:
            logger.error(f"SENTINEL_HEARTBEAT_FAILURE: {e}")
            return {
                "status": "error",
                "error": str(e),
                "alert": "LEDGER_PERSIST_FAILURE - rollback trigger"
            }
    
    def check_staleness(self) -> dict:
        """Check if last heartbeat is stale (>15 min)."""
        if not self.last_heartbeat:
            return {
                "stale": True,
                "reason": "no_heartbeat_recorded",
                "alert": True
            }
        
        age_seconds = (datetime.now(timezone.utc) - self.last_heartbeat).total_seconds()
        is_stale = age_seconds > self.STALE_THRESHOLD_SECONDS
        
        return {
            "stale": is_stale,
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "age_seconds": age_seconds,
            "threshold_seconds": self.STALE_THRESHOLD_SECONDS,
            "alert": is_stale
        }
    
    def get_status(self) -> dict:
        """Get sentinel status."""
        staleness = self.check_staleness()
        return {
            "running": self.running,
            "heartbeat_count": self.heartbeat_count,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "staleness": staleness,
            "interval_seconds": self.HEARTBEAT_INTERVAL_SECONDS,
            "threshold_seconds": self.STALE_THRESHOLD_SECONDS
        }

# Singleton instance
ledger_sentinel = LedgerSentinel()

"""
Threat Discovery Background Worker.
Orchestrates periodic continuous polling across configured threat intelligence feeds.
Guarantees:
- Non-overlapping executions via asyncio lock
- Incremental polling using persistent checkpoints
- Graceful error recovery and provider outage handling
- Clean start and shutdown lifecycles
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.repositories.discovery_repo import DiscoveryCheckpointRepository
from app.services.discovery.connector import ThreatSourceConnector
from app.services.discovery.connectors.urlhaus import URLhausConnector
from app.services.discovery.pipeline import ThreatDiscoveryPipeline

logger = get_logger("app.services.discovery.worker")


class ThreatDiscoveryWorker:
    """
    Automated background worker for continuous threat discovery and brand risk monitoring.
    """

    def __init__(
        self,
        connectors: Optional[List[ThreatSourceConnector]] = None,
        poll_interval: Optional[int] = None,
        batch_size: Optional[int] = None,
        session_factory: Optional[Callable[[], AsyncSession]] = None,
    ) -> None:
        settings = get_settings()
        self.connectors: List[ThreatSourceConnector] = connectors if connectors is not None else [
            URLhausConnector()
        ]
        self.poll_interval = poll_interval or settings.THREAT_DISCOVERY_POLL_INTERVAL_SECONDS
        self.batch_size = batch_size or settings.THREAT_DISCOVERY_BATCH_SIZE
        self.session_factory = session_factory or AsyncSessionLocal

        self.pipeline = ThreatDiscoveryPipeline()
        self.checkpoint_repo = DiscoveryCheckpointRepository()

        self._lock = asyncio.Lock()
        self._running = False
        self._stop_event = asyncio.Event()
        self._task: Optional[asyncio.Task] = None
        self._last_cycle_start: Optional[datetime] = None
        self._last_cycle_end: Optional[datetime] = None

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        """Start the background polling worker loop."""
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        self._task = asyncio.create_task(self._poll_loop())
        logger.info(
            f"ThreatDiscoveryWorker started with {len(self.connectors)} connector(s). "
            f"Poll interval: {self.poll_interval}s, Batch size: {self.batch_size}."
        )

    async def stop(self) -> None:
        """Gracefully stop the background polling worker loop."""
        if not self._running:
            return
        logger.info("Stopping ThreatDiscoveryWorker...")
        self._running = False
        self._stop_event.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("ThreatDiscoveryWorker successfully stopped.")

    async def _poll_loop(self) -> None:
        """Background loop executing discovery cycles at configured interval."""
        while self._running:
            try:
                await self.run_discovery_cycle()
            except Exception as exc:
                logger.error(f"Unhandled error in discovery worker cycle: {exc}", exc_info=True)

            try:
                # Wait for next cycle or until stopped
                await asyncio.wait_for(self._stop_event.wait(), timeout=float(self.poll_interval))
                break  # Stop event was set
            except asyncio.TimeoutError:
                continue  # Interval elapsed, proceed to next poll

    async def run_discovery_cycle(
        self,
        db_override: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """
        Execute a single discovery cycle across all connectors.
        Thread-safe: skips concurrent overlapping runs if already executing.
        """
        if self._lock.locked():
            logger.warning("Discovery cycle already in progress. Skipping overlapping execution.")
            return {
                "status": "SKIPPED_OVERLAPPING",
                "message": "Previous discovery cycle is still executing.",
            }

        async with self._lock:
            self._last_cycle_start = datetime.now(timezone.utc)
            cycle_summary: Dict[str, Any] = {
                "started_at": self._last_cycle_start.isoformat(),
                "connectors_processed": 0,
                "total_fetched": 0,
                "total_valid": 0,
                "total_rejected": 0,
                "details": [],
            }

            if db_override:
                await self._execute_connectors(db_override, cycle_summary)
            else:
                async with self.session_factory() as db:
                    await self._execute_connectors(db, cycle_summary)

            self._last_cycle_end = datetime.now(timezone.utc)
            cycle_summary["completed_at"] = self._last_cycle_end.isoformat()
            cycle_summary["duration_seconds"] = (
                self._last_cycle_end - self._last_cycle_start
            ).total_seconds()
            return cycle_summary

    async def _execute_connectors(
        self,
        db: AsyncSession,
        summary: Dict[str, Any],
    ) -> None:
        """Execute each registered connector against the database session."""
        for connector in self.connectors:
            source_id = connector.source_id
            if not connector.is_configured():
                logger.info(f"Connector '{source_id}' is NOT_CONFIGURED. Skipping.")
                await self.checkpoint_repo.record_poll_cycle(
                    db=db,
                    source_id=source_id,
                    success=False,
                    error_message=f"{connector.source_name} is NOT_CONFIGURED.",
                )
                await db.commit()
                summary["details"].append({
                    "source_id": source_id,
                    "status": "NOT_CONFIGURED",
                })
                continue

            # Load persistent checkpoint
            cp = await self.checkpoint_repo.get_or_create(db, source_id)
            current_checkpoint = cp.checkpoint_value

            # Fetch observations from source
            fetch_res = await connector.fetch_observations(
                checkpoint=current_checkpoint,
                limit=self.batch_size,
            )

            if not fetch_res.success:
                logger.warning(
                    f"Poll failed for '{source_id}': {fetch_res.error_message} "
                    f"(rate_limited: {fetch_res.rate_limited})"
                )
                await self.checkpoint_repo.record_poll_cycle(
                    db=db,
                    source_id=source_id,
                    success=False,
                    fetched=fetch_res.items_fetched,
                    rejected=fetch_res.items_rejected,
                    error_message=fetch_res.error_message,
                )
                await db.commit()
                summary["details"].append({
                    "source_id": source_id,
                    "status": "ERROR",
                    "error": fetch_res.error_message,
                })
                continue

            # Process valid records through pipeline
            processed_count = 0
            for record in fetch_res.records:
                try:
                    await self.pipeline.process_record(db, record)
                    processed_count += 1
                except Exception as exc:
                    logger.error(
                        f"Error processing record {record.canonical_value} from {source_id}: {exc}",
                        exc_info=True,
                    )

            # Record success and update checkpoint
            await self.checkpoint_repo.record_poll_cycle(
                db=db,
                source_id=source_id,
                success=True,
                new_checkpoint=fetch_res.new_checkpoint,
                fetched=fetch_res.items_fetched,
                accepted=fetch_res.items_valid,
                rejected=fetch_res.items_rejected,
            )
            await db.commit()

            summary["connectors_processed"] += 1
            summary["total_fetched"] += fetch_res.items_fetched
            summary["total_valid"] += fetch_res.items_valid
            summary["total_rejected"] += fetch_res.items_rejected
            summary["details"].append({
                "source_id": source_id,
                "status": "SUCCESS",
                "fetched": fetch_res.items_fetched,
                "processed": processed_count,
                "new_checkpoint": fetch_res.new_checkpoint,
            })


# Global singleton instance for application lifespan
discovery_worker = ThreatDiscoveryWorker()

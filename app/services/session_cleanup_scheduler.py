import asyncio
from collections.abc import Awaitable, Callable

from app.utils.logger import get_logger

logger = get_logger()


class SessionCleanupScheduler:
    """Periodically logs out users with expired active sessions."""

    def __init__(
        self,
        cleanup: Callable[[], Awaitable[int]],
        interval_seconds: int = 30 * 60,
    ):
        self.cleanup = cleanup
        self.interval_seconds = interval_seconds
        self.task: asyncio.Task | None = None

    async def _run(self):
        while True:
            try:
                count = await self.cleanup()
                logger.info("[Session Scheduler] Logged out %s stale user(s)", count)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error("[Session Scheduler] Cleanup failed: %s", e, exc_info=True)

            await asyncio.sleep(self.interval_seconds)

    def start(self):
        if self.task is None or self.task.done():
            self.task = asyncio.create_task(self._run())

    async def stop(self):
        if self.task is None or self.task.done():
            return

        self.task.cancel()
        try:
            await self.task
        except asyncio.CancelledError:
            pass
        finally:
            self.task = None

"""Sinapsis Local API; optional telemetry is isolated from execution."""
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI

from sinapsis_api.api.routes.agents import agents_router
from sinapsis_api.api.routes.health import health_router
from sinapsis_api.api.routes.jobs import jobs_router
from sinapsis_api.telemetry import collect_inventory, enabled, publish_pending


async def _telemetry_loop() -> None:
    """Send queued events and retry once per hour in a dedicated async task."""
    while enabled():
        await asyncio.to_thread(collect_inventory)
        await asyncio.to_thread(publish_pending)
        await asyncio.sleep(3600)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Start periodic container telemetry only if its own consent is enabled."""
    task = asyncio.create_task(_telemetry_loop()) if enabled() else None
    try:
        yield
    finally:
        if task:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task


app = FastAPI(title='Sinapsis Local API', lifespan=lifespan)
app.include_router(health_router)
app.include_router(agents_router)
app.include_router(jobs_router)

"""Authenticated scheduling operations for immutable saved agent versions."""

from uuid import UUID

from sinapsis_contracts.cloud_api.models.scheduling import (
    AgentSchedule,
    ScheduleCreate,
    SchedulePage,
    SchedulePatch,
    ScheduleRunPage,
    ScheduleStatus,
)
from sinapsis_contracts.cloud_api.paths.scheduling import SCHEDULE_PATHS

from sinapsis_sdk.common.base_resource_client import BaseClientResource


class SchedulesResource(BaseClientResource):
    """Access the Cloud schedule API using the SDK's authenticated transport.

    The resource uses the same token refresh, error mapping, and HTTP transport
    as other Cloud resources. Job execution remains in :class:`JobsResource`.
    """

    def __init__(self, http) -> None:
        """Bind the scheduling resource to the shared HTTP transport."""
        super().__init__(http, SCHEDULE_PATHS.base)

    async def create(self, schedule: ScheduleCreate) -> AgentSchedule:
        """Create a schedule pinned to an immutable agent version.

        Args:
            schedule: Validated scheduling request with recurrence settings.

        Returns:
            The newly created schedule and its next run time.
        """
        payload = schedule.model_dump(mode="json", exclude_none=True)
        data = await self._http.post(self._path(""), json=payload)
        return AgentSchedule.model_validate(data)

    async def list(self, *, limit: int = 100) -> SchedulePage:
        """List the authenticated user's schedules, newest first."""
        data = await self._http.get(self._path(""), params={"limit": limit})
        return SchedulePage.model_validate(data)

    async def get(self, schedule_id: UUID) -> AgentSchedule:
        """Fetch one schedule after server-side ownership verification."""
        data = await self._http.get(self._path(SCHEDULE_PATHS.item, schedule_id=str(schedule_id)))
        return AgentSchedule.model_validate(data)

    async def update(self, schedule_id: UUID, patch: SchedulePatch) -> AgentSchedule:
        """Update a schedule, omitting fields not explicitly provided."""
        if not patch.model_fields_set:
            raise ValueError("At least one schedule field must be updated")
        data = await self._http.patch(
            self._path(SCHEDULE_PATHS.item, schedule_id=str(schedule_id)),
            json=patch.model_dump(mode="json", exclude_unset=True),
        )
        return AgentSchedule.model_validate(data)

    async def pause(self, schedule_id: UUID) -> AgentSchedule:
        """Pause future dispatch without removing the schedule history."""
        return await self.update(schedule_id, SchedulePatch(status=ScheduleStatus.PAUSED))

    async def resume(self, schedule_id: UUID) -> AgentSchedule:
        """Resume a paused schedule; the API calculates its next occurrence."""
        return await self.update(schedule_id, SchedulePatch(status=ScheduleStatus.ACTIVE))

    async def delete(self, schedule_id: UUID) -> None:
        """Disable a schedule while preserving its historical occurrences."""
        await self._http.delete(self._path(SCHEDULE_PATHS.item, schedule_id=str(schedule_id)))

    async def runs(self, schedule_id: UUID, *, limit: int = 100) -> ScheduleRunPage:
        """List dispatch occurrences and their corresponding Redis job IDs."""
        data = await self._http.get(
            self._path(SCHEDULE_PATHS.runs, schedule_id=str(schedule_id)), params={"limit": limit}
        )
        return ScheduleRunPage.model_validate(data)

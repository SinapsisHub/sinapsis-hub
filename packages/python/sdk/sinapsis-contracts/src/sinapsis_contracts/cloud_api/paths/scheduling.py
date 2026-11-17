"""Canonical Cloud scheduling endpoint paths shared by the API and SDK."""

from dataclasses import dataclass

from sinapsis_contracts.common.paths import BaseApiPaths


@dataclass(frozen=True, slots=True)
class SchedulePaths:
    """Paths for authenticated schedule management, including run history.

    The management router is mounted beneath ``/api/v1/management``.
    Paths passed to the HTTP client are fully versioned and require no
    independent CLI or SDK prefix construction.
    """

    base: str = f"{BaseApiPaths.base}/management/agent-schedules"
    item: str = "/{schedule_id}"
    runs: str = "/{schedule_id}/runs"


SCHEDULE_PATHS = SchedulePaths()


@dataclass(frozen=True, slots=True)
class ArchivedResultPaths:
    """Authenticated archive endpoint, separate from live agent streams."""

    base: str = f"{BaseApiPaths.base}/management"
    item: str = "/agent-results/{job_id}/archive"


ARCHIVED_RESULT_PATHS = ArchivedResultPaths()

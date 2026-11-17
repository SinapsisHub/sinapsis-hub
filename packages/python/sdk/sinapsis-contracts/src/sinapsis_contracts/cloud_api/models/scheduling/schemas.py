"""Public schedule and archived-result models; never expose privileged DB fields."""

from datetime import datetime, time
from enum import StrEnum
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ScheduleType(StrEnum):
    """Supported recurrence mechanisms, stored verbatim in PostgreSQL."""

    ONCE = "ONCE"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    INTERVAL = "INTERVAL"


class ScheduleStatus(StrEnum):
    """Schedule lifecycle independent of execution/job state."""

    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"


class OccurrenceStatus(StrEnum):
    """Scheduler dispatch lifecycle, not the agent execution lifecycle."""

    PENDING = "PENDING"
    CLAIMED = "CLAIMED"
    ENQUEUED = "ENQUEUED"
    FAILED = "FAILED"


class ResultKind(StrEnum):
    """Durable output classification for Redis event archives."""

    FINAL = "FINAL"
    STREAM = "STREAM"


class StrictModel(BaseModel):
    """Disallow silently ignored fields in user-provided schedule settings."""

    model_config = ConfigDict(extra="forbid")


class ScheduleFields(StrictModel):
    """Recurrence fields; wall-clock schedules follow the configured timezone."""

    schedule_type: ScheduleType
    timezone: str = Field(default="UTC", min_length=1, max_length=80)
    run_at: datetime | None = None
    local_time: time | None = None
    weekdays: list[int] | None = None
    interval_seconds: int | None = Field(default=None, ge=60, le=31_536_000)

    @model_validator(mode="after")
    def validate_recurrence(self):
        """Require exactly the fields used by the requested schedule type."""
        try:
            ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Unknown IANA timezone") from exc
        if self.schedule_type is ScheduleType.ONCE:
            valid = (
                self.run_at is not None
                and self.run_at.tzinfo is not None
                and self.local_time is None
                and self.weekdays is None
                and self.interval_seconds is None
            )
        elif self.schedule_type is ScheduleType.DAILY:
            valid = (
                self.run_at is None
                and self.local_time is not None
                and self.weekdays is None
                and self.interval_seconds is None
            )
        elif self.schedule_type is ScheduleType.WEEKLY:
            valid = (
                self.run_at is None
                and self.local_time is not None
                and self.weekdays is not None
                and bool(self.weekdays)
                and len(set(self.weekdays)) == len(self.weekdays)
                and all(0 <= day <= 6 for day in self.weekdays)
                and self.interval_seconds is None
            )
        else:
            valid = (
                self.run_at is None
                and self.local_time is None
                and self.weekdays is None
                and self.interval_seconds is not None
            )
        if not valid:
            raise ValueError("Recurrence fields do not match schedule_type")
        return self


class ScheduleCreate(ScheduleFields):
    """Create a schedule pinned to an immutable, owned agent version."""

    name: str = Field(min_length=1, max_length=160)
    agent_id: UUID
    agent_version_id: UUID
    preset_id: UUID | None = None


class SchedulePatch(StrictModel):
    """Update name, pause/resume, or replace the complete recurrence definition."""

    name: str | None = Field(default=None, min_length=1, max_length=160)
    status: ScheduleStatus | None = None
    recurrence: ScheduleFields | None = None


class AgentSchedule(ScheduleCreate):
    """Persisted schedule with its next planned UTC execution."""

    id: UUID
    owner_id: UUID
    created_by: UUID
    status: ScheduleStatus
    next_run_at: datetime
    last_run_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class SchedulePage(StrictModel):
    """A bounded page of the authenticated user's schedules."""

    items: list[AgentSchedule]


class ScheduleRun(StrictModel):
    """One scheduled occurrence, including its Redis job identifier."""

    id: UUID
    schedule_id: UUID
    scheduled_for: datetime
    redis_job_id: str
    status: OccurrenceStatus
    attempt_count: int
    lease_until: datetime | None = None
    enqueued_at: datetime | None = None
    created_at: datetime
    last_error: str | None = None


class ScheduleRunPage(StrictModel):
    """Execution dispatch history for one authorized schedule."""

    items: list[ScheduleRun]


class ArchivedResultFrame(StrictModel):
    """One archived MessagePack frame, base64 encoded for JSON transport."""

    instance_id: str
    stream_id: str
    result_kind: ResultKind
    output_b64: str


class ArchivedResultPage(StrictModel):
    """Archived frames; live Redis streams are a separate API surface."""

    items: list[ArchivedResultFrame]

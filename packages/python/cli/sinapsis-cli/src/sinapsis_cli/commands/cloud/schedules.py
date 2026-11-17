"""Cloud job scheduling commands backed by the authenticated Sinapsis SDK."""

import asyncio
from dataclasses import dataclass
from datetime import datetime, time
from enum import StrEnum
from uuid import UUID

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table
from sinapsis_contracts.cloud_api.models.scheduling import (
    AgentSchedule,
    ScheduleCreate,
    ScheduleFields,
    SchedulePage,
    SchedulePatch,
    ScheduleRunPage,
    ScheduleType,
)

from sinapsis_cli.execution import ExecutionContext, create_api_client
from sinapsis_cli.state import get_agent_selection, record_agent_selection


@dataclass(frozen=True, slots=True)
class ScheduleCLISettings:
    """Immutable defaults shared by the scheduling commands."""

    default_timezone: str = "UTC"
    seconds_per_hour: int = 3600
    default_list_limit: int = 100


SETTINGS = ScheduleCLISettings()


class Weekday(StrEnum):
    """Human-friendly weekday arguments in Python's Monday-first convention."""

    MON = "mon"
    TUE = "tue"
    WED = "wed"
    THU = "thu"
    FRI = "fri"
    SAT = "sat"
    SUN = "sun"


def _parse_datetime(value: str) -> datetime:
    """Require an ISO 8601 timestamp with an explicit UTC offset."""
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise typer.BadParameter("Expected ISO 8601, e.g. 2026-12-01T09:00:00+00:00") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise typer.BadParameter("--once requires an explicit offset, e.g. +00:00 or Z")
    return parsed


def _parse_local_time(value: str) -> time:
    """Parse a local wall-clock time without an embedded timezone offset."""
    try:
        parsed = time.fromisoformat(value)
    except ValueError as error:
        raise typer.BadParameter("Expected local time HH:MM or HH:MM:SS") from error
    if parsed.tzinfo is not None:
        raise typer.BadParameter("Use --timezone for daily/weekly times, not a time offset")
    return parsed


def _make_recurrence(
    *,
    once: str | None,
    daily: str | None,
    weekly: str | None,
    every_hours: int | None,
    weekday: list[Weekday] | None,
    timezone: str,
) -> ScheduleFields:
    """Validate exactly one recurrence mode through shared public contracts."""
    modes = (once, daily, weekly, every_hours)
    if sum(value is not None for value in modes) != 1:
        raise typer.BadParameter("Choose exactly one of --once, --daily, --weekly, or --every-hours")

    if weekday and weekly is None:
        raise typer.BadParameter("--weekday requires --weekly")

    fields: dict[str, object] = {"timezone": timezone}
    if once is not None:
        fields.update(schedule_type=ScheduleType.ONCE, run_at=_parse_datetime(once))
    elif daily is not None:
        fields.update(schedule_type=ScheduleType.DAILY, local_time=_parse_local_time(daily))
    elif weekly is not None:
        if not weekday:
            raise typer.BadParameter("--weekly requires at least one --weekday (mon to sun)")
        fields.update(
            schedule_type=ScheduleType.WEEKLY,
            local_time=_parse_local_time(weekly),
            weekdays=sorted({list(Weekday).index(day) for day in weekday}),
        )
    else:
        if every_hours is None or every_hours <= 0:
            raise typer.BadParameter("--every-hours must be a positive whole number")
        fields.update(
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=every_hours * SETTINGS.seconds_per_hour,
        )

    try:
        return ScheduleFields.model_validate(fields)
    except ValidationError as error:
        raise typer.BadParameter(str(error)) from error


def _optional_recurrence(
    *,
    once: str | None,
    daily: str | None,
    weekly: str | None,
    every_hours: int | None,
    weekday: list[Weekday] | None,
    timezone: str | None,
) -> ScheduleFields | None:
    """Build a replacement recurrence or leave the current one intact."""
    if not any(value is not None for value in (once, daily, weekly, every_hours)):
        if timezone is not None or weekday:
            raise typer.BadParameter("Changing timezone or weekdays requires a full recurrence mode")
        return None
    if timezone is None:
        raise typer.BadParameter("Specify --timezone when replacing a recurrence")
    return _make_recurrence(
        once=once,
        daily=daily,
        weekly=weekly,
        every_hours=every_hours,
        weekday=weekday,
        timezone=timezone,
    )


def _format_time(value: datetime | None) -> str:
    """Render an optional timestamp without hiding its timezone offset."""
    return value.isoformat(timespec="seconds") if value is not None else "—"


def _print_schedule(schedule: AgentSchedule) -> None:
    """Display one schedule and its saved agent/version identifiers."""
    typer.echo(f"Schedule: {schedule.name}")
    typer.echo(f"ID: {schedule.id}   Status: {schedule.status.value}")
    typer.echo(f"Agent: {schedule.agent_id}   Version: {schedule.agent_version_id}")
    typer.echo(f"Recurrence: {schedule.schedule_type.value}   Timezone: {schedule.timezone}")
    if schedule.run_at is not None:
        typer.echo(f"Runs once: {_format_time(schedule.run_at)}")
    elif schedule.local_time is not None:
        typer.echo(f"Local time: {schedule.local_time.isoformat(timespec='minutes')}")
    if schedule.weekdays:
        days = ", ".join(list(Weekday)[day].value for day in schedule.weekdays)
        typer.echo(f"Weekdays: {days}")
    if schedule.interval_seconds is not None:
        typer.echo(f"Every {schedule.interval_seconds // SETTINGS.seconds_per_hour} hours")
    if schedule.preset_id is not None:
        typer.echo(f"Preset: {schedule.preset_id}")
    typer.echo(f"Next run: {_format_time(schedule.next_run_at)}")
    typer.echo(f"Last run: {_format_time(schedule.last_run_at)}")


def _print_schedule_page(page: SchedulePage) -> None:
    """Render schedules in a compact table suitable for terminals."""
    if not page.items:
        typer.echo("No schedules found.")
        return
    table = Table(title="Agent schedules")
    for heading in ("Name", "ID", "Status", "Recurrence", "Next run"):
        table.add_column(heading)
    for item in page.items:
        table.add_row(
            item.name,
            str(item.id),
            item.status.value,
            item.schedule_type.value,
            _format_time(item.next_run_at),
        )
    Console().print(table)


def _print_runs(page: ScheduleRunPage) -> None:
    """Render dispatch history with job IDs usable by ``jobs status``."""
    if not page.items:
        typer.echo("No scheduled runs found.")
        return
    table = Table(title="Scheduled runs")
    for heading in ("Scheduled for", "Status", "Job ID", "Attempts", "Error"):
        table.add_column(heading)
    for item in page.items:
        table.add_row(
            _format_time(item.scheduled_for),
            item.status.value,
            item.redis_job_id,
            str(item.attempt_count),
            item.last_error or "",
        )
    Console().print(table)


async def resolve_schedule_selection(agents_resource, profile: str, agent_id: UUID | None, version_id: UUID | None):
    """Resolve and authenticate all four documented ID-selection combinations."""
    selected = get_agent_selection(profile)
    resolved_agent = agent_id or (selected[0] if selected else None)
    if resolved_agent is None:
        raise typer.BadParameter("No selected agent; provide --agent-id or register one")

    if version_id is not None:
        candidate = version_id
    elif agent_id is None and selected is not None:
        candidate = selected[1]
    else:
        candidate = None

    saved = (
        await agents_resource.version(resolved_agent, candidate)
        if candidate is not None
        else await agents_resource.latest_version(resolved_agent)
    )
    if saved.agent_id != resolved_agent:
        raise typer.BadParameter("Version does not belong to the specified agent")
    return saved


def create_app(execution: ExecutionContext) -> typer.Typer:
    """Build the ``jobs schedule`` command group for the current Cloud profile."""
    app = typer.Typer(
        name="schedule",
        help="Schedule saved agent versions and manage recurring jobs.",
        no_args_is_help=True,
    )

    @app.command("create")
    def create(
        name: str = typer.Option(..., "--name", help="Friendly schedule name."),
        agent_id: UUID | None = typer.Option(None, "--agent-id", help="Saved agent UUID; defaults to last selection."),
        agent_version_id: UUID | None = typer.Option(
            None, "--agent-version-id", help="Immutable version UUID; defaults to saved or newest."
        ),
        preset_id: UUID | None = typer.Option(None, "--preset-id", help="Optional saved agent preset UUID."),
        once: str | None = typer.Option(None, "--once", help="Once at ISO 8601 timestamp with UTC offset."),
        daily: str | None = typer.Option(None, "--daily", help="Daily at local time HH:MM."),
        weekly: str | None = typer.Option(None, "--weekly", help="Weekly at local time HH:MM."),
        every_hours: int | None = typer.Option(None, "--every-hours", help="Fixed elapsed interval in hours."),
        weekday: list[Weekday] | None = typer.Option(None, "--weekday", help="Weekday for --weekly; repeat."),
        timezone: str = typer.Option(SETTINGS.default_timezone, "--timezone", help="IANA timezone."),
    ) -> None:
        """Schedule an existing, saved agent version; do not submit YAML directly."""
        recurrence = _make_recurrence(
            once=once,
            daily=daily,
            weekly=weekly,
            every_hours=every_hours,
            weekday=weekday,
            timezone=timezone,
        )

        async def operation() -> None:
            async with create_api_client(execution) as client:
                saved = await resolve_schedule_selection(
                    client.agents, execution.profile_name, agent_id, agent_version_id
                )
                request = ScheduleCreate(
                    **recurrence.model_dump(),
                    name=name,
                    agent_id=saved.agent_id,
                    agent_version_id=saved.id,
                    preset_id=preset_id,
                )
                created = await client.schedules.create(request)
            record_agent_selection(execution.profile_name, saved.agent_id, saved.id)
            typer.echo("Schedule created.")
            _print_schedule(created)

        asyncio.run(operation())

    @app.command("list")
    def list_schedules(
        limit: int = typer.Option(SETTINGS.default_list_limit, "--limit", min=1, max=200),
    ) -> None:
        """List schedules owned by the current Cloud user."""

        async def operation() -> None:
            async with create_api_client(execution) as client:
                page = await client.schedules.list(limit=limit)
            _print_schedule_page(page)

        asyncio.run(operation())

    @app.command("show")
    def show(schedule_id: UUID = typer.Argument(..., help="Schedule UUID.")) -> None:
        """Display recurrence details and the next expected run."""

        async def operation() -> None:
            async with create_api_client(execution) as client:
                schedule = await client.schedules.get(schedule_id)
            _print_schedule(schedule)

        asyncio.run(operation())

    @app.command("update")
    def update(
        schedule_id: UUID = typer.Argument(..., help="Schedule UUID."),
        name: str | None = typer.Option(None, "--name", help="New schedule name."),
        once: str | None = typer.Option(None, "--once", help="Replace with one-time execution."),
        daily: str | None = typer.Option(None, "--daily", help="Replace with a daily local time."),
        weekly: str | None = typer.Option(None, "--weekly", help="Replace with a weekly local time."),
        every_hours: int | None = typer.Option(None, "--every-hours", help="Replace with fixed interval."),
        weekday: list[Weekday] | None = typer.Option(None, "--weekday", help="Repeat for weekly days."),
        timezone: str | None = typer.Option(None, "--timezone", help="IANA timezone for new recurrence."),
    ) -> None:
        """Rename a schedule or replace its complete recurrence definition."""
        recurrence = _optional_recurrence(
            once=once,
            daily=daily,
            weekly=weekly,
            every_hours=every_hours,
            weekday=weekday,
            timezone=timezone,
        )
        if name is None and recurrence is None:
            raise typer.BadParameter("Provide --name or a new recurrence")
        patch = SchedulePatch(name=name, recurrence=recurrence)
        patch = SchedulePatch.model_validate(patch.model_dump(exclude_none=True))

        async def operation() -> None:
            async with create_api_client(execution) as client:
                updated = await client.schedules.update(schedule_id, patch)
            typer.echo("Schedule updated.")
            _print_schedule(updated)

        asyncio.run(operation())

    @app.command("pause")
    def pause(schedule_id: UUID = typer.Argument(..., help="Schedule UUID.")) -> None:
        """Pause future occurrences without deleting the schedule."""

        async def operation() -> None:
            async with create_api_client(execution) as client:
                schedule = await client.schedules.pause(schedule_id)
            _print_schedule(schedule)

        asyncio.run(operation())

    @app.command("resume")
    def resume(schedule_id: UUID = typer.Argument(..., help="Schedule UUID.")) -> None:
        """Resume a paused schedule and recalculate its next occurrence."""

        async def operation() -> None:
            async with create_api_client(execution) as client:
                schedule = await client.schedules.resume(schedule_id)
            _print_schedule(schedule)

        asyncio.run(operation())

    @app.command("delete")
    def delete(
        schedule_id: UUID = typer.Argument(..., help="Schedule UUID."),
        yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt."),
    ) -> None:
        """Disable a schedule, retaining dispatch and job history."""
        if not yes and not typer.confirm(f"Disable schedule {schedule_id}?"):
            raise typer.Abort()

        async def operation() -> None:
            async with create_api_client(execution) as client:
                await client.schedules.delete(schedule_id)
            typer.echo(f"Schedule disabled: {schedule_id}")

        asyncio.run(operation())

    @app.command("runs")
    def runs(
        schedule_id: UUID = typer.Argument(..., help="Schedule UUID."),
        limit: int = typer.Option(SETTINGS.default_list_limit, "--limit", min=1, max=200),
    ) -> None:
        """Display scheduled dispatches and their Redis job identifiers."""

        async def operation() -> None:
            async with create_api_client(execution) as client:
                page = await client.schedules.runs(schedule_id, limit=limit)
            _print_runs(page)

        asyncio.run(operation())

    return app

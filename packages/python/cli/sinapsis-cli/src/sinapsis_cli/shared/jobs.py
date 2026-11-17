"""Shared job helpers for the Sinapsis CLI."""


import typer

from sinapsis_cli.execution import ExecutionContext
from sinapsis_cli.state import (
    JobRecord,
    clear_jobs,
    clear_state,
    get_job,
    get_last_job_id,
    list_jobs,
)


def resolve_job_id(job_id: str | None, *, profile_name: str) -> str:
    """Resolve an explicit or profile-scoped remembered job ID.

    Args:
        job_id: Explicit job ID, or ``None`` to use the profile's latest job.
        profile_name: Name of the profile whose job history should be used.

    Returns:
        The resolved job ID.

    Raises:
        typer.Exit: If no explicit or remembered job ID is available.
    """
    if job_id is not None:
        return job_id

    resolved_job_id = get_last_job_id(profile_name)

    if resolved_job_id is None:
        typer.echo(f"No job ID was provided and profile {profile_name!r} has no previous job.", err=True)
        raise typer.Exit(code=1)

    return resolved_job_id


def get_job_record(job_id: str, *, profile_name: str) -> JobRecord:
    """Return a job recorded for the selected profile or fail.

    Args:
        job_id: Job identifier to retrieve.
        profile_name: Profile expected to own the job.

    Returns:
        The matching job record.

    Raises:
        typer.Exit: If the job is missing, unscoped, or belongs to another
            profile.
    """
    record = get_job(job_id)

    if record is None:
        typer.echo(f"Job {job_id!r} is not recorded in local CLI state.", err=True)
        raise typer.Exit(code=1)

    if record.profile is None:
        typer.echo(
            f"Job {job_id!r} predates profile-scoped history and could not be mapped safely to a profile.",
            err=True,
        )
        raise typer.Exit(code=1)

    if record.profile != profile_name:
        typer.echo(f"Job {job_id!r} belongs to profile {record.profile!r}, not {profile_name!r}.", err=True)
        raise typer.Exit(code=1)

    return record


def require_job_target(job_id: str, *, profile_name: str, default_target: str) -> str:
    """Resolve the API endpoint without requiring local job history.

    A job submitted through this profile retains its recorded endpoint.
    Scheduled, remote, or externally submitted jobs have no local record:
    send explicit IDs to the selected profile's API, where the server
    authorizes access. A record from another profile never chooses that
    profile's endpoint implicitly.
    """
    record = get_job(job_id)
    if record is not None and record.profile == profile_name and record.target:
        return record.target
    return default_target


def register_history_commands(app: typer.Typer, execution: ExecutionContext) -> None:
    """Register job-history commands shared by all execution backends.

    Args:
        app: Backend-specific jobs application.
        execution: Resolved execution context for the current invocation.
    """

    @app.command("list")
    def list_command(
        all_profiles: bool = typer.Option(
            False, "--all-profiles", help="Include jobs submitted through every profile."
        ),
    ) -> None:
        """List jobs remembered by the CLI."""
        profile_name = None if all_profiles else execution.profile_name
        jobs = list_jobs(profile_name)

        if not jobs:
            typer.echo("No jobs have been recorded.")
            return

        last_job_id = get_last_job_id(execution.profile_name)

        for job in jobs:
            marker = "*" if job.job_id == last_job_id else " "
            source = job.source or "-"
            profile = job.profile or "legacy"
            target = job.target or "-"

            typer.echo(f"{marker} {job.job_id}  {job.submitted_at}  {profile}  {target}  {source}")

    @app.command("clear")
    def clear_command(
        all_profiles: bool = typer.Option(False, "--all-profiles", help="Clear job history for every profile."),
    ) -> None:
        """Clear remembered job state."""
        if all_profiles:
            clear_state()
            typer.echo("Job history cleared for all profiles.")
            return

        clear_jobs(execution.profile_name)
        typer.echo(f"Job history cleared for profile {execution.profile_name!r}.")

"""Local API job backend for the Sinapsis CLI."""

import asyncio
from pathlib import Path
from typing import Any

import typer
from sinapsis.agent import generic_agent_schema_builder
from sinapsis_contracts.local_api.models import JobResponse
from sinapsis_protocol import SSEEnvelope

from sinapsis_cli.execution import ExecutionContext, create_api_client
from sinapsis_cli.shared.jobs import register_history_commands, require_job_target, resolve_job_id
from sinapsis_cli.shared.terminal import divider
from sinapsis_cli.shared.writer import ResultWriter
from sinapsis_cli.state import record_job

TERMINAL_JOB_STATUSES = frozenset({"completed", "failed", "cancelled"})
LOCAL_API_POLL_INTERVAL_SECONDS = 0.25


def create_app(execution: ExecutionContext) -> typer.Typer:
    """Create the local-API jobs command tree."""
    app = typer.Typer(name="jobs", help="Manage jobs through the local Sinapsis API.", no_args_is_help=True)

    @app.command()
    def run(
        agent_definition: Path = typer.Argument(
            ...,
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Path to the agent definition.",
        ),
        wait: bool = typer.Option(
            False, "--wait", help="Wait for the job to finish and retrieve its retained results."
        ),
        result: bool = typer.Option(False, "--result", help="Retrieve retained results after submission."),
        stream: bool = typer.Option(False, "--stream", help="Stream job events until the job finishes."),
        save_dir: Path = typer.Option(
            Path("results"),
            "--save-dir",
            "-o",
            help="Directory where results and artifacts are saved.",
        ),
        print_only: bool = typer.Option(False, "--print-only", help="Print results instead of saving artifacts."),
    ) -> None:
        """Create an agent and submit a job through the local API."""
        selected = sum(bool(value) for value in (wait, result, stream))
        if selected > 1:
            typer.echo("Options --wait, --result, and --stream are mutually exclusive.", err=True)
            raise typer.Exit(code=1)

        asyncio.run(
            run_local_api_job(
                execution,
                agent_definition,
                wait=wait,
                result=result,
                stream=stream,
                save_dir=save_dir,
                print_only=print_only,
            )
        )

    @app.command()
    def status(
        job_id: str | None = typer.Argument(None, help="ID of the job. Defaults to this profile's most recent job."),
    ) -> None:
        """Show the current status of a local-API job."""
        resolved_job_id = resolve_job_id(job_id, profile_name=execution.profile_name)
        asyncio.run(get_local_api_status(execution, resolved_job_id))

    @app.command("result")
    def result_command(
        job_id: str | None = typer.Argument(None, help="ID of the job. Defaults to this profile's most recent job."),
        save_dir: Path = typer.Option(
            Path("results"),
            "--save-dir",
            "-o",
            help="Directory where results and artifacts are saved.",
        ),
        print_only: bool = typer.Option(False, "--print-only", help="Print results instead of saving artifacts."),
    ) -> None:
        """Replay retained results for a local-API job."""
        resolved_job_id = resolve_job_id(job_id, profile_name=execution.profile_name)
        asyncio.run(get_local_api_result(execution, resolved_job_id, save_dir=save_dir, print_only=print_only))

    @app.command("stream")
    def stream_command(
        job_id: str | None = typer.Argument(None, help="ID of the job. Defaults to this profile's most recent job."),
        save_dir: Path = typer.Option(
            Path("results"),
            "--save-dir",
            "-o",
            help="Directory where streamed results and artifacts are saved.",
        ),
        print_only: bool = typer.Option(
            False, "--print-only", help="Print streamed results instead of saving artifacts."
        ),
    ) -> None:
        """Stream events from a running local-API job."""
        resolved_job_id = resolve_job_id(job_id, profile_name=execution.profile_name)
        asyncio.run(stream_local_api_job(execution, resolved_job_id, save_dir=save_dir, print_only=print_only))

    @app.command()
    def cancel(
        job_id: str | None = typer.Argument(None, help="ID of the job. Defaults to this profile's most recent job."),
    ) -> None:
        """Cancel a running local-API job."""
        resolved_job_id = resolve_job_id(job_id, profile_name=execution.profile_name)
        asyncio.run(cancel_local_api_job(execution, resolved_job_id))

    register_history_commands(app, execution)
    return app


async def run_local_api_job(
    execution: ExecutionContext,
    agent_definition: Path,
    *,
    wait: bool,
    result: bool,
    stream: bool,
    save_dir: Path,
    print_only: bool,
) -> None:
    """Submit a job to the local Sinapsis API."""
    api_url = execution.api_url
    definition = generic_agent_schema_builder(agent_definition)

    async with create_api_client(execution) as client:
        submission = await client.jobs.submit(definition)

    job_id = submission.job_id
    record_job(
        job_id,
        source=agent_definition,
        target=api_url,
        profile=execution.profile_name,
        backend=execution.profile.backend.value,
    )

    typer.echo(f"Job ID: {job_id}")

    if stream:
        await _stream_local_api_job(execution, job_id, api_url=api_url, save_dir=save_dir, print_only=print_only)
        return

    if wait:
        await _wait_for_local_api_job(execution, job_id, api_url=api_url, save_dir=save_dir, print_only=print_only)
        return

    if result:
        await _get_local_api_result(execution, job_id, api_url=api_url, save_dir=save_dir, print_only=print_only)


async def get_local_api_job(execution: ExecutionContext, job_id: str, *, api_url: str) -> JobResponse:
    """Retrieve local API job state."""
    async with create_api_client(execution, api_url=api_url) as client:
        return await client.jobs.get_status(job_id)


async def _wait_for_local_api_job(
    execution: ExecutionContext, job_id: str, *, api_url: str, save_dir: Path, print_only: bool
) -> None:
    """Wait for a local API job to reach a terminal state."""
    typer.echo("Waiting for job to finish...")

    async with create_api_client(execution, api_url=api_url) as client:
        while True:
            job = await client.jobs.get_status(job_id)
            print_local_api_status(job)

            if job.status in TERMINAL_JOB_STATUSES:
                break

            await asyncio.sleep(LOCAL_API_POLL_INTERVAL_SECONDS)

    if job.status == "failed":
        return

    await _get_local_api_result(execution, job_id, api_url=api_url, save_dir=save_dir, print_only=print_only)


async def _stream_local_api_job(
    execution: ExecutionContext, job_id: str, *, api_url: str, save_dir: Path, print_only: bool
) -> None:
    """Stream decoded local API job events."""
    async with create_api_client(execution, api_url=api_url) as client:
        async for event in client.jobs.stream_results(job_id):
            handle_local_envelope(event.envelope, metadata=event.metadata, save_dir=save_dir, print_only=print_only)

            job = await client.jobs.get_status(job_id)
            if job.status in TERMINAL_JOB_STATUSES:
                typer.echo(f"Job {job_id} {job.status}.")
                return


async def _get_local_api_result(
    execution: ExecutionContext, job_id: str, *, api_url: str, save_dir: Path, print_only: bool
) -> None:
    """Replay retained local API events."""
    async with create_api_client(execution, api_url=api_url) as client:
        events = await client.jobs.get_result(job_id)

    for event in events:
        handle_local_envelope(event.envelope, metadata=event.metadata, save_dir=save_dir, print_only=print_only)


def handle_local_envelope(envelope: SSEEnvelope, *, metadata: dict[str, Any], save_dir: Path, print_only: bool) -> None:
    """Print or save one decoded local API event."""
    if print_only:
        print_local_envelope(envelope, metadata=metadata)
        return

    if envelope.data is None:
        return

    writer = ResultWriter(save_dir)
    written = writer.write_container(
        envelope.data,
        agent_id=envelope.agent_id or metadata.get("agent_id"),
        stream_name=envelope.job_id or metadata.get("job_id"),
    )

    if written:
        typer.echo(f"Saved {len(written)} file(s) to {save_dir}")


def print_local_envelope(envelope: SSEEnvelope, *, metadata: dict[str, Any]) -> None:
    """Print one local API SSEEnvelope."""
    typer.echo(f"Cursor:      {metadata.get('cursor', '-')}")
    typer.echo(f"Agent:       {envelope.agent_id or metadata.get('agent_id', '-')}")
    typer.echo(f"Job:         {envelope.job_id or metadata.get('job_id', '-')}")
    typer.echo(f"Event:       {envelope.event_type}")
    typer.echo(f"Status:      {envelope.agent_status or '-'}")

    if envelope.errors:
        typer.echo(f"Errors:      {envelope.errors}")

    if envelope.data is not None:
        typer.echo(f"Container:   {envelope.data.container_id}")

    divider(0)


def print_local_api_status(job: JobResponse) -> None:
    """Print local API job state."""
    typer.echo(f"Job ID:      {job.job_id}")
    typer.echo(f"State:       {job.status}")
    typer.echo(f"Agent:       {job.agent_id}")
    typer.echo(f"Instance:    {job.instance_id or '-'}")
    typer.echo(f"Error:       {job.error or '-'}")


async def get_local_api_status(execution: ExecutionContext, job_id: str) -> None:
    """Show the current status of a local API job."""
    api_url = require_job_target(job_id, profile_name=execution.profile_name, default_target=execution.api_url)
    job = await get_local_api_job(execution, job_id, api_url=api_url)
    print_local_api_status(job)


async def get_local_api_result(execution: ExecutionContext, job_id: str, *, save_dir: Path, print_only: bool) -> None:
    """Retrieve a local API job result from retained events."""
    api_url = require_job_target(job_id, profile_name=execution.profile_name, default_target=execution.api_url)
    await _get_local_api_result(execution, job_id, api_url=api_url, save_dir=save_dir, print_only=print_only)


async def stream_local_api_job(execution: ExecutionContext, job_id: str, *, save_dir: Path, print_only: bool) -> None:
    """Stream a local API job from its recorded target."""
    api_url = require_job_target(job_id, profile_name=execution.profile_name, default_target=execution.api_url)
    await _stream_local_api_job(execution, job_id, api_url=api_url, save_dir=save_dir, print_only=print_only)


async def cancel_local_api_job(execution: ExecutionContext, job_id: str) -> None:
    """Cancel a local API job."""
    api_url = require_job_target(job_id, profile_name=execution.profile_name, default_target=execution.api_url)

    async with create_api_client(execution, api_url=api_url) as client:
        await client.jobs.cancel(job_id)

    typer.echo(f"Cancelled job {job_id}.")

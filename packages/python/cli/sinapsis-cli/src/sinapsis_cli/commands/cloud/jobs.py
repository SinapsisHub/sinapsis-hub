"""Cloud API job backend for the Sinapsis CLI."""

import asyncio
from pathlib import Path

import typer
from sinapsis.agent import load_yaml_config
from sinapsis.sentinels import SinapsisSentinel
from sinapsis_contracts.common.sentinels import SINAPSIS_AGENT_FINISHED, SINAPSIS_END_OF_STREAM
from sinapsis_deserialization.schemas import SSEMessage
from sinapsis_sdk.cloud_api.models import JobResult, JobStatus
from sinapsis_sdk.common.exceptions import APIError, NotFoundError

from sinapsis_cli.execution import ExecutionContext, build_api_config, create_api_client
from sinapsis_cli.shared.jobs import register_history_commands, require_job_target, resolve_job_id
from sinapsis_cli.shared.terminal import divider
from sinapsis_cli.shared.writer import ResultWriter
from sinapsis_cli.state import record_job

from .files import _get_staging_file


def create_app(execution: ExecutionContext) -> typer.Typer:
    """Create the cloud jobs command tree.

    Args:
        execution: Resolved execution context for the current invocation.

    Returns:
        Typer application containing cloud job commands.
    """
    app = typer.Typer(name="jobs", help="Manage Sinapsis Cloud jobs.", no_args_is_help=True)

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
        wait: bool = typer.Option(False, "--wait", help="Wait for the job to finish and retrieve its result."),
        result: bool = typer.Option(False, "--result", help="Retrieve the result after submission."),
        stream: bool = typer.Option(False, "--stream", help="Stream results until the job finishes."),
        refresh: bool = typer.Option(
            False,
            "--refresh",
            help="Refresh the result from the API instead of using a local result.",
        ),
        save_dir: Path = typer.Option(
            Path("results"),
            "--save-dir",
            "-o",
            help="Directory where results and artifacts are saved.",
        ),
        print_only: bool = typer.Option(False, "--print-only", help="Print results instead of saving artifacts."),
    ) -> None:
        """Submit an agent as a cloud job."""
        selected = sum(bool(value) for value in (wait, result, stream))

        if selected > 1:
            typer.echo("Options --wait, --result, and --stream are mutually exclusive.", err=True)
            raise typer.Exit(code=1)

        if refresh and not result:
            typer.echo("--refresh can only be used with --result.", err=True)
            raise typer.Exit(code=1)

        asyncio.run(
            run_cloud_job(
                execution,
                agent_definition,
                wait=wait,
                result=result,
                stream=stream,
                refresh=refresh,
                save_dir=save_dir,
                print_only=print_only,
            )
        )

    @app.command()
    def status(
        job_id: str | None = typer.Argument(None, help="ID of the job. Defaults to this profile's most recent job."),
        verbose: bool = typer.Option(False, "--verbose", "-v", help="Include the full agent definition."),
    ) -> None:
        """Show the current status of a cloud job."""
        resolved_job_id = resolve_job_id(job_id, profile_name=execution.profile_name)
        asyncio.run(get_cloud_status(execution, resolved_job_id, verbose=verbose))

    @app.command("result")
    def result_command(
        job_id: str | None = typer.Argument(None, help="ID of the job. Defaults to this profile's most recent job."),
        refresh: bool = typer.Option(False, "--refresh", help="Always retrieve the result from the API."),
        save_dir: Path = typer.Option(
            Path("results"),
            "--save-dir",
            "-o",
            help="Directory where results and artifacts are saved.",
        ),
        print_only: bool = typer.Option(False, "--print-only", help="Print results instead of saving artifacts."),
    ) -> None:
        """Retrieve a cloud job result."""
        resolved_job_id = resolve_job_id(job_id, profile_name=execution.profile_name)
        asyncio.run(
            get_cloud_result(
                execution,
                resolved_job_id,
                refresh=refresh,
                save_dir=save_dir,
                print_only=print_only,
            )
        )

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
        """Stream results from a running cloud job."""
        resolved_job_id = resolve_job_id(job_id, profile_name=execution.profile_name)
        asyncio.run(stream_cloud_job(execution, resolved_job_id, save_dir=save_dir, print_only=print_only))

    @app.command()
    def cancel(
        job_id: str | None = typer.Argument(None, help="ID of the job. Defaults to this profile's most recent job."),
    ) -> None:
        """Cancel a running cloud job."""
        resolved_job_id = resolve_job_id(job_id, profile_name=execution.profile_name)
        asyncio.run(cancel_cloud_job(execution, resolved_job_id))

    from sinapsis_cli.commands.cloud.schedules import create_app as create_schedules_app

    app.add_typer(create_schedules_app(execution), name="schedule")
    register_history_commands(app, execution)
    return app


def _get_api_config(execution: ExecutionContext, *, job_id: str | None = None):
    """Build SDK API configuration for the selected profile or recorded job."""
    api_url = execution.api_url

    if job_id is not None:
        api_url = require_job_target(job_id, profile_name=execution.profile_name, default_target=execution.api_url)

    return build_api_config(execution, api_url=api_url)


async def run_cloud_job(
    execution: ExecutionContext,
    agent_definition: Path,
    *,
    wait: bool,
    result: bool,
    stream: bool,
    refresh: bool,
    save_dir: Path,
    print_only: bool,
) -> None:
    """Submit and optionally follow a cloud API job."""
    config = _get_api_config(execution)

    async with create_api_client(execution, api_url=config.api_url) as client:
        definition = load_yaml_config(agent_definition)
        submission = await client.jobs.submit(definition)
        job_id = submission.job_id

    record_job(
        job_id,
        source=agent_definition,
        target=config.api_url,
        profile=execution.profile_name,
        backend=execution.profile.backend.value,
    )

    typer.echo(f"Job ID: {job_id}")

    if stream:
        await _stream_cloud_job(execution, job_id, api_url=config.api_url, save_dir=save_dir, print_only=print_only)
        return

    if wait:
        await _wait_for_cloud_job(execution, job_id, api_url=config.api_url, save_dir=save_dir, print_only=print_only)
        return

    if result:
        await _get_cloud_result(
            execution,
            job_id,
            api_url=config.api_url,
            refresh=refresh,
            save_dir=save_dir,
            print_only=print_only,
        )


async def _wait_for_cloud_job(
    execution: ExecutionContext, job_id: str, *, api_url: str, save_dir: Path, print_only: bool
) -> None:
    """Poll a cloud job until completion and retrieve its result."""
    typer.echo("Waiting for job to finish...")

    async with create_api_client(execution, api_url=api_url) as client:
        while True:
            status = await client.jobs.get_status(job_id)
            _print_status(status)

            if _is_done(status):
                break

            await asyncio.sleep(1.0)

    if getattr(status, "error", None):
        return

    await _get_cloud_result(execution, job_id, api_url=api_url, refresh=True, save_dir=save_dir, print_only=print_only)


def _archival_fallback_error(exc: Exception) -> bool:
    """Only missing/expired Redis results trigger archive recovery."""
    return isinstance(exc, NotFoundError) or (
        isinstance(exc, APIError) and exc.status_code == 503 and "Job state unavailable" in str(exc)
    )


async def _replay_archived_results(
    client,
    execution: ExecutionContext,
    job_id: str,
    *,
    api_url: str,
    save_dir: Path,
    print_only: bool,
) -> int:
    """Replay archived stream frames as normal streaming output."""
    count = 0
    writer = None if print_only else ResultWriter(save_dir)

    async for message in client.jobs.archived_stream_results(job_id):
        if isinstance(message, SinapsisSentinel):
            continue
        if not count:
            typer.echo("Replaying archived stream frames from the database.")
        count += 1
        if print_only:
            _print_result(message)
        else:
            assert writer is not None
            written = writer.write(message)
            if written:
                typer.echo(f"Saved {len(written)} file(s) to {save_dir}")
        try:
            await _fetch_content_files(execution, message, save_dir, api_url=api_url)
        except NotFoundError:
            typer.echo("Note: a staged file referenced by archived output has expired.", err=True)
    return count


async def _get_cloud_result(
    execution: ExecutionContext,
    job_id: str,
    *,
    api_url: str,
    refresh: bool,
    save_dir: Path,
    print_only: bool,
) -> None:
    """Get the Redis result or replay the last one/two archived output frames."""
    del refresh
    async with create_api_client(execution, api_url=api_url) as client:
        try:
            results = [await client.jobs.get_result(job_id)]
        except (NotFoundError, APIError) as exc:
            if not _archival_fallback_error(exc):
                raise
            results = await client.jobs.archived_recent_results(job_id)
            if not results:
                typer.echo(
                    f"No result frames are available for job {job_id} in Redis or the database archive.",
                    err=True,
                )
                raise typer.Exit(code=1) from exc
            typer.echo(f"Recovered {len(results)} recent result frame(s) from the database archive.")

        for message in results:
            if isinstance(message, SinapsisSentinel):
                continue
            _handle_result(message, save_dir=save_dir, print_only=print_only)
            await _fetch_content_files(execution, message, save_dir, api_url=api_url)


async def _stream_cloud_job(
    execution: ExecutionContext, job_id: str, *, api_url: str, save_dir: Path, print_only: bool
) -> None:
    """Stream running jobs, or replay durable output for finished/expired jobs."""
    writer = None if print_only else ResultWriter(save_dir)

    async with create_api_client(execution, api_url=api_url) as client:
        try:
            job_status = await client.jobs.get_status(job_id)
        except (NotFoundError, APIError) as exc:
            if not _archival_fallback_error(exc):
                raise
            # A fully expired Redis job still has a separately authorized
            # Management archive that can be replayed without Redis metadata.
            job_status = None

        if job_status is None or _is_done(job_status):
            count = await _replay_archived_results(
                client, execution, job_id, api_url=api_url, save_dir=save_dir, print_only=print_only
            )
            if count:
                typer.echo(f"Replayed {count} archived stream frame(s).")
                return
            if job_status is not None and str(job_status.state).upper() == "COMPLETED":
                # Archive can be empty while the final Redis frame remains.
                try:
                    final = await client.jobs.get_result(job_id)
                except (NotFoundError, APIError) as exc:
                    if not _archival_fallback_error(exc):
                        raise
                else:
                    typer.echo("No archived stream frames; displaying the final Redis output frame.")
                    _handle_result(final, save_dir=save_dir, print_only=print_only)
                    await _fetch_content_files(execution, final, save_dir, api_url=api_url)
                    return
            typer.echo(f"Job {job_id} is not streaming, and no archived stream output is available.")
            return

        try:
            async for message in client.jobs.stream_results(job_id):
                if isinstance(message, SinapsisSentinel):
                    if message in (SINAPSIS_AGENT_FINISHED, SINAPSIS_END_OF_STREAM):
                        if print_only:
                            typer.echo("Agent has finished.")
                        break
                    continue

                if print_only:
                    _print_result(message)
                else:
                    assert writer is not None
                    written = writer.write(message)
                    if written:
                        typer.echo(f"Saved {len(written)} file(s) to {save_dir}")

                await _fetch_content_files(execution, message, save_dir, api_url=api_url)
        except (NotFoundError, APIError) as exc:
            if not _archival_fallback_error(exc) and not (isinstance(exc, APIError) and exc.status_code == 410):
                raise
            count = await _replay_archived_results(
                client, execution, job_id, api_url=api_url, save_dir=save_dir, print_only=print_only
            )
            if not count:
                raise
            typer.echo(f"Replayed {count} archived stream frame(s).")


async def get_cloud_status(execution: ExecutionContext, job_id: str, *, verbose: bool) -> None:
    """Show the current status of a cloud API job."""
    config = _get_api_config(execution, job_id=job_id)

    async with create_api_client(execution, api_url=config.api_url) as client:
        job_status = await client.jobs.get_status(job_id, verbose=verbose)

    _print_status(job_status)


async def get_cloud_result(
    execution: ExecutionContext, job_id: str, *, refresh: bool, save_dir: Path, print_only: bool
) -> None:
    """Retrieve a cloud API job result."""
    config = _get_api_config(execution, job_id=job_id)

    await _get_cloud_result(
        execution,
        job_id,
        api_url=config.api_url,
        refresh=refresh,
        save_dir=save_dir,
        print_only=print_only,
    )


async def stream_cloud_job(execution: ExecutionContext, job_id: str, *, save_dir: Path, print_only: bool) -> None:
    """Stream results from a cloud API job."""
    config = _get_api_config(execution, job_id=job_id)

    await _stream_cloud_job(execution, job_id, api_url=config.api_url, save_dir=save_dir, print_only=print_only)


async def cancel_cloud_job(execution: ExecutionContext, job_id: str) -> None:
    """Cancel a cloud API job."""
    config = _get_api_config(execution, job_id=job_id)

    async with create_api_client(execution, api_url=config.api_url) as client:
        await client.jobs.cancel(job_id)

    typer.echo(f"Cancelled job {job_id}.")


def _handle_result(result: JobResult, *, save_dir: Path, print_only: bool) -> None:
    """Print or persist a cloud job result, never a control sentinel."""
    if isinstance(result, SinapsisSentinel):
        return
    if print_only:
        _print_result(result)
        return

    writer = ResultWriter(save_dir)
    written = writer.write(result)

    if not written:
        typer.echo("Result contained no output data.")
        return

    typer.echo(f"Saved {len(written)} file(s) to {save_dir}")


def _is_done(status: JobStatus) -> bool:
    """Return whether the authoritative job state is terminal.

    Accept both string values and enum-valued states from older SDKs.
    """
    value = getattr(status.state, "value", status.state)
    state = str(value).rsplit(".", 1)[-1].strip().lower()
    return state in {"done", "completed", "complete", "failed", "error", "cancelled", "canceled"}


def _print_status(status: JobStatus) -> None:
    """Print a cloud job status."""
    typer.echo(f"Job ID:      {status.job_id}")
    typer.echo(f"State:       {status.state}")
    typer.echo(f"Agent:       {status.agent_name or '-'}")
    typer.echo(f"Updated:     {status.updated_at or '-'}")
    typer.echo(f"Heartbeat:   {status.heartbeat or '-'}")
    typer.echo(f"Result URL:  {status.result_url or '-'}")
    typer.echo(f"Error:       {status.error or '-'}")

    if status.agent_def is not None:
        typer.echo()
        typer.echo("Agent definition:")
        typer.echo(status.agent_def)


def _print_result(result: SSEMessage) -> None:
    """Print a human-readable representation of a cloud job result."""
    if isinstance(result, SinapsisSentinel):
        return
    typer.echo(f"Agent:       {result.agent_id}")
    typer.echo(f"Status:      {result.agent_status}")
    typer.echo(f"Timestamp:   {result.timestamp.isoformat()}")

    if result.agent_error:
        typer.echo(f"Error:       {result.agent_error}")

    for entry in result.template_data:
        typer.echo()
        typer.echo(f"Template:    {entry.template_name}")
        typer.echo(f"Status:      {entry.status}")
        typer.echo(f"Timestamp:   {entry.timestamp.isoformat()}")

        if entry.error:
            typer.echo(f"Error:       {entry.error}")

        output = entry.output

        if output is None:
            continue

        typer.echo()
        typer.echo(f"Container:     {output.container_id}")
        typer.echo(f"Images:        {len(output.images)}")
        typer.echo(f"Audios:        {len(output.audios)}")
        typer.echo(f"Texts:         {len(output.texts)}")
        typer.echo(f"Conversations: {len(output.llm_conversations)}")
        typer.echo(f"Files:         {len(output.files)}")
        typer.echo(f"Time series:   {len(output.time_series)}")
        typer.echo(f"Data frames:   {len(output.data_frames)}")
        typer.echo(f"Binary data:   {len(output.binary_data)}")
        typer.echo(f"Generic data:  {len(output.generic_data)}")

    divider(0)


async def _fetch_content_files(execution: ExecutionContext, sse_message, save_dir: Path, *, api_url: str) -> None:
    """Fetch cloud-staged content referenced by an SSE message."""
    if isinstance(sse_message, SinapsisSentinel):
        return
    for agent_response in sse_message.template_data:
        for packet_name in {"images", "texts"}:
            output = agent_response.output
            if output is None:
                continue

            for data_packet in getattr(output, packet_name):
                if not isinstance(data_packet.content, dict):
                    continue

                file_path = data_packet.content.get("content", {}).get("original")

                if file_path is None:
                    continue

                file_path = file_path.split("/")[-1]

                destination = (
                    Path(save_dir)
                    / agent_response.agent_id.replace("/", "_")
                    / agent_response.template_name
                    / file_path
                )

                agent_id = agent_response.agent_id.split("/")[-1]

                await _get_staging_file(
                    agent_id,
                    file_path.strip("/"),
                    destination,
                    execution=execution,
                    api_url=api_url,
                )

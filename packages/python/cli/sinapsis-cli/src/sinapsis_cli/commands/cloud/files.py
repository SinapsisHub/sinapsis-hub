"""File commands for the Sinapsis CLI."""

import asyncio
from pathlib import Path

import typer

from sinapsis_cli.execution import ExecutionContext, create_api_client, get_execution_context

app = typer.Typer(name="files", help="Manage files.", no_args_is_help=True)


@app.command()
def upload(
    ctx: typer.Context,
    file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to the file to upload.",
    ),
) -> None:
    """Upload a file to the selected Sinapsis API profile."""
    asyncio.run(_upload(get_execution_context(ctx), file))


async def _upload(execution: ExecutionContext, file: Path) -> None:
    async with create_api_client(execution) as client:
        result = await client.files.upload(file)

    typer.echo(result)


@app.command()
def get(
    ctx: typer.Context,
    path: str = typer.Argument(..., help="ID of the file to fetch."),
    output: Path = typer.Option(
        ...,
        "--output",
        "-o",
        exists=False,
        file_okay=True,
        dir_okay=False,
        writable=True,
        help="Path where the downloaded file will be saved.",
    ),
) -> None:
    """Fetch a file from the selected Sinapsis API profile."""
    asyncio.run(_get(get_execution_context(ctx), path, output))


async def _get(execution: ExecutionContext, path: str, output: Path) -> None:
    async with create_api_client(execution) as client:
        content = await client.files.get(path)

    output.write_bytes(content)
    typer.echo(f"File saved to {output}")


@app.command("list")
def list_files(ctx: typer.Context, root_path: Path = typer.Argument(default="/", help="Root path.")) -> None:
    """List files for the selected API profile."""
    asyncio.run(_list_files(get_execution_context(ctx), root_path))


async def _list_files(execution: ExecutionContext, root_path: Path) -> None:
    async with create_api_client(execution) as client:
        result = await client.files.list(str(root_path))

    _print_files(result)


def _print_files(result, key_name: str = "entries") -> None:
    for file_entry in result.get(key_name, []):
        typer.echo()
        typer.echo(f"File path:         {file_entry.get('path')}")
        typer.echo(f"File size:         {file_entry.get('size')}")
        typer.echo(f"Last modified:     {file_entry.get('last_modified')}")
        if version := file_entry.get("version"):
            typer.echo(f"Version:           {version}")


@app.command()
def fetch(
    ctx: typer.Context,
    agent_id: str = typer.Argument(..., help="ID for the agent that produced the staging file."),
    file_id: str = typer.Argument(..., help="ID of the file to fetch."),
    output: Path = typer.Option(
        ...,
        "--output",
        "-o",
        exists=False,
        file_okay=True,
        dir_okay=False,
        writable=True,
        help="Path where the downloaded file will be saved.",
    ),
) -> None:
    """Fetch an agent staging file."""
    asyncio.run(_get_staging_file(agent_id, file_id, output, execution=get_execution_context(ctx)))


async def _get_staging_file(
    agent_id: str,
    file_id: str,
    output: Path,
    *,
    execution: ExecutionContext,
    api_url: str | None = None,
) -> None:
    """Fetch an agent staging file from a profile API."""
    async with create_api_client(execution, api_url=api_url) as client:
        content = await client.files.fetch(agent_id, file_id)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(content)
    typer.echo(f"File saved to {output}")


@app.command()
def search(ctx: typer.Context, file_name: str = typer.Argument(..., help="Name of the file to search for.")) -> None:
    """Search for a file in the selected API profile."""
    asyncio.run(_search_file(get_execution_context(ctx), file_name))


async def _search_file(execution: ExecutionContext, file_name: str) -> None:
    async with create_api_client(execution) as client:
        content = await client.files.search(file_name)

    typer.echo()
    typer.echo(f"File search: {content.get('query')}")
    _print_files(content, "matches")

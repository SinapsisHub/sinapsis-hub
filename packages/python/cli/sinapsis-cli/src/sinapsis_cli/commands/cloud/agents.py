"""Explicit saved-agent registration and authenticated version discovery."""

import asyncio
import json
from pathlib import Path
from uuid import UUID

import typer
from sinapsis.agent import load_yaml_config

from sinapsis_cli.execution import ExecutionContext, create_api_client
from sinapsis_cli.state import get_agent_selection, record_agent_selection


def _load_definition(path: Path) -> dict:
    """Forward unmodified YAML; the server's Sinapsis builder validates it."""
    return load_yaml_config(path)


def _show_version(version, *, name: str | None = None) -> None:
    """Never abbreviate UUIDs or rely on terminal-width table rendering."""
    prefix = f"{name} | " if name else ""
    typer.echo(
        f"{prefix}agent={version.agent_id} version_id={version.id} "
        f"label={version.version} created={version.created_at.isoformat()}"
    )


def create_app(execution: ExecutionContext) -> typer.Typer:
    app = typer.Typer(name="agents", help="Register and discover saved Cloud agents.", no_args_is_help=True)

    @app.command("register")
    def register(
        file: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False),
        version: str = typer.Option(..., "--version"),
        name: str | None = typer.Option(None, "--name"),
    ) -> None:
        """Register a reusable agent without starting a job."""
        definition = _load_definition(file)

        async def operation() -> None:
            async with create_api_client(execution) as client:
                registered = await client.agents.register(definition, version=version, name=name)
            record_agent_selection(execution.profile_name, registered.agent_id, registered.agent_version_id)
            typer.echo(f"Agent ID: {registered.agent_id}")
            typer.echo(f"Version ID: {registered.agent_version_id} ({registered.version})")

        asyncio.run(operation())

    @app.command("publish")
    def publish(
        agent_id: UUID = typer.Argument(..., help="Existing saved agent UUID."),
        file: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False),
        version: str = typer.Option(..., "--version"),
    ) -> None:
        """Publish an immutable revision to an already registered agent."""
        definition = _load_definition(file)

        async def operation() -> None:
            async with create_api_client(execution) as client:
                saved = await client.agents.publish(agent_id, definition, version=version)
            record_agent_selection(execution.profile_name, saved.agent_id, saved.id)
            _show_version(saved)

        asyncio.run(operation())

    @app.command("list")
    def list_agents(
        include_all: bool = typer.Option(False, "--all", help="Include execution-created and unaudited legacy agents."),
    ) -> None:
        """List owned, explicitly registered agents by default."""

        async def operation() -> None:
            async with create_api_client(execution) as client:
                offset = 0
                while True:
                    page = await client.agents.list(include_execution=include_all, offset=offset, limit=200)
                    for agent in page:
                        typer.echo(
                            f"{agent.id} | {agent.name} | {agent.registration_source.value} "
                            f"| created={agent.created_at.isoformat()}"
                        )
                    if len(page) < 200:
                        break
                    offset += len(page)

        asyncio.run(operation())

    @app.command("versions")
    def versions(
        agent_id: UUID | None = typer.Argument(None, help="Optional agent UUID; omit to enumerate registered agents."),
        include_all: bool = typer.Option(False, "--all", help="Include execution-created and unaudited legacy agents."),
    ) -> None:
        """List immutable versions with complete UUIDs."""

        async def operation() -> None:
            async with create_api_client(execution) as client:
                if agent_id is not None:
                    found = await client.agents.versions(agent_id)
                    for version in found:
                        _show_version(version)
                    if found:
                        latest = max(found, key=lambda v: (v.created_at, str(v.id)))
                        record_agent_selection(execution.profile_name, agent_id, latest.id)
                else:
                    for agent, rows in await client.agents.all_versions(include_execution=include_all):
                        for version in rows:
                            _show_version(version, name=agent.name)

        asyncio.run(operation())

    @app.command("version")
    def show_version(
        agent_id: UUID | None = typer.Argument(None, help="Agent UUID; defaults to last selection."),
        version_id: UUID | None = typer.Argument(None, help="Version UUID; defaults to last selected or newest."),
    ) -> None:
        """Inspect one saved definition without changing the immutable revision."""
        selected = get_agent_selection(execution.profile_name)
        resolved_agent = agent_id or (selected[0] if selected else None)
        if resolved_agent is None:
            raise typer.BadParameter("No selected agent; specify AGENT_ID or register an agent first")

        async def operation() -> None:
            async with create_api_client(execution) as client:
                if version_id is None and selected and selected[0] == resolved_agent:
                    found = await client.agents.version(resolved_agent, selected[1])
                elif version_id is None:
                    found = await client.agents.latest_version(resolved_agent)
                else:
                    found = await client.agents.version(resolved_agent, version_id)
            record_agent_selection(execution.profile_name, found.agent_id, found.id)
            _show_version(found)
            typer.echo(json.dumps(found.definition, indent=2))

        asyncio.run(operation())

    return app

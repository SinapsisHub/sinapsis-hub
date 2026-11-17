"""Direct local job backend for the Sinapsis CLI."""

import asyncio
from pathlib import Path

import typer

from sinapsis_cli.execution import ExecutionContext
from sinapsis_cli.shared.jobs import register_history_commands


def create_app(execution: ExecutionContext) -> typer.Typer:
    """Create the direct-local jobs command tree.

    Direct local execution is synchronous from the CLI user's perspective, so
    API-specific options such as ``--wait``, ``--result``, ``--stream`` and
    ``--refresh`` are deliberately not registered.

    Args:
        execution: Resolved execution context for the current invocation.

    Returns:
        Typer application containing direct-local job commands.
    """
    app = typer.Typer(
        name="jobs",
        help="Run and manage jobs in the local virtual environment.",
        no_args_is_help=True,
    )

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
        save_dir: Path = typer.Option(
            Path("results"),
            "--save-dir",
            "-o",
            help="Directory where results and artifacts are saved.",
        ),
        print_only: bool = typer.Option(False, "--print-only", help="Print results instead of saving artifacts."),
    ) -> None:
        """Run an agent directly in the selected local environment."""
        asyncio.run(run_local_job(execution, agent_definition, save_dir=save_dir, print_only=print_only))

    register_history_commands(app, execution)
    return app


async def run_local_job(
    execution: ExecutionContext, agent_definition: Path, *, save_dir: Path, print_only: bool
) -> None:
    """Run an agent directly in the configured virtual environment."""
    from sinapsis.agent import AgentMode
    from sinapsis.cli import generic_agent_builder

    agent = generic_agent_builder(agent_definition)

    agent_mode = agent.agent_attributes.agent_mode

    if agent_mode == AgentMode.GENERATOR:
        for result in agent(container=None):
            typer.echo(result)
    else:
        result = agent(container=None)
        typer.echo(result)

    # Successful generator and non-generator executions must leave with status 0.
    # A hard-coded failure made CLI telemetry report successful jobs as errors.
    return

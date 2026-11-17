"""Main entry point for the profile-aware Sinapsis CLI."""

import sys
import time
from typing import Annotated, Any

import rich.box
import typer
import typer.rich_utils
from rich.panel import Panel

from sinapsis_cli.composition import compose_profile_commands, register_global_commands
from sinapsis_cli.config import CLIConfig, get_execution_profile, load_config
from sinapsis_cli.execution import ExecutionContext
from sinapsis_cli.state import migrate_legacy_job_state

state = {"verbose": False}


class BorderlessPanel(Panel):
    """Rich panel that preserves its title without visible borders."""

    def __init__(self, renderable: Any, *args: Any, **kwargs: Any) -> None:
        super().__init__(renderable, *args, **kwargs)
        self.box = rich.box.Box("    \n    \n    \n    \n    \n    \n    \n    \n")


typer.rich_utils.Panel = BorderlessPanel


_PROFILE_PREFIX_FLAGS = {"--verbose", "-v"}


def create_app(execution: ExecutionContext) -> typer.Typer:
    """Create the CLI tree for one resolved execution profile."""
    app = typer.Typer(
        name="sinapsis",
        help=(
            "[bold #00F5FF on #1E1B4B] ⚡ SINAPSIS CLI "
            "[/bold #00F5FF on #1E1B4B]\n\n"
            f"[bold #FF79C6]Profile: {execution.profile_name}. "
            f"({execution.profile.backend.value})[/bold #FF79C6]"
            f"  Use `sinapsis profiles loca|cloud|local-api' to change."
            f"\n\talternatively use `sinapsis local|cloud|local-api' to run with a different profile`"
            "\n\tNOTE: commands available depend on profile being used. "
        ),
        no_args_is_help=True,
        rich_markup_mode="rich",
        pretty_exceptions_show_locals=False,
        subcommand_metavar="[PROFILE] COMMAND [ARGS]...",
    )

    @app.callback()
    def main_callback(
        ctx: typer.Context,
        verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show full traceback on errors.")] = False,
    ) -> None:
        """Run commands using the resolved execution profile."""
        ctx.obj = execution
        state["verbose"] = verbose

    register_global_commands(app, execution)
    compose_profile_commands(app, execution)
    return app


def resolve_invocation(arguments: list[str], *, config: CLIConfig | None = None) -> tuple[ExecutionContext, list[str]]:
    """Resolve an optional positional profile and return remaining CLI args."""
    config = config or load_config()
    migrate_legacy_job_state(config)
    remaining = list(arguments)

    candidate_index = _profile_candidate_index(remaining)
    explicit_profile = False
    profile_name: str | None = None

    if candidate_index is not None:
        candidate = remaining[candidate_index]
        if config.profiles is not None and candidate in config.profiles:
            profile_name = candidate
            del remaining[candidate_index]
            explicit_profile = True

    profile = get_execution_profile(profile_name, config=config)

    return (ExecutionContext(profile=profile, explicit_profile=explicit_profile), remaining)


def _profile_candidate_index(arguments: list[str]) -> int | None:
    """Return the index where an optional profile token may appear."""
    index = 0

    while index < len(arguments) and arguments[index] in _PROFILE_PREFIX_FLAGS:
        index += 1

    if index >= len(arguments):
        return None

    if arguments[index].startswith("-"):
        return None

    return index


def run(arguments: list[str] | None = None, *, prog_name: str = "sinx") -> None:
    """Resolve a profile, run the command, and record only safe opt-in metadata."""
    raw_arguments = list(sys.argv[1:] if arguments is None else arguments)
    started = time.monotonic()
    remaining = raw_arguments
    backend = "other"
    outcome = "error"
    try:
        execution, remaining = resolve_invocation(raw_arguments)
        backend = execution.profile.backend.value
        selected_app = create_app(execution)
        selected_app(args=remaining, prog_name=prog_name)
        outcome = "success"
    except SystemExit as exception:
        outcome = "success" if exception.code in (0, None) else "error"
        raise
    except Exception as exception:
        if state.get("verbose"):
            raise
        typer.secho(f"Error: {exception}", fg=typer.colors.RED, err=True)
        raise SystemExit(1) from exception
    finally:
        # A short-lived CLI must never upload telemetry, scan site-packages,
        # or write SQLite from the execution thread.  A detached *local*
        # collector receives only allowlisted metadata (never raw arguments).
        try:
            from sinapsis_cli.telemetry.collector import spawn_collector

            spawn_collector(remaining, backend=backend, outcome=outcome,
                            duration_ms=int((time.monotonic()-started)*1000),
                            venv=execution.profile.venv if 'execution' in locals() else None)
        except Exception:  # noqa: BLE001
            pass  # Optional telemetry must not alter command behavior.


def main() -> None:
    try:
        run(prog_name="sinx")
    except Exception as e:
        if state.get("verbose"):
            raise e
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        sys.exit(1)


def main_cloud() -> None:
    try:
        run(["cloud", *sys.argv[1:]], prog_name="sinx-cloud")
    except Exception as e:
        if state.get("verbose"):
            raise e
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        sys.exit(1)


def main_local_venv() -> None:
    try:
        run(["local", *sys.argv[1:]], prog_name="sinx-venv")
    except Exception as e:
        if state.get("verbose"):
            raise e
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        sys.exit(1)


def main_local_api() -> None:
    try:
        run(["local-api", *sys.argv[1:]], prog_name="sinx-api")
    except Exception as e:
        if state.get("verbose"):
            raise e
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        sys.exit(1)


# # Compatibility for callers that import ``sinapsis_cli.main:app`` directly.
# app = create_app(ExecutionContext(profile=get_execution_profile()))


if __name__ == "__main__":
    main()

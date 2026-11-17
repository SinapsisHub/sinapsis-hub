"""Profile-driven CLI command composition."""

from collections.abc import Callable
from dataclasses import dataclass

import typer

from sinapsis_cli.config import ExecutionBackend
from sinapsis_cli.execution import ExecutionContext

AUTH_PANEL = "\n[bold #00F5FF on #2E1065] 🔐 AUTHENTICATION [/bold #00F5FF on #2E1065]"
CORE_PANEL = "\n[bold #00F5FF on #2E1065] ⚡ CORE SERVICES [/bold #00F5FF on #2E1065]"
DEV_PANEL = "\n[bold #00F5FF on #2E1065] 🛠️ DEVELOPER TOOLS [/bold #00F5FF on #2E1065]"
SEC_PANEL = "\n[bold #00F5FF on #2E1065] 🛡️ SECURITY & KEYS [/bold #00F5FF on #2E1065]"
CONFIG_PANEL = "\n[bold #00F5FF on #2E1065] ⚙️ CONFIGURATION [/bold #00F5FF on #2E1065]"


RegisterCommand = Callable[[typer.Typer, ExecutionContext], None]


@dataclass(frozen=True)
class CommandProvider:
    """A named command-tree contribution that can be composed into a profile."""

    name: str
    register: RegisterCommand


def _register_local_venv_jobs(app: typer.Typer, execution: ExecutionContext) -> None:
    """Register the local virtual-environment jobs command."""
    from sinapsis_cli.commands.local_venv.jobs import create_app as create_jobs_app

    app.add_typer(create_jobs_app(execution), name="jobs", rich_help_panel=CORE_PANEL)


def _register_local_api_jobs(app: typer.Typer, execution: ExecutionContext) -> None:
    """Register the local API jobs command."""
    from sinapsis_cli.commands.local_api.jobs import create_app as create_jobs_app

    app.add_typer(create_jobs_app(execution), name="jobs", rich_help_panel=CORE_PANEL)


def _register_cloud_agents(app: typer.Typer, execution: ExecutionContext) -> None:
    """Register Cloud saved-agent discovery and version management."""
    from sinapsis_cli.commands.cloud.agents import create_app

    app.add_typer(create_app(execution), name="agents", rich_help_panel=CORE_PANEL)


def _register_cloud_jobs(app: typer.Typer, execution: ExecutionContext) -> None:
    """Register the cloud jobs command."""
    from sinapsis_cli.commands.cloud.jobs import create_app as create_jobs_app

    app.add_typer(create_jobs_app(execution), name="jobs", rich_help_panel=CORE_PANEL)


def _register_templates(app: typer.Typer, execution: ExecutionContext) -> None:
    """Register local virtual-environment template commands."""
    del execution

    from sinapsis_cli.commands.local_venv import templates

    app.add_typer(templates.app, name="templates", rich_help_panel=CORE_PANEL)


def _register_cloud_templates(app: typer.Typer, execution: ExecutionContext) -> None:
    """Register public user-facing Cloud catalog commands."""
    del execution
    from sinapsis_cli.commands.cloud import templates

    app.add_typer(templates.app, name="templates", rich_help_panel=CORE_PANEL)


def _register_files(app: typer.Typer, execution: ExecutionContext) -> None:
    """Register cloud file commands."""
    del execution

    from sinapsis_cli.commands.cloud import files

    app.add_typer(files.app, name="files", rich_help_panel=CORE_PANEL)


def _register_webhooks(app: typer.Typer, execution: ExecutionContext) -> None:
    """Register cloud webhook commands."""
    del execution

    from sinapsis_cli.commands.cloud import webhooks

    app.add_typer(webhooks.app, name="webhooks", rich_help_panel=DEV_PANEL)


def _register_api_keys(app: typer.Typer, execution: ExecutionContext) -> None:
    """Register cloud API key commands."""
    del execution

    from sinapsis_cli.commands.cloud import api_keys

    app.add_typer(api_keys.app, name="api-keys", rich_help_panel=SEC_PANEL)


def _register_packages(app: typer.Typer, execution: ExecutionContext) -> None:
    """Provide native uv credential integration for Cloud users."""
    del execution
    from sinapsis_cli.commands.cloud import packages
    app.add_typer(packages.app, name="packages", rich_help_panel=DEV_PANEL)


def _register_secrets(app: typer.Typer, execution: ExecutionContext) -> None:
    """Register cloud secret commands."""
    del execution

    from sinapsis_cli.commands.cloud import secrets

    app.add_typer(secrets.app, name="secrets", rich_help_panel=SEC_PANEL)


_COMMAND_PROVIDERS: dict[str, CommandProvider] = {
    "local-venv.jobs": CommandProvider("local-venv.jobs", _register_local_venv_jobs),
    "local-venv.templates": CommandProvider("local-venv.templates", _register_templates),
    "local-api.jobs": CommandProvider("local-api.jobs", _register_local_api_jobs),
    "cloud.jobs": CommandProvider("cloud.jobs", _register_cloud_jobs),
    "cloud.agents": CommandProvider("cloud.agents", _register_cloud_agents),
    "cloud.templates": CommandProvider("cloud.templates", _register_cloud_templates),
    "cloud.files": CommandProvider("cloud.files", _register_files),
    "cloud.webhooks": CommandProvider("cloud.webhooks", _register_webhooks),
    "cloud.api-keys": CommandProvider("cloud.api-keys", _register_api_keys),
    "cloud.packages": CommandProvider("cloud.packages", _register_packages),
    "cloud.secrets": CommandProvider("cloud.secrets", _register_secrets),
}


_BASE_COMMAND_SETS: dict[ExecutionBackend, tuple[str, ...]] = {
    ExecutionBackend.LOCAL_VENV: ("local-venv.jobs", "local-venv.templates"),
    ExecutionBackend.LOCAL_API: ("local-api.jobs",),
    ExecutionBackend.CLOUD: (
        "cloud.jobs",
        "cloud.agents",
        "cloud.templates",
        "cloud.files",
        "cloud.webhooks",
        "cloud.api-keys",
        "cloud.packages",
        "cloud.secrets",
    ),
}


def register_command_provider(provider: CommandProvider) -> None:
    """Register an additive command provider.

    Args:
        provider: Command provider to register.

    Raises:
        ValueError: If a provider with the same name is already registered.
    """
    if provider.name in _COMMAND_PROVIDERS:
        raise ValueError(f"Command provider {provider.name!r} is already registered.")

    _COMMAND_PROVIDERS[provider.name] = provider


def register_global_commands(app: typer.Typer, execution: ExecutionContext) -> None:
    """Register commands that manage the CLI rather than an execution backend."""
    del execution

    from sinapsis_cli.commands.common import auth, profiles, telemetry

    app.command(name="configure", rich_help_panel=AUTH_PANEL)(auth.configure)

    app.add_typer(profiles.app, name="profiles", rich_help_panel=CONFIG_PANEL)

    config_app = typer.Typer(name="config", help="Configure local Sinapsis CLI features.", no_args_is_help=True)
    config_app.add_typer(telemetry.app, name="telemetry")
    app.add_typer(config_app, name="config", rich_help_panel=CONFIG_PANEL)


def compose_profile_commands(app: typer.Typer, execution: ExecutionContext) -> None:
    """Compose the command tree for a selected profile.

    The selected backend contributes its base command providers. Additional
    providers configured on the profile are then appended, allowing profiles
    to extend a backend without modifying its base command tree.

    Args:
        app: Root Typer application.
        execution: Resolved execution context for the selected profile.

    Raises:
        ValueError: If the backend has no registered command set or the profile
            references an unknown additive command provider.
    """
    try:
        base_provider_names = _BASE_COMMAND_SETS[execution.profile.backend]
    except KeyError as exception:
        raise ValueError(
            f"No command composition is registered for backend {execution.profile.backend.value!r}."
        ) from exception

    provider_names = [*base_provider_names, *execution.profile.command_sets]

    for provider_name in dict.fromkeys(provider_names):
        try:
            provider = _COMMAND_PROVIDERS[provider_name]
        except KeyError as exception:
            raise ValueError(
                f"Profile {execution.profile_name!r} references unknown command set {provider_name!r}."
            ) from exception

        provider.register(app, execution)


def command_provider_names() -> tuple[str, ...]:
    """Return the currently registered provider names."""
    return tuple(_COMMAND_PROVIDERS)

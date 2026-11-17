"""Authentication and interactive profile configuration commands."""

import asyncio

import click
import typer
from sinapsis.logging import sinapsis_logger
from sinapsis_sdk.cloud_api._auth import AuthManager
from sinapsis_sdk.cloud_api._config import ConfigStore
from sinapsis_sdk.cloud_api._credentials import create_credential_store
from sinapsis_sdk.cloud_api.cloud_config import CloudAPIConfig

from sinapsis_cli.config import (
    DEFAULT_CLOUD_URL,
    DEFAULT_LOCAL_URL,
    DEFAULT_VENV,
    CLIConfig,
    ExecutionBackend,
    Profile,
    load_config,
    save_config,
)
from sinapsis_cli.execution import ExecutionContext, get_execution_context


def configure(
    ctx: typer.Context,
    profile: str | None = typer.Option(None, "--profile", "-p", help="Configure a specific profile."),
    all_profiles: bool = typer.Option(False, "--all-profiles", help="Configure every defined profile."),
) -> None:
    """Configure Sinapsis execution profiles.

    With an explicitly selected positional profile, that profile is configured.
    Without one, the command preserves the previous behavior and configures all
    profiles unless ``--profile`` chooses a specific profile.
    """
    execution = get_execution_context(ctx)

    if profile is not None and all_profiles:
        raise typer.BadParameter("--profile and --all-profiles are mutually exclusive.")

    asyncio.run(_configure(execution=execution, profile_name=profile, all_profiles=all_profiles))


async def _configure(*, execution: ExecutionContext, profile_name: str | None, all_profiles: bool) -> None:
    """Configure one or more Sinapsis execution profiles."""
    cli_config = load_config()
    assert cli_config.profiles is not None

    if profile_name is not None:
        names = [cli_config.get_profile(profile_name).name]
    elif execution.explicit_profile and not all_profiles:
        names = [execution.profile_name]
    else:
        names = list(cli_config.profiles)

    typer.echo("Sinapsis configuration")
    typer.echo()

    for name in names:
        await _configure_profile(cli_config, name)

    if len(names) > 1:
        _configure_default(cli_config)

    save_config(cli_config)

    typer.echo()
    typer.echo("Configuration complete.")
    typer.echo(f"Default profile: {cli_config.default_profile}")


async def _configure_profile(cli_config: CLIConfig, profile_name: str) -> None:
    """Configure one profile according to its execution backend."""
    profile = cli_config.get_profile(profile_name)

    if profile.backend is ExecutionBackend.LOCAL_VENV:
        _configure_local_venv(cli_config, profile)
        return

    if profile.backend is ExecutionBackend.LOCAL_API:
        _configure_local_api(cli_config, profile)
        return

    if profile.backend is ExecutionBackend.CLOUD:
        await _configure_cloud(cli_config, profile)
        return

    raise RuntimeError(f"No profile configurator for backend {profile.backend.value!r}.")


def _configure_local_venv(cli_config: CLIConfig, profile: Profile) -> None:
    """Configure local virtual-environment execution."""
    assert cli_config.profiles is not None

    typer.echo(f"Local execution [{profile.name}]")
    typer.echo("-" * (18 + len(profile.name)))

    venv = typer.prompt("Virtual environment", default=profile.venv or DEFAULT_VENV)

    cli_config.profiles[profile.name] = Profile(
        name=profile.name,
        backend=profile.backend,
        venv=venv,
        authenticated=False,
        command_sets=profile.command_sets,
    )
    typer.echo()


async def _configure_cloud(cli_config: CLIConfig, profile: Profile) -> None:
    """Configure cloud execution and authenticate the user."""
    assert cli_config.profiles is not None

    typer.echo(f"Cloud API [{profile.name}]")
    typer.echo("-" * (12 + len(profile.name)))

    api_url = typer.prompt("Cloud API URL", default=profile.api_url or DEFAULT_CLOUD_URL).rstrip("/")

    cli_config.profiles[profile.name] = Profile(
        name=profile.name,
        backend=profile.backend,
        api_url=api_url,
        authenticated=True,
        command_sets=profile.command_sets,
    )

    current_api_config = ConfigStore().load()
    api_config = CloudAPIConfig(api_url=api_url, timeout=current_api_config.timeout)

    typer.echo()
    typer.echo("Cloud authentication")
    typer.echo()

    credential_store = create_credential_store()
    auth = AuthManager(api_config, credential_store)

    try:
        await _configure_supabase(auth)
    finally:
        await auth.aclose()

    typer.echo()


def _configure_local_api(cli_config: CLIConfig, profile: Profile) -> None:
    """Configure local API execution."""
    assert cli_config.profiles is not None

    typer.echo(f"Local API [{profile.name}]")
    typer.echo("-" * (12 + len(profile.name)))

    api_url = typer.prompt("Local API URL", default=profile.api_url or DEFAULT_LOCAL_URL).rstrip("/")

    cli_config.profiles[profile.name] = Profile(
        name=profile.name,
        backend=profile.backend,
        api_url=api_url,
        authenticated=False,
        command_sets=profile.command_sets,
    )
    typer.echo()


def _configure_default(cli_config: CLIConfig) -> None:
    """Configure the default execution profile."""
    assert cli_config.profiles is not None

    names = list(cli_config.profiles)
    typer.echo("Default execution profile")
    typer.echo("-------------------------")
    typer.echo()

    for index, name in enumerate(names, start=1):
        profile = cli_config.profiles[name]
        typer.echo(f"{index}. {name} ({profile.backend.value})")

    current_index = names.index(cli_config.default_profile) + 1 if cli_config.default_profile in names else 1

    choice = typer.prompt("Choose default profile", default=current_index, type=click.IntRange(min=1, max=len(names)))

    cli_config.default_profile = names[choice - 1]


async def _configure_supabase(auth: AuthManager, *, max_attempts: int = 3) -> None:
    """Authenticate the cloud profile through the Cloud API.

    Args:
        auth: Authentication manager used to perform the login.
        max_attempts: Maximum number of authentication attempts.

    Raises:
        typer.Exit: If authentication fails after all attempts.
        ValueError: If ``max_attempts`` is less than one.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be greater than zero.")

    for attempt in range(1, max_attempts + 1):
        email = typer.prompt("Email")
        password = typer.prompt("Password", hide_input=True)

        try:
            await auth.login(email, password)
            return
        except Exception as exception:
            sinapsis_logger.warning("Cloud authentication attempt {}/{} failed: {}", attempt, max_attempts, exception)

            attempts_remaining = max_attempts - attempt

            if attempts_remaining:
                typer.echo(
                    f"Login failed. {attempts_remaining} attempt{'s' if attempts_remaining != 1 else ''} remaining.",
                    err=True,
                )
                continue

            typer.echo(f"Login failed after {max_attempts} attempts.", err=True)
            raise typer.Exit(code=1) from exception

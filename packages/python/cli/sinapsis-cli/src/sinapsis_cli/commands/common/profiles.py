"""Execution profile management commands."""

import typer

from sinapsis_cli.config import (
    DEFAULT_CLOUD_URL,
    DEFAULT_LOCAL_URL,
    DEFAULT_VENV,
    ExecutionBackend,
    Profile,
    delete_profile,
    load_config,
    set_default_profile,
    set_profile,
    validate_backend,
    validate_profile_name,
)

app = typer.Typer(name="profiles", help="Manage Sinapsis execution profiles.", no_args_is_help=True)


_RESERVED_PROFILE_NAMES = {
    "configure",
    "profiles",
    "jobs",
    "templates",
    "files",
    "webhooks",
    "api-keys",
    "secrets",
    "api",
    "version",
}


def _validate_new_profile_name(name: str) -> str:
    normalized = validate_profile_name(name)

    if normalized in _RESERVED_PROFILE_NAMES:
        raise typer.BadParameter(f"Profile name {normalized!r} is reserved by the CLI.")

    return normalized


@app.command("list")
def list_profiles() -> None:
    """List configured execution profiles."""
    config = load_config()
    assert config.profiles is not None

    for name in sorted(config.profiles):
        profile = config.profiles[name]
        marker = "*" if name == config.default_profile else " "
        target = profile.api_url or profile.venv or "-"
        extras = ",".join(profile.command_sets) or "-"
        typer.echo(f"{marker} {name:16} {profile.backend.value:12} {target}  extras={extras}")


@app.command()
def show(name: str = typer.Argument(..., help="Profile name.")) -> None:
    """Show one execution profile."""
    profile = load_config().get_profile(name)

    typer.echo(f"Name:          {profile.name}")
    typer.echo(f"Backend:       {profile.backend.value}")
    typer.echo(f"API URL:       {profile.api_url or '-'}")
    typer.echo(f"Virtual env:   {profile.venv or '-'}")
    typer.echo(f"Authenticated: {profile.authenticated}")
    typer.echo("Command sets:  " + (", ".join(profile.command_sets) or "-"))


@app.command()
def create(
    name: str = typer.Argument(..., help="Profile name."),
    backend: str = typer.Option(..., "--backend", "-b", help="Execution backend: local-venv, local-api, or cloud."),
    api_url: str | None = typer.Option(None, "--api-url", help="API URL for API-backed profiles."),
    venv: str | None = typer.Option(None, "--venv", help="Virtual environment for local-venv profiles."),
    command_set: list[str] | None = typer.Option(
        None,
        "--command-set",
        help="Additional command-set provider. Repeat for multiple providers.",
    ),
) -> None:
    """Create or replace an execution profile."""
    normalized_name = _validate_new_profile_name(name)

    try:
        resolved_backend = validate_backend(backend)
    except ValueError as exception:
        raise typer.BadParameter(str(exception), param_hint="--backend") from exception

    if resolved_backend is ExecutionBackend.CLOUD:
        resolved_api_url = (api_url or DEFAULT_CLOUD_URL).rstrip("/")
        resolved_venv = None
        authenticated = True
    elif resolved_backend is ExecutionBackend.LOCAL_API:
        resolved_api_url = (api_url or DEFAULT_LOCAL_URL).rstrip("/")
        resolved_venv = None
        authenticated = False
    else:
        resolved_api_url = None
        resolved_venv = venv or DEFAULT_VENV
        authenticated = False

    requested_command_sets = tuple(command_set or ())
    if requested_command_sets:
        from sinapsis_cli.composition import command_provider_names

        available = set(command_provider_names())
        unknown = [name for name in requested_command_sets if name not in available]
        if unknown:
            raise typer.BadParameter(
                "Unknown command set(s): " + ", ".join(sorted(unknown)), param_hint="--command-set"
            )

    profile = Profile(
        name=normalized_name,
        backend=resolved_backend,
        api_url=resolved_api_url,
        venv=resolved_venv,
        authenticated=authenticated,
        command_sets=requested_command_sets,
    )

    set_profile(profile)
    typer.echo(f"Profile {normalized_name!r} saved.")


@app.command("default")
def set_default(
    name: str = typer.Argument(..., help="Profile to use when none is specified."),
) -> None:
    """Set the default execution profile."""
    try:
        set_default_profile(name)
    except ValueError as exception:
        raise typer.BadParameter(str(exception), param_hint="name") from exception

    typer.echo(f"Default profile changed to {name!r}.")


@app.command()
def delete(
    name: str = typer.Argument(..., help="Profile name."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Delete without prompting for confirmation."),
) -> None:
    """Delete an execution profile."""
    if not yes and not typer.confirm(f"Delete profile {name!r}?"):
        raise typer.Abort()

    try:
        delete_profile(name)
    except ValueError as exception:
        raise typer.BadParameter(str(exception), param_hint="name") from exception

    typer.echo(f"Deleted profile {name!r}.")

"""Transparent, opt-in Sinapsis CLI telemetry controls."""

import json
from pathlib import Path

import typer

from sinapsis_cli.config import ExecutionBackend
from sinapsis_cli.execution import get_execution_context
from sinapsis_cli.telemetry.core import (
    clear_events,
    collection_enabled,
    data_fields,
    inventory_snapshot,
    override_state,
    recent_events,
    record_inventory_if_due,
    set_consent,
    stored_consent,
)
from sinapsis_cli.telemetry.transport import publish_pending, queue_status
from sinapsis_cli.telemetry.scheduler import install_scheduler, remove_scheduler, scheduler_status

app = typer.Typer(name="telemetry", no_args_is_help=True, help="Control and inspect optional CLI telemetry.")


def _selected_venv(ctx: typer.Context) -> Path | None:
    """Use the selected invocation profile, never the host of a local API."""
    profile = get_execution_context(ctx).profile
    if profile.backend is ExecutionBackend.LOCAL_VENV and profile.venv:
        return Path(profile.venv).expanduser().resolve()
    return None


def _print_json(value: object) -> None:
    typer.echo(json.dumps(value, indent=2, sort_keys=True))


@app.command()
def status() -> None:
    """Show effective consent, overrides, local history, and delivery status."""
    typer.echo(f"Collection: {'enabled' if collection_enabled() else 'disabled'}")
    typer.echo(f"Stored consent: {'enabled' if stored_consent() else 'disabled'}")
    typer.echo(f"SINAPSIS_TELEMETRY override: {override_state() if override_state() is not None else 'unset'}")
    typer.echo(f"Local events retained: {len(recent_events(200))}")
    delivery = queue_status()
    schedule = scheduler_status()
    typer.echo(f"Hourly background publisher: {schedule['status']} ({schedule['provider']})")
    typer.echo(f"Pending events: {delivery['pending']}")
    typer.echo(f"Acknowledged events: {delivery['sent']}")
    typer.echo(f"Last transmission: {delivery['last_sent']['acknowledged_at'] if delivery['last_sent'] else 'none'}")


@app.command()
def enable(ctx: typer.Context) -> None:
    """Opt in and install an independent hourly OS-level telemetry publisher."""
    try:
        install_scheduler()
    except (OSError, RuntimeError, ValueError) as error:
        # Never claim consent/publishing is enabled when scheduling failed.
        set_consent(False)
        typer.secho(f"Unable to enable automatic telemetry: {error}", err=True, fg=typer.colors.RED)
        raise typer.Exit(1) from error
    set_consent(True)
    # An initial inventory is explicitly requested here (not a normal job).
    recorded = record_inventory_if_due(venv=_selected_venv(ctx), force=True)
    typer.echo("Telemetry enabled. Automatic publishing scheduled hourly.")
    typer.echo("Environment inventory recorded." if recorded else "Inventory will be collected by the scheduler.")
    if override_state() == "0":
        typer.echo("SINAPSIS_TELEMETRY=0 currently suppresses collection in this process.")
    typer.echo("Use `sinx config telemetry info` to inspect the exact payloads.")


@app.command()
def disable(
    clear: bool = typer.Option(False, "--clear", help="Also delete locally retained events."),
) -> None:
    """Opt out; optionally delete locally collected event history."""
    set_consent(False)
    try:
        remove_scheduler()
    except (OSError, RuntimeError) as error:
        typer.secho(f"WARNING: Could not remove OS scheduler: {error}", fg=typer.colors.YELLOW, err=True)
    deleted = clear_events() if clear else None
    typer.echo("Stored telemetry consent disabled.")
    if override_state() == "1":
        typer.echo("WARNING: SINAPSIS_TELEMETRY=1 currently overrides this setting.")
    if deleted is not None:
        typer.echo(f"Deleted {deleted} local events.")


@app.command()
def info() -> None:
    """List all collected fields and display the most recent actual event."""
    status()
    typer.echo("\nFields collected (never raw CLI arguments or files):")
    for field, meaning in data_fields().items():
        typer.echo(f"  {field}: {meaning}")
    events = recent_events(1)
    typer.echo("\nLast locally collected event:")
    if events:
        _print_json(events[0])
    else:
        typer.echo("None. Run `sinx config telemetry preview` for an unsaved example.")
    typer.echo("\nLast successfully transmitted payload:")
    _print_json(queue_status()['last_sent'])


@app.command()
def preview(ctx: typer.Context) -> None:
    """Show an inventory example without collecting or persisting an event."""
    typer.echo("Environment inventory preview (NOT stored or transmitted):")
    _print_json(inventory_snapshot(venv=_selected_venv(ctx)))


@app.command()
def inventory(ctx: typer.Context) -> None:
    """Record a current environment snapshot when telemetry consent is enabled."""
    if not collection_enabled():
        typer.echo("Telemetry is disabled. Use `sinx config telemetry preview` without opting in.")
        return
    recorded = record_inventory_if_due(venv=_selected_venv(ctx), force=True)
    typer.echo("Environment inventory recorded." if recorded else "Could not record environment inventory.")
    typer.echo("Queued events are sent automatically by the hourly background publisher.")


@app.command()
def history(limit: int = typer.Option(10, "--limit", min=1, max=200)) -> None:
    """Inspect recent locally collected telemetry payloads, newest first."""
    _print_json(recent_events(limit))


@app.command()
def clear(yes: bool = typer.Option(False, "--yes", "-y")) -> None:
    """Delete all local telemetry events (does not change consent)."""
    if not yes and not typer.confirm("Delete all locally retained telemetry events?"):
        raise typer.Abort()
    typer.echo(f"Deleted {clear_events()} local events.")


@app.command('last-sent')
def last_sent() -> None:
    """Display the actual acknowledged payload and server-acceptance timestamp."""
    _print_json(queue_status()['last_sent'])


@app.command('send')
def send() -> None:
    """Diagnostic only: the OS scheduler publishes hourly without CLI use."""
    typer.echo(f"Acknowledged {publish_pending()} events.")

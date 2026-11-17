"""API key commands for the Sinapsis CLI."""

import asyncio
import re
from datetime import UTC, datetime, timedelta

import typer
from sinapsis_contracts.cloud_api.models.api_key_permissions import ApiKeyPermission

from sinapsis_cli.execution import ExecutionContext, create_api_client, get_execution_context

app = typer.Typer(name="api-keys", help="Manage API keys.", no_args_is_help=True)


_EXPIRATION_DURATION = re.compile(r"(?P<quantity>[1-9][0-9]*)(?P<unit>[dhm])", re.IGNORECASE)


def _parse_expiration(value: str | None) -> datetime | None:
    """Parse a relative duration or an absolute, timezone-aware ISO timestamp.

    The server remains authoritative for validity and maximum lifetime.
    """
    if value is None:
        return None  # Management's existing 90-day default.

    value = value.strip()
    match = _EXPIRATION_DURATION.fullmatch(value)
    if match:
        try:
            quantity = int(match.group("quantity"))
            unit = match.group("unit").lower()
            duration = timedelta(seconds=quantity * {"d": 86400, "h": 3600, "m": 60}[unit])
            return datetime.now(UTC) + duration
        except (OverflowError, ValueError):
            raise typer.BadParameter("Expiration duration is too large") from None

    try:
        expires_at = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise typer.BadParameter(
            "Use a duration such as 7d, 12h, 30m, or an ISO 8601 timestamp "
            "with a timezone (e.g. 2026-12-01T09:00:00+00:00)"
        ) from None
    if expires_at.utcoffset() is None:
        raise typer.BadParameter("Absolute expiration must include a timezone offset")
    return expires_at


@app.command("permissions")
def permissions() -> None:
    """List valid --scope values without requiring an API connection."""
    for permission in ApiKeyPermission:
        typer.echo(permission.value)


@app.command()
def create(
    ctx: typer.Context,
    name: str = typer.Option(..., prompt=True),
    scope: list[str] | None = typer.Option(
        None, "--scope", help="Repeat for each scope, e.g. files:read (see api-keys permissions)."
    ),
    agent_id: list[str] | None = typer.Option(None, "--agent-id", help="Allowed agent UUID; repeatable."),
    all_user_agents: bool = typer.Option(False, "--all-user-agents", help="Dynamically allow owned agents."),
    expire: str | None = typer.Option(
        None,
        "--expire",
        help="Expiry: 7d, 12h, 30m, or timezone-aware ISO 8601. Defaults to 90d; max 365d.",
    ),
) -> None:
    """Create a scoped API key; its secret is shown only once."""
    expires_at = _parse_expiration(expire)
    asyncio.run(
        _create_key(
            get_execution_context(ctx),
            name,
            scope,
            agent_id,
            all_user_agents,
            expires_at=expires_at,
        )
    )


async def _create_key(
    execution: ExecutionContext,
    name: str,
    scope: list[str] | None = None,
    agent_id: list[str] | None = None,
    all_user_agents: bool = False,
    *,
    expires_at: datetime | None = None,
) -> None:
    async with create_api_client(execution) as client:
        response = await client.api_keys.generate(
            name,
            scopes=scope,
            agent_ids=agent_id or [],
            all_user_agents=all_user_agents,
            expires_at=expires_at,
        )
    typer.echo(f"API Key {response.api_key_name!r} created (ID: {response.metadata.id}).")
    expires = response.metadata.expires_at
    typer.echo(f"Expires: {expires.isoformat() if expires else 'not specified'}")
    typer.echo("Copy this secret now; it cannot be retrieved later:")
    typer.echo(response.api_key)


@app.command()
def copy(ctx: typer.Context, masked_api_key: str = typer.Option(..., prompt=True)) -> None:
    """Explain why existing API key values cannot be retrieved."""
    asyncio.run(_copy_key(get_execution_context(ctx), masked_api_key))


async def _copy_key(execution: ExecutionContext, masked_api_key: str) -> None:
    del execution, masked_api_key
    typer.echo(
        "API key values are only shown at creation. Create a replacement key and revoke the old one.",
        err=True,
    )
    raise typer.Exit(code=1)


@app.command("list")
def list_keys(ctx: typer.Context) -> None:
    """List active API keys."""
    asyncio.run(_list_keys(get_execution_context(ctx)))


async def _list_keys(execution: ExecutionContext) -> None:
    async with create_api_client(execution) as client:
        key_list = await client.api_keys.list_all()

    for key in key_list.keys:
        expires = key.expires_at.isoformat() if key.expires_at else "not specified"
        typer.echo(
            f"Name: {key.name}   ID: {key.id}   Key: {key.api_key}   "
            f"Scopes: {', '.join(key.scopes)}   Expires: {expires}"
        )


@app.command()
def delete(ctx: typer.Context, key_id: str = typer.Option(..., prompt=True)) -> None:
    """Delete an API key."""
    if not typer.confirm(f"Delete API key {key_id!r}?"):
        raise typer.Abort()

    asyncio.run(_delete(get_execution_context(ctx), key_id))


async def _delete(execution: ExecutionContext, key_id: str) -> None:
    async with create_api_client(execution) as client:
        await client.api_keys.delete(key_id)

    typer.echo(f"Deleted API key: {key_id}")

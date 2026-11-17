"""Webhook commands for the Sinapsis CLI."""

import asyncio
import json
from uuid import UUID

import typer
from sinapsis_contracts.cloud_api.models.webhooks.payloads import RegisterWebhookRequest
from sinapsis_contracts.cloud_api.models.webhooks.responses import RegisteredWebhookItem

from sinapsis_cli.execution import ExecutionContext, create_api_client, get_execution_context

from ._webhook_render import print_webhooks

app = typer.Typer(name="webhooks", help="Manage webhook integrations.", no_args_is_help=True)


@app.command()
def register(
    ctx: typer.Context,
    integration_name: str = typer.Argument(..., help="Name for the webhook integration."),
    provider: str = typer.Option(..., "--provider", "-p", help="Webhook provider."),
    credential_id: UUID | None = typer.Option(None, "--credential-id", help="Credential ID used by the provider."),
    enforce_schema: bool = typer.Option(
        False, "--enforce-schema", help="Require incoming payloads to match the expected schema."
    ),
    expected_schema: str | None = typer.Option(
        None, "--expected-schema", help="JSON schema used to validate incoming payloads."
    ),
) -> None:
    """Register a webhook integration."""
    asyncio.run(
        _register(
            execution=get_execution_context(ctx),
            integration_name=integration_name,
            provider=provider,
            credential_id=credential_id,
            enforce_schema=enforce_schema,
            expected_schema=expected_schema,
        )
    )


async def _register(
    *,
    execution: ExecutionContext,
    integration_name: str,
    provider: str,
    credential_id: UUID | None,
    enforce_schema: bool,
    expected_schema: str | None,
) -> None:
    payload_data: dict[str, object] = {
        "integration_name": integration_name,
        "provider": provider,
        "credential_id": credential_id,
        "enforce_schema": enforce_schema,
    }

    if expected_schema is not None:
        payload_data["expected_schema"] = json.loads(expected_schema)

    payload = RegisterWebhookRequest.model_validate(payload_data)

    async with create_api_client(execution) as client:
        webhook: RegisteredWebhookItem = await client.webhooks.register(payload)

    typer.echo(f"Created webhook: {webhook.webhook_id}")
    typer.echo(f"Name:           {webhook.integration_name}")
    typer.echo(f"Provider:       {webhook.provider}")
    typer.echo(f"Active:         {webhook.is_active}")
    typer.echo(f"Public URL:     {webhook.webhook_url}")


@app.command("list")
def list_webhooks(ctx: typer.Context) -> None:
    """List registered webhook integrations."""
    asyncio.run(_list_webhooks(get_execution_context(ctx)))


async def _list_webhooks(execution: ExecutionContext) -> None:
    async with create_api_client(execution) as client:
        webhooks = await client.webhooks.list_user_webhooks()

    if not webhooks:
        typer.echo("No webhook integrations found.")
        return

    print_webhooks(webhooks)


@app.command("show")
def show_webhook(
    ctx: typer.Context,
    webhook_id: UUID = typer.Argument(..., help="ID of the webhook integration."),
) -> None:
    """Show one webhook integration's configuration and public URL."""
    asyncio.run(_show_webhook(get_execution_context(ctx), webhook_id))


async def _show_webhook(execution: ExecutionContext, webhook_id: UUID) -> None:
    async with create_api_client(execution) as client:
        webhook = await client.webhooks.get(webhook_id)
    typer.echo(webhook.model_dump_json(indent=2))
    typer.echo(f"Public URL: {webhook.webhook_url}")


@app.command()
def delete(
    ctx: typer.Context,
    webhook_id: UUID = typer.Argument(..., help="ID of the webhook integration."),
) -> None:
    """Delete a webhook integration."""
    if not typer.confirm(f"Delete webhook {webhook_id!r}?"):
        raise typer.Abort()

    asyncio.run(_delete(get_execution_context(ctx), webhook_id))


async def _delete(execution: ExecutionContext, webhook_id: UUID) -> None:
    async with create_api_client(execution) as client:
        result = await client.webhooks.delete(str(webhook_id))

    typer.echo(result.message)


@app.command()
def toggle(
    ctx: typer.Context,
    webhook_id: UUID = typer.Argument(..., help="ID of the webhook integration."),
    active: bool = typer.Option(..., "--active/--inactive", help="Enable or disable the webhook integration."),
) -> None:
    """Enable or disable a webhook integration."""
    asyncio.run(_toggle(get_execution_context(ctx), webhook_id, active))


async def _toggle(execution: ExecutionContext, webhook_id: UUID, active: bool) -> None:
    async with create_api_client(execution) as client:
        webhook = await client.webhooks.toggle(str(webhook_id), is_active=active)

    state = "active" if webhook.is_active else "inactive"
    typer.echo(f"Webhook {webhook_id!r} is now {state}.")


@app.command("public-url")
def public_url(
    ctx: typer.Context,
    webhook_id: UUID = typer.Argument(..., help="ID of the webhook integration."),
) -> None:
    """Print the public URL for a webhook integration."""
    asyncio.run(_public_url(get_execution_context(ctx), webhook_id))


async def _public_url(execution: ExecutionContext, webhook_id: UUID) -> None:
    async with create_api_client(execution) as client:
        typer.echo(client.webhooks.public_url(webhook_id))

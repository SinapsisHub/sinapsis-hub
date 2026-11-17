"""Secret commands for the Sinapsis CLI."""

import asyncio
from uuid import UUID

import typer
from sinapsis_contracts.cloud_api.models.secrets.payloads import CreateSecretRequest

from sinapsis_cli.execution import ExecutionContext, create_api_client, get_execution_context

from ._secrets_render import print_user_secrets

app = typer.Typer(name="secrets", help="Manage secrets.", no_args_is_help=True)


@app.command()
def create(
    ctx: typer.Context,
    label_args: list[str] = typer.Argument(None, metavar="LABEL", help="Label for the secret (e.g. 'my-label')."),
    label_opt: str | None = typer.Option(None, "--label", "-l", help="Label for the secret."),
    value: str | None = typer.Option(None, "--value", "-v", help="Secret value. If omitted, prompt securely."),
) -> None:
    """Create a new secret."""
    label = label_opt

    if not label and label_args:
        if len(label_args) == 2 and label_args[0].lower() == "label":
            label = label_args[1]
        elif len(label_args) == 1:
            label = label_args[0].removeprefix("label=")
        else:
            label = " ".join(label_args)

    if not label:
        raise typer.BadParameter("Label is required. Use `create LABEL` or `create --label LABEL`.")

    if value is None:
        value = typer.prompt("Secret value", hide_input=True, confirmation_prompt=True)

    payload = CreateSecretRequest(label=label, secret=value)
    asyncio.run(_create(get_execution_context(ctx), payload))


async def _create(execution: ExecutionContext, payload: CreateSecretRequest) -> None:
    async with create_api_client(execution) as client:
        secret = await client.secrets.create(payload)

    typer.echo(f"Created secret {secret.label!r}.")
    typer.echo(f"Metadata ID: {secret.id}")


@app.command("list")
def list_secrets(ctx: typer.Context) -> None:
    """List stored secret metadata."""
    asyncio.run(_list_secrets(get_execution_context(ctx)))


async def _list_secrets(execution: ExecutionContext) -> None:
    async with create_api_client(execution) as client:
        response = await client.secrets.list_user_secrets()

    if not response.secrets:
        typer.echo("No secrets found.")
        return

    print_user_secrets(response)


@app.command()
def get(ctx: typer.Context, metadata_id: UUID = typer.Argument(..., help="Metadata ID of the secret.")) -> None:
    """Get metadata for a stored secret."""
    asyncio.run(_get(get_execution_context(ctx), metadata_id))


async def _get(execution: ExecutionContext, metadata_id: UUID) -> None:
    async with create_api_client(execution) as client:
        secret = await client.secrets.get(metadata_id)

    typer.echo(f"Label:       {secret.label}")
    typer.echo(f"Metadata ID: {secret.id}")


@app.command()
def delete(ctx: typer.Context, metadata_id: UUID = typer.Argument(..., help="Metadata ID of the secret.")) -> None:
    """Delete a stored secret."""
    if not typer.confirm(f"Delete secret {metadata_id!r}?"):
        raise typer.Abort()

    asyncio.run(_delete(get_execution_context(ctx), metadata_id))


async def _delete(execution: ExecutionContext, metadata_id: UUID) -> None:
    async with create_api_client(execution) as client:
        await client.secrets.delete(metadata_id)

    typer.echo(f"Deleted secret: {metadata_id}")

"""User-facing Cloud template and package discovery."""

import asyncio
import json
from uuid import UUID

import typer

from sinapsis_cli.execution import ExecutionContext, create_api_client, get_execution_context

app = typer.Typer(name="templates", help="Search published Cloud templates.", no_args_is_help=True)


def _render_page(page) -> None:
    for item in page.items:
        typer.echo(
            f"{item.get('class_name') or item.get('title') or item.get('name')}  "
            f"[{item.get('package', item.get('version', ''))}]  "
            f"{item.get('id', '')}"
        )
    typer.echo(f"Showing {len(page.items)} of {page.total} results (offset {page.offset})")


@app.command("search")
def search_templates(
    ctx: typer.Context,
    query: str = typer.Argument(..., help="Class, tag, description or capability."),
    category: str | None = typer.Option(None, "--category"),
    package: str | None = typer.Option(None, "--package"),
    tag: str | None = typer.Option(None, "--tag"),
    limit: int = typer.Option(50, "--limit", min=1, max=200),
    offset: int = typer.Option(0, "--offset", min=0),
) -> None:
    """Search the authorized docs catalog with relevance ranking."""
    asyncio.run(_search(get_execution_context(ctx), query, category, package, tag, limit, offset))


async def _search(
    execution: ExecutionContext,
    query: str,
    category: str | None,
    package: str | None,
    tag: str | None,
    limit: int,
    offset: int,
) -> None:
    async with create_api_client(execution) as client:
        result = await client.templates.search(
            query, category=category, package=package, tag=tag, limit=limit, offset=offset
        )
    _render_page(result)


@app.command("list")
def list_templates(
    ctx: typer.Context,
    limit: int = typer.Option(50, "--limit", min=1, max=200),
    offset: int = typer.Option(0, "--offset", min=0),
) -> None:
    """List templates visible to this user."""
    asyncio.run(_list(get_execution_context(ctx), limit, offset))


async def _list(execution: ExecutionContext, limit: int, offset: int) -> None:
    async with create_api_client(execution) as client:
        result = await client.templates.list(limit=limit, offset=offset)
    _render_page(result)


@app.command("show")
def show_template(ctx: typer.Context, template_id: UUID) -> None:
    """Display one published template's full documentation."""
    asyncio.run(_show(get_execution_context(ctx), template_id))


async def _show(execution: ExecutionContext, template_id: UUID) -> None:
    async with create_api_client(execution) as client:
        result = await client.templates.get(template_id)
    typer.echo(json.dumps(result, indent=2, default=str))


@app.command("packages")
def list_packages(
    ctx: typer.Context,
    limit: int = typer.Option(50, "--limit", min=1, max=200),
    offset: int = typer.Option(0, "--offset", min=0),
) -> None:
    """List packages containing templates accessible to this user."""
    asyncio.run(_packages(get_execution_context(ctx), limit, offset))


async def _packages(execution: ExecutionContext, limit: int, offset: int) -> None:
    async with create_api_client(execution) as client:
        result = await client.templates.packages(limit=limit, offset=offset)
    _render_page(result)

"""Configure native uv authentication for Sinapsis-managed package indexes.

No package secrets are placed in Sinapsis profiles, pyproject.toml, command
arguments, or logs. Login validates the scoped token against Cloud first and
then passes it to uv via stdin using the OS-native credential storage preview.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from urllib.parse import urlsplit

import typer

from sinapsis_contracts.cloud_api.paths import PACKAGE_PATHS


app = typer.Typer(name="packages", help="Sinapsis package-index authentication and setup.", no_args_is_help=True)

_HOSTS: dict[str, str] = {
    "sinapsis-dependencies": "https://pypi.sinapsis.tech",
    "sinapsis-community": "https://community.pypi.sinapsis.tech",
    "sinapsis-internal": "https://internal.pypi.sinapsis.tech",
}


def _index_endpoint(registry: str) -> str:
    """Resolve only allowlisted index destinations; prevent secret exfiltration."""
    endpoint = _HOSTS.get(registry)
    if endpoint is None:
        raise typer.BadParameter("Unknown Sinapsis registry")
    parsed = urlsplit(endpoint)
    if parsed.scheme != "https" or not parsed.hostname or parsed.port not in (None, 443):
        raise typer.BadParameter("Invalid configured package-index hostname")
    return endpoint


def _verify_key(registry: str, key: str, cloud_url: str) -> None:
    """Validate read scope and account status before passing a token to uv."""
    parsed = urlsplit(cloud_url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.port not in (None, 443)
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise typer.BadParameter("The Cloud API must use a credential-free HTTPS origin")
    if not re.fullmatch(r"sk_[A-Za-z0-9_-]{8,192}", key):
        raise typer.BadParameter("A scoped Sinapsis API key is required")
    request = urllib.request.Request(
        cloud_url.rstrip("/") + PACKAGE_PATHS.index_list,
        data=json.dumps({"registry": registry}).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            if response.status != 200:
                raise typer.BadParameter("The key was not authorized for package reads")
    except urllib.error.HTTPError as error:
        raise typer.BadParameter(f"Package read permission was denied (HTTP {error.code})") from None
    except (OSError, urllib.error.URLError):
        raise typer.BadParameter("The Sinapsis Cloud API is unavailable") from None


async def _issue_read_key(ctx: typer.Context, registry: str) -> str:
    """Use the existing Cloud session to provision a narrowly scoped index key."""
    from sinapsis_cli.execution import create_api_client, get_execution_context

    try:
        async with create_api_client(get_execution_context(ctx)) as client:
            response = await client.api_keys.generate(
                f"uv:{registry}",
                scopes=["packages:read"],
                agent_ids=[],
                all_user_agents=False,
            )
    except Exception as error:
        # SDK exceptions can include request context; do not display them.
        raise typer.BadParameter("Unable to issue package key; run sinx-cloud configure first") from None
    return response.api_key


@app.command("login")
def login(
    ctx: typer.Context,
    registry: str = typer.Option("sinapsis-community", "--registry", help="Named Sinapsis index."),
    key_environment: str | None = typer.Option(
        None, "--key-env", help="Existing environment variable with a packages:read key."
    ),
    cloud_url: str = typer.Option("https://api.sinapsis.tech", "--cloud-url", help="Cloud API HTTPS origin."),
) -> None:
    """Validate a scoped key and install it into uv native secure credentials."""
    endpoint = _index_endpoint(registry)
    if key_environment is not None:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", key_environment):
            raise typer.BadParameter("Invalid environment-variable name")
        key = os.environ.get(key_environment, "")
    else:
        key = asyncio.run(_issue_read_key(ctx, registry))
    if not key:
        raise typer.BadParameter("No API key supplied")
    _verify_key(registry, key, cloud_url)
    # uv currently defaults to a plaintext store. Never silently fall back to
    # plaintext when the secure OS backend is unavailable. The token is stdin,
    # never shell history or argv. uv auth login itself does not check validity.
    env = dict(os.environ)
    env["UV_PREVIEW_FEATURES"] = ",".join(part for part in [env.get("UV_PREVIEW_FEATURES", ""), "native-auth"] if part)
    try:
        result = subprocess.run(
            ["uv", "auth", "login", urlsplit(endpoint).hostname or "", "--token", "-"],
            input=key + "\n",
            text=True,
            capture_output=True,
            env=env,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise typer.BadParameter("Unable to invoke uv native credential storage") from error
    if result.returncode:
        # uv stderr could contain sensitive diagnostics; never echo it.
        raise typer.BadParameter("uv native credential storage failed; no plaintext fallback was used")
    typer.echo(f"Authenticated uv for {registry}. The key was stored by uv, not Sinapsis.")
    typer.echo("For subsequent uv commands, enable UV_PREVIEW_FEATURES=native-auth in your shell or CI environment.")
    typer.echo("For a project, use a named explicit index and pin the distribution in [tool.uv.sources].")


@app.command("logout")
def logout(registry: str = typer.Option("sinapsis-community", "--registry")) -> None:
    """Remove a locally stored uv credential; remote API key revocation is separate."""
    endpoint = _index_endpoint(registry)
    env = dict(os.environ)
    env["UV_PREVIEW_FEATURES"] = ",".join(part for part in [env.get("UV_PREVIEW_FEATURES", ""), "native-auth"] if part)
    result = subprocess.run(
        ["uv", "auth", "logout", urlsplit(endpoint).hostname or ""],
        env=env,
        check=False,
        capture_output=True,
        timeout=20,
    )
    if result.returncode:
        raise typer.BadParameter("uv could not remove the native credential")
    typer.echo(f"Removed uv credential for {registry}; revoke the API key separately if required.")


@app.command("indexes")
def indexes() -> None:
    """Display credential-free index URLs and the required explicit uv mapping."""
    for name, url in _HOSTS.items():
        typer.echo(f"{name}: {url}/simple/")
    typer.echo(
        "Example: uv add sinapsis-sub-agents --index sinapsis-community=https://community.pypi.sinapsis.tech/simple/"
    )
    typer.echo("Use explicit index/source pinning for private packages and third-party patches.")

"""Per-account, per-endpoint local selection of saved immutable agent versions.

JWT contents are used only to namespace local convenience state, NEVER to authorize
an API call. The backend remains responsible for validating every request.
"""

import base64
import binascii
import hashlib
import json
from uuid import UUID

import typer

from sinapsis_cli.execution import ExecutionContext
from sinapsis_cli.state import get_saved_agent, record_saved_agent


async def selection_scope(execution: ExecutionContext, client) -> str:
    """Scope CLI selection by Cloud profile, API endpoint, and credential identity.

    JWTs use their stable subject across access-token refreshes; opaque API keys
    use a digest of the key, so changing accounts/keys never reuses stale state.
    Do not persist access tokens, raw identity claims, or API keys.
    """
    # The Cloud SDK already owns credential refresh; retrieve its active token.
    token = await client._auth.get_access_token()
    principal = _principal_id(token)
    canonical = json.dumps(
        [execution.profile_name, execution.api_url.rstrip("/").lower(), principal],
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _principal_id(token: str) -> str:
    """Identify the local credential without trusting it as authorization."""
    segments = token.split(".")
    if len(segments) == 3:
        try:
            encoded = segments[1]
            payload = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
            if isinstance(payload, dict):
                subject = payload.get("sub")
                if isinstance(subject, str):
                    # Normal Cloud JWT identities are UUIDs.
                    parsed = UUID(subject)
                    issuer = payload.get("iss", "")
                    if not isinstance(issuer, str):
                        issuer = ""
                    return f"jwt:{issuer}:{parsed}"
        except (ValueError, UnicodeDecodeError, TypeError, binascii.Error):
            pass
    return "opaque:" + hashlib.sha256(token.encode("utf-8")).hexdigest()


def remember_agent(scope: str, agent_id: UUID, version_id: UUID) -> None:
    """Record a verified selection after a successful Management API request."""
    record_saved_agent(scope, str(agent_id), str(version_id))


async def newest_version(client, agent_id: UUID, *, allow_empty: bool = False):
    """Return the newest visible version, failing if the API page is incomplete."""
    versions = await client.agents.list_versions(agent_id)
    if not versions:
        if allow_empty:
            return None
        raise typer.BadParameter(f"Agent {agent_id} has no versions. Publish one with 'agents publish'.")
    # Management currently caps its versions response at 200 without pagination.
    # Selecting 'latest' from a truncated list would be unsafe.
    if len(versions) >= 200:
        raise typer.BadParameter(
            "The server returned 200 versions; latest cannot be determined safely. "
            "Supply --agent-version-id explicitly."
        )
    return max(versions, key=lambda version: (version.created_at, str(version.id)))


async def resolve_schedule_agent(
    client, execution: ExecutionContext, agent_id: UUID | None, version_id: UUID | None
) -> tuple[UUID, UUID, str]:
    """Resolve optional CLI flags to immutable IDs before creating a schedule."""
    scope = await selection_scope(execution, client)
    selected = get_saved_agent(scope)
    explicit_agent = agent_id is not None

    if agent_id is None:
        if selected is None:
            raise typer.BadParameter(
                "No agent selected for this Cloud account/profile. "
                "Run 'sinx-cloud agents register FILE.yaml' or supply --agent-id "
                "and --agent-version-id."
            )
        agent_id = UUID(selected.agent_id)

    if version_id is None:
        if explicit_agent:
            version = await newest_version(client, agent_id)
            version_id = version.id
        else:
            assert selected is not None
            version_id = UUID(selected.agent_version_id)
    elif not explicit_agent:
        # The API has no global reverse lookup for a version UUID.
        # Use the locally selected agent, and verify the association.
        version = await client.agents.get_version(agent_id, version_id)
        if version.agent_id != agent_id:
            raise typer.BadParameter(
                "The version does not belong to the selected agent. Supply both --agent-id and --agent-version-id."
            )

    return agent_id, version_id, scope

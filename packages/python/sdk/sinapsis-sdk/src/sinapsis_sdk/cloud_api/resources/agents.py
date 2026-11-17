"""Saved-agent registration and version discovery through authenticated HTTP."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sinapsis_contracts.cloud_api.models.saved_agent import (
    Agent,
    AgentRegisterRequest,
    AgentRegistration,
    AgentVersion,
    AgentVersionPublishRequest,
)
from sinapsis_contracts.cloud_api.paths.saved_agent import SAVED_AGENT_PATHS

from sinapsis_sdk.common.base_resource_client import BaseClientResource


class AgentsResource(BaseClientResource):
    """The Cloud backend owns access control; the SDK never queries Supabase."""

    def __init__(self, http) -> None:
        super().__init__(http, SAVED_AGENT_PATHS.base)

    async def register(
        self, definition: dict[str, Any], *, name: str | None = None, version: str, description: str | None = None
    ) -> AgentRegistration:
        request = AgentRegisterRequest(name=name, version=version, definition=definition, description=description)
        payload = request.model_dump(mode="json", exclude_none=True)
        data = await self._http.post(self._path(SAVED_AGENT_PATHS.register), json=payload)
        return AgentRegistration.model_validate(data)

    async def publish(self, agent_id: UUID, definition: dict[str, Any], *, version: str) -> AgentVersion:
        request = AgentVersionPublishRequest(version=version, definition=definition)
        data = await self._http.post(
            self._path(SAVED_AGENT_PATHS.versions, agent_id=str(agent_id)),
            json=request.model_dump(mode="json", exclude_none=True),
        )
        return AgentVersion.model_validate(data)

    async def list(self, *, include_execution: bool = False, limit: int = 200, offset: int = 0) -> list[Agent]:
        data = await self._http.get(
            self._path(""), params={"include_execution": include_execution, "limit": limit, "offset": offset}
        )
        return [Agent.model_validate(item) for item in data]

    async def get(self, agent_id: UUID) -> Agent:
        data = await self._http.get(self._path(SAVED_AGENT_PATHS.agent, agent_id=str(agent_id)))
        return Agent.model_validate(data)

    async def versions(self, agent_id: UUID) -> list[AgentVersion]:
        """Page through every immutable revision (the server caps pages at 200)."""
        entries: list[AgentVersion] = []
        while True:
            data = await self._http.get(
                self._path(SAVED_AGENT_PATHS.versions, agent_id=str(agent_id)),
                params={"limit": 200, "offset": len(entries)},
            )
            entries.extend(AgentVersion.model_validate(item) for item in data)
            if len(data) < 200:
                return entries

    async def version(self, agent_id: UUID, version_id: UUID) -> AgentVersion:
        data = await self._http.get(
            self._path(SAVED_AGENT_PATHS.version, agent_id=str(agent_id), version_id=str(version_id))
        )
        return AgentVersion.model_validate(data)

    async def latest_version(self, agent_id: UUID) -> AgentVersion:
        versions = await self.versions(agent_id)
        if not versions:
            raise LookupError(f"Agent {agent_id} has no published versions")
        return max(versions, key=lambda item: (item.created_at, str(item.id)))

    async def all_versions(self, *, include_execution: bool = False) -> list[tuple[Agent, list[AgentVersion]]]:
        """Use existing endpoints, paging agents without cross-owner discovery."""
        items: list[tuple[Agent, list[AgentVersion]]] = []
        offset, page_size = 0, 200
        while True:
            page = await self.list(include_execution=include_execution, offset=offset, limit=page_size)
            for agent in page:
                items.append((agent, await self.versions(agent.id)))
            if len(page) < page_size:
                break
            offset += len(page)
        return items

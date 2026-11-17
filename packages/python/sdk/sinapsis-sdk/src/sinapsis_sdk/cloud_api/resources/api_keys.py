"""User-owned scoped API keys; a key's plaintext is only available on issue."""

from __future__ import annotations

from datetime import datetime
from typing import Sequence
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sinapsis_contracts.cloud_api.paths import ACCESS_API_KEY_PATHS

from sinapsis_sdk.common.base_resource_client import BaseClientResource


class ScopedKeyMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: UUID
    name: str
    prefix: str
    scopes: list[str] = Field(default_factory=list)
    agent_ids: list[UUID] = Field(default_factory=list)
    all_user_agents: bool = False
    expires_at: datetime | None = None
    revoked_at: datetime | None = None

    @property
    def api_key_name(self) -> str:
        return self.name

    @property
    def api_key(self) -> str:
        return f"{self.prefix}-*****"


class IssuedKey(BaseModel):
    metadata: ScopedKeyMetadata
    api_key: str = Field(repr=False)

    @property
    def api_key_name(self) -> str:
        return self.metadata.name


class KeyList(BaseModel):
    keys: list[ScopedKeyMetadata]

    @property
    def items(self) -> list[ScopedKeyMetadata]:
        return self.keys


class ApiKeysResource(BaseClientResource):
    """Manage only the authenticated user's own API keys."""

    def __init__(self, http) -> None:
        super().__init__(http, ACCESS_API_KEY_PATHS.base)

    async def generate(
        self,
        name: str,
        *,
        scopes: Sequence[str] | None = None,
        agent_ids: Sequence[str | UUID] = (),
        all_user_agents: bool = False,
        expires_at: datetime | None = None,
    ) -> IssuedKey:
        """Issue a key. Default is files:read (least-privilege compatibility)."""
        return await self.issue(
            name, scopes=scopes, agent_ids=agent_ids, all_user_agents=all_user_agents, expires_at=expires_at
        )

    async def issue(
        self,
        name: str,
        *,
        scopes: Sequence[str] | None = None,
        agent_ids: Sequence[str | UUID] = (),
        all_user_agents: bool = False,
        expires_at: datetime | None = None,
    ) -> IssuedKey:
        payload = {
            "name": name,
            "scopes": list(scopes if scopes is not None else ["files:read"]),
            "agent_ids": [str(value) for value in agent_ids],
            "all_user_agents": all_user_agents,
            "expires_at": expires_at.isoformat() if expires_at else None,
        }
        data = await self._http.post(self._path(ACCESS_API_KEY_PATHS.create), json=payload)
        return IssuedKey.model_validate(data)

    async def list_scoped(self) -> list[ScopedKeyMetadata]:
        data = await self._http.get(self._path(ACCESS_API_KEY_PATHS.list))
        return [ScopedKeyMetadata.model_validate(item) for item in data["items"]]

    async def list_all(self) -> KeyList:
        """Legacy shape .keys preserved; only masked prefixes are listed."""
        return KeyList(keys=await self.list_scoped())

    async def delete(self, api_key: str | UUID) -> bool:
        """Revoke by UUID or the legacy masked prefix (resolved for this user)."""
        try:
            key_id = UUID(str(api_key))
        except ValueError:
            matches = [key for key in await self.list_scoped() if api_key == key.prefix or api_key == key.api_key]
            if len(matches) != 1:
                raise ValueError("API key not found; supply its UUID or masked prefix") from None
            key_id = matches[0].id
        await self._http.post(self._path(ACCESS_API_KEY_PATHS.delete), json={"key_id": str(key_id)})
        return True

    async def validate(self) -> bool:
        """Validate the current JWT session (scoped keys cannot use this route)."""
        response = await self._http.get(self._path(ACCESS_API_KEY_PATHS.validate))
        return bool(response["valid"])

    async def copy_value(self, api_key: str):
        """Existing key plaintext is never retrievable from hashed storage."""
        raise ValueError("API keys can only be copied when they are created; rotate this key instead")

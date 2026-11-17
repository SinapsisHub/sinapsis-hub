"""Authentication and session management through Sinapsis Cloud (not Supabase)."""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Any

import httpx
from sinapsis_contracts.common.paths import BaseApiPaths

from sinapsis_sdk.cloud_api.cloud_config import CloudAPIConfig as Config
from sinapsis_sdk.common.exceptions import AuthenticationError

from ._credentials import CredentialStore

# Retain the existing credential key and session shape to avoid CLI reconfiguration.
_SESSION_CREDENTIAL = "supabase_session"
_API_KEY_CREDENTIAL = "api_key"
_TOKEN_REFRESH_MARGIN = 60
_AUTH_BASE = f"{BaseApiPaths.base}/auth/sdk"


@dataclass(frozen=True, slots=True)
class SupabaseSession:
    """Persisted bearer session (legacy class name retained for compatibility)."""

    access_token: str = field(repr=False)
    refresh_token: str = field(repr=False)
    expires_at: int

    @property
    def is_expired(self) -> bool:
        return time.time() >= self.expires_at - _TOKEN_REFRESH_MARGIN

    def to_dict(self) -> dict[str, Any]:
        return {"access_token": self.access_token, "refresh_token": self.refresh_token, "expires_at": self.expires_at}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SupabaseSession:
        access = data.get("access_token")
        refresh = data.get("refresh_token")
        expiry = data.get("expires_at")
        if not isinstance(access, str) or not access:
            raise ValueError("Invalid access token")
        if not isinstance(refresh, str) or not refresh:
            raise ValueError("Invalid refresh token")
        if isinstance(expiry, bool) or not isinstance(expiry, int):
            raise ValueError("Invalid token expiry")
        return cls(access_token=access, refresh_token=refresh, expires_at=expiry)


class AuthManager:
    """Manage Cloud-issued bearer tokens and scoped Sinapsis API keys."""

    def __init__(self, config: Config, credential_store: CredentialStore) -> None:
        self._config = config
        self._credential_store = credential_store
        self._http: httpx.AsyncClient | None = None
        self._refresh_lock = asyncio.Lock()

    def is_configured(self) -> bool:
        return (
            self._credential_store.get(_API_KEY_CREDENTIAL) is not None
            or self._credential_store.get(_SESSION_CREDENTIAL) is not None
        )

    async def login(self, email: str, password: str) -> None:
        """Authenticate against Cloud; no direct Supabase client is created."""
        data = await self._request("login", {"email": email, "password": password})
        self._save_session(self._session_from_response(data))
        self._credential_store.delete(_API_KEY_CREDENTIAL)

    def set_api_key(self, api_key: str) -> None:
        if not api_key.strip():
            raise AuthenticationError("API key cannot be empty")
        self._credential_store.set(_API_KEY_CREDENTIAL, api_key)
        self._credential_store.delete(_SESSION_CREDENTIAL)

    async def get_access_token(self) -> str:
        api_key = self._credential_store.get(_API_KEY_CREDENTIAL)
        if api_key is not None:
            return api_key
        saved = self._credential_store.get(_SESSION_CREDENTIAL)
        if saved is None:
            raise AuthenticationError("No credentials configured. Run 'sinapsis configure' first.")
        session = self._deserialize_session(saved)
        if not session.is_expired:
            return session.access_token
        return await self._refresh_session(session)

    def logout(self) -> None:
        """Remove local credentials; does not claim server-side JWT revocation."""
        self._credential_store.delete(_API_KEY_CREDENTIAL)
        self._credential_store.delete(_SESSION_CREDENTIAL)

    async def aclose(self) -> None:
        if self._http is not None:
            await self._http.aclose()
            self._http = None

    async def _refresh_session(self, session: SupabaseSession) -> str:
        async with self._refresh_lock:
            saved = self._credential_store.get(_SESSION_CREDENTIAL)
            if saved is None:
                raise AuthenticationError("Session was removed during refresh")
            current = self._deserialize_session(saved)
            if not current.is_expired:
                return current.access_token
            data = await self._request("refresh", {"refresh_token": current.refresh_token})
            refreshed = self._session_from_response(data)
            self._save_session(refreshed)  # persist rotated refresh token
            return refreshed.access_token

    async def _request(self, action: str, payload: dict[str, str]) -> dict[str, Any]:
        if self._http is None:
            self._http = httpx.AsyncClient(base_url=self._config.api_url.rstrip("/"), timeout=self._config.timeout)
        try:
            response = await self._http.post(f"{_AUTH_BASE}/{action}", json=payload)
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            # No passwords, refresh tokens or response bodies in exceptions/logs.
            raise AuthenticationError(f"Cloud {action} failed; verify your credentials or try again") from exc
        if not isinstance(data, dict):
            raise AuthenticationError("Cloud returned an invalid authentication response")
        return data

    @staticmethod
    def _session_from_response(data: dict[str, Any]) -> SupabaseSession:
        try:
            return SupabaseSession.from_dict(data)
        except ValueError as exc:
            raise AuthenticationError("Cloud returned an invalid authentication session") from exc

    def _save_session(self, session: SupabaseSession) -> None:
        self._credential_store.set(_SESSION_CREDENTIAL, self._serialize_session(session))

    @staticmethod
    def _serialize_session(session: SupabaseSession) -> str:
        return json.dumps(session.to_dict())

    @staticmethod
    def _deserialize_session(value: str) -> SupabaseSession:
        try:
            data = json.loads(value)
            if isinstance(data, dict):
                return SupabaseSession.from_dict(data)
        except (ValueError, TypeError) as exc:
            raise AuthenticationError("Stored authentication session is invalid") from exc
        raise AuthenticationError("Stored authentication session is invalid")

"""Async HTTP transport for the Sinapsis SDK."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from sinapsis_sdk.common.async_http_client import AsyncHTTPClient
from sinapsis_sdk.common.base_config import BaseAPIConfig
from sinapsis_sdk.common.exceptions import AuthenticationError

from ._auth import AuthManager


class CloudAsyncHTTPClient(AsyncHTTPClient):
    """Authenticated HTTP transport for the Sinapsis Cloud API."""

    def __init__(self, config: BaseAPIConfig, auth: AuthManager) -> None:
        super().__init__(config)
        self._auth = auth

    async def request(self, method: str, path: str, *, raw: bool = False, **kwargs: Any) -> Any:
        """Send an authenticated HTTP request."""
        kwargs["headers"] = await self._authenticated_headers(kwargs.pop("headers", None))

        return await super().request(method, path, raw=raw, **kwargs)

    async def stream_msgpack(self, method: str, path: str, **kwargs: Any) -> AsyncIterator[bytes]:
        """Stream an authenticated HTTP response."""
        kwargs["headers"] = await self._authenticated_headers(kwargs.pop("headers", None))

        async for chunk in super().stream_msgpack(method, path, **kwargs):
            yield chunk

    async def _authenticated_headers(self, headers: Any = None) -> dict[str, str]:
        """Return request headers containing the current access token."""
        request_headers = dict(headers or {})

        # AuthManager refreshes bearer tokens through Cloud when necessary.
        access_token = await self._auth.get_access_token()

        if not access_token:
            raise AuthenticationError("No authentication token is available.")

        request_headers["Authorization"] = f"Bearer {access_token}"
        return request_headers

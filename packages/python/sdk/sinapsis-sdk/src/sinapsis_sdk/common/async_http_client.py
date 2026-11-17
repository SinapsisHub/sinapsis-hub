"""Async HTTP transport for the Sinapsis SDK."""

from __future__ import annotations

from collections.abc import AsyncIterator
from types import TracebackType
from typing import Any

import httpx

from sinapsis_sdk.common.base_config import BaseAPIConfig
from sinapsis_sdk.common.exception_parser import get_error_message
from sinapsis_sdk.common.exceptions import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    NetworkError,
    NotFoundError,
)


class AsyncHTTPClient:
    """Base asynchronous HTTP transport without authentication."""

    def __init__(self, config: BaseAPIConfig) -> None:
        self._client = httpx.AsyncClient(base_url=config.api_url.rstrip("/"), timeout=config.timeout)

    async def get(self, path: str, **kwargs: Any) -> Any:
        """Send a GET request."""
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> Any:
        """Send a POST request."""
        return await self.request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs: Any) -> Any:
        """Send a PUT request."""
        return await self.request("PUT", path, **kwargs)

    async def patch(self, path: str, **kwargs: Any) -> Any:
        """Send a PATCH request."""
        return await self.request("PATCH", path, **kwargs)

    async def delete(self, path: str, **kwargs: Any) -> Any:
        """Send a DELETE request."""
        return await self.request("DELETE", path, **kwargs)

    async def request(self, method: str, path: str, *, raw: bool = False, **kwargs: Any) -> Any:
        """Send an HTTP request."""
        try:
            response = await self._client.request(method, path, **kwargs)
        except httpx.ReadTimeout as exc:
            raise NetworkError("The Sinapsis API did not respond before the read timeout") from exc
        except httpx.HTTPError as exc:
            raise NetworkError(f"Sinapsis API request failed: {exc}") from exc

        self._raise_for_status(response)

        if raw:
            return response.content

        return self._decode_response(response)

    async def stream_msgpack(self, method: str, path: str, **kwargs: Any) -> AsyncIterator[bytes]:
        """Stream an HTTP response."""
        # Streaming agents can legitimately be silent for longer than the
        # ordinary 30-second request timeout. Keep connect/write/pool bounds,
        # but do not mistake an idle, established stream for a connection error.
        timeout = self._client.timeout
        kwargs.setdefault(
            "timeout", httpx.Timeout(connect=timeout.connect, read=None, write=timeout.write, pool=timeout.pool)
        )
        try:
            async with self._client.stream(method, path, **kwargs) as response:
                self._raise_for_status(response)

                async for chunk in response.aiter_bytes():
                    yield chunk

        except httpx.ReadTimeout as exc:
            raise NetworkError("The API connection was established, but reading the stream timed out") from exc
        except httpx.HTTPError as exc:
            raise NetworkError(f"Sinapsis API stream failed: {exc}") from exc

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> AsyncHTTPClient:
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> None:
        await self.aclose()

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        if response.is_success:
            return

        status_code = response.status_code
        message = get_error_message(response)

        if status_code == 401:
            raise AuthenticationError(message)

        if status_code == 403:
            raise AuthorizationError(message)

        if status_code == 404:
            raise NotFoundError(message)

        raise APIError(message, status_code=status_code, response=response)

    @staticmethod
    def _decode_response(response: httpx.Response) -> Any:
        if not response.content:
            return None

        content_type = response.headers.get("content-type", "")

        if "application/json" in content_type:
            return response.json()

        return response.text

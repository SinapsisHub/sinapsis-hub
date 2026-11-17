from __future__ import annotations

from types import TracebackType

from sinapsis_sdk.common.async_http_client import AsyncHTTPClient
from sinapsis_sdk.common.base_config import BaseAPIConfig


class BaseSinapsisAPIClient:
    """Base async API client.

    Owns SDK configuration and HTTP transport only.
    """

    def __init__(self, config: BaseAPIConfig, http: AsyncHTTPClient) -> None:
        self._config = config
        self._http = http

    async def aclose(self) -> None:
        """Close the client and release network resources."""
        await self._http.aclose()

    async def __aenter__(self) -> BaseSinapsisAPIClient:
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> None:
        await self.aclose()

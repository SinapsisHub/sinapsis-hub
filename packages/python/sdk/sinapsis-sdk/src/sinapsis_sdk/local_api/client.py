from sinapsis_sdk.common.async_http_client import AsyncHTTPClient
from sinapsis_sdk.common.base_client import BaseSinapsisAPIClient
from sinapsis_sdk.common.base_config import BaseAPIConfig

from .resources.jobs import LocalJobsResource


class SinapsisAPIClient(BaseSinapsisAPIClient):
    """Async client for interacting with a local Sinapsis API."""

    def __init__(self, config: BaseAPIConfig) -> None:
        http = AsyncHTTPClient(config)

        super().__init__(config=config, http=http)

        self.jobs = LocalJobsResource(self._http)

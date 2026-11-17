"""Main client for the Sinapsis API."""

from __future__ import annotations

from sinapsis_sdk.cloud_api.cloud_config import CloudAPIConfig
from sinapsis_sdk.common.base_client import BaseSinapsisAPIClient

from ._auth import AuthManager
from ._credentials import CredentialStore, create_credential_store
from ._http_client import CloudAsyncHTTPClient
from .resources import (
    AgentsResource,
    ApiKeysResource,
    FilesResource,
    JobsResource,
    SchedulesResource,
    SecretsResource,
    TemplatesResource,
    WebhooksResource,
)


class CloudSinapsisAPIClient(BaseSinapsisAPIClient):
    """Async client for interacting with the Sinapsis Cloud API."""

    def __init__(self, config: CloudAPIConfig | None = None, credential_store: CredentialStore | None = None) -> None:
        config = config or CloudAPIConfig()

        self._credential_store = credential_store or create_credential_store()
        self._auth = AuthManager(config, self._credential_store)

        http = CloudAsyncHTTPClient(config, self._auth)

        super().__init__(config=config, http=http)

        self.jobs = JobsResource(self._http)
        self.agents = AgentsResource(self._http)
        self.schedules = SchedulesResource(self._http)
        self.files = FilesResource(self._http)
        self.api_keys = ApiKeysResource(self._http)
        self.secrets = SecretsResource(self._http)
        self.webhooks = WebhooksResource(self._http)
        self.templates = TemplatesResource(self._http)

    async def aclose(self) -> None:
        await super().aclose()
        await self._auth.aclose()

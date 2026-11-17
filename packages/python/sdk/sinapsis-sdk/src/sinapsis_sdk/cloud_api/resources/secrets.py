"""User secret operations for the Sinapsis API."""

from uuid import UUID

from sinapsis_contracts.cloud_api.models.secrets.payloads import CreateSecretRequest
from sinapsis_contracts.cloud_api.models.secrets.responses import UserSecretListResponse, UserSecretResponse
from sinapsis_contracts.cloud_api.paths import USER_SECRET_PATHS

from sinapsis_sdk.common.base_resource_client import BaseClientResource

from .._http_client import CloudAsyncHTTPClient


class SecretsResource(BaseClientResource):
    """Provides operations for user-managed secrets."""

    def __init__(self, http: CloudAsyncHTTPClient) -> None:
        super().__init__(http, USER_SECRET_PATHS.base)

    async def create(self, payload: CreateSecretRequest) -> UserSecretListResponse:
        """Store a secret.

        The secret value is sent to the API but is never returned by the API.

        Args:
            payload containing: User-defined 'label' for the secret and 'secret' value to store.

        Returns:
            Metadata for the newly stored secret.
        """
        response = await self._http.post(self._path(USER_SECRET_PATHS.create), json=payload.model_dump(mode="json"))
        return UserSecretResponse.model_validate(response)

    async def list_user_secrets(self) -> UserSecretListResponse:
        """List stored secret metadata.

        Returns:
            Metadata for all secrets belonging to the authenticated user.
        """
        response = await self._http.get(self._path(USER_SECRET_PATHS.list))
        return UserSecretListResponse(secrets=response.get("secrets"))

    async def get(self, metadata_id: UUID) -> UserSecretResponse:
        """Get metadata for a stored secret.

        The secret value is never returned.

        Args:
            metadata_id: ID of the secret metadata.

        Returns:
            Metadata for the requested secret.
        """
        response = await self._http.get(self._path(USER_SECRET_PATHS.get, metadata_id=str(metadata_id)))
        return UserSecretResponse.model_validate(response)

    async def delete(self, metadata_id: UUID) -> None:
        """Delete a stored secret.

        Args:
            metadata_id: ID of the secret metadata.
        """
        await self._http.delete(self._path(USER_SECRET_PATHS.delete, metadata_id=str(metadata_id)))

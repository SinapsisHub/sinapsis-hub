"""Webhook operations for the Sinapsis API."""

import hashlib
import hmac
import time
from uuid import UUID

import httpx
from sinapsis_contracts.cloud_api.models.webhooks.payloads import RegisterWebhookRequest
from sinapsis_contracts.cloud_api.models.webhooks.responses import DeleteResponse, ToggleWebhookIntegration
from sinapsis_contracts.cloud_api.paths import PUBLIC_WEBHOOK_PATHS, WEBHOOK_PATHS
from sinapsis_contracts.common.constants import ApiConstants

from sinapsis_sdk.cloud_api.models.webhook import TriggerPayload
from sinapsis_sdk.cloud_api.models.webhook_integration import WebhookList, WebhookRecord
from sinapsis_sdk.common.base_resource_client import BaseClientResource

from .._http_client import CloudAsyncHTTPClient


class WebhooksResource(BaseClientResource):
    """Provides operations for webhook integrations."""

    def __init__(self, http: CloudAsyncHTTPClient) -> None:
        super().__init__(http, WEBHOOK_PATHS.base)

    def public_url(self, webhook_id: UUID | str) -> str:
        """Build the public receiver URL path without exposing credentials."""
        return f"{PUBLIC_WEBHOOK_PATHS.base}/{webhook_id}"

    async def register(self, payload: RegisterWebhookRequest) -> WebhookRecord:
        """Register a webhook integration.

        Args:
            payload: Webhook registration configuration.

        Returns:
            The registered webhook integration.
        """
        body = payload.model_dump(mode="json")
        if body.get("expected_schema") is None:
            body["expected_schema"] = {}
        response = await self._http.post(self._path(WEBHOOK_PATHS.register), json=body)
        return WebhookRecord.model_validate(response)

    async def list_user_webhooks(self) -> WebhookList:
        """List the user's webhook integrations.

        Returns:
            Registered webhook integrations.
        """
        response = await self._http.get(self._path(WEBHOOK_PATHS.list))
        return WebhookList.model_validate(response)

    async def get(self, webhook_id: UUID | str) -> WebhookRecord:
        """Fetch one user-accessible webhook integration by UUID."""
        response = await self._http.get(self._path(WEBHOOK_PATHS.delete, webhook_id=str(webhook_id)))
        return WebhookRecord.model_validate(response)

    async def delete(self, webhook_id: UUID) -> DeleteResponse:
        """Delete a webhook integration.

        Args:
            webhook_id: ID of the webhook integration.

        Returns:
            Deletion result.
        """
        response = await self._http.delete(self._path(WEBHOOK_PATHS.delete, webhook_id=str(webhook_id)))
        return DeleteResponse(status="success", message=f"Deleted webhook {webhook_id}")

    async def toggle(self, webhook_id: UUID, is_active: bool) -> ToggleWebhookIntegration:
        """Enable or disable a webhook integration.

        Args:
            webhook_id: ID of the webhook integration.
            is_active: Whether the integration should be enabled.

        Returns:
            The updated webhook integration.
        """
        response = await self._http.patch(
            self._path(WEBHOOK_PATHS.toggle, webhook_id=str(webhook_id)), json={"is_active": is_active}
        )
        return ToggleWebhookIntegration.model_validate(response)


class PublicWebhooksResource(BaseClientResource):
    def __init__(self, http) -> None:
        super().__init__(http, PUBLIC_WEBHOOK_PATHS.base)

    def public_url(self, webhook_id: str) -> str:
        return self._path(PUBLIC_WEBHOOK_PATHS.webhook, webhook_id=str(webhook_id))

    async def trigger_webhook(self, webhook_id: UUID, secret: str, payload: TriggerPayload) -> httpx.Response:
        body = payload.dump_body()

        timestamp = int(time.time())

        signature = self.__sign_payload(body=body, secret=secret, timestamp=timestamp)

        headers = {"Content-Type": "application/json", ApiConstants.signature: f"t={timestamp},v1={signature}"}

        return await self._http.post(self.public_url(str(webhook_id)), content=body, headers=headers)

    @staticmethod
    def __sign_payload(body: bytes, secret: str, timestamp: int) -> str:
        signed_payload = str(timestamp).encode("utf-8") + b"." + body

        return hmac.new(secret.encode("utf-8"), msg=signed_payload, digestmod=hashlib.sha256).hexdigest()

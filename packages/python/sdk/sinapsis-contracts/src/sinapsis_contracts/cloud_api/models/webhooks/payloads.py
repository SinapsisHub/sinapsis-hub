from typing import Any
from uuid import UUID

from pydantic import BaseModel

from .responses import WebhookBase


class RegisterWebhookRequest(WebhookBase):
    """Model used for incoming registration payloads."""

    provider: str


class WebhookTriggerPayload(BaseModel):
    """Base model to hold webhook metadata and payload.

    Payload traditionally comes as a nested dict.
    """

    user_id: UUID
    webhook_id: UUID
    provider: str
    payload: dict[str, Any]

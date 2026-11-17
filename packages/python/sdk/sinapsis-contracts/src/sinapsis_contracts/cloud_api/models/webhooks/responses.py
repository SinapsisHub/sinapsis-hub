from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

from sinapsis_contracts.cloud_api.paths import PUBLIC_WEBHOOK_PATHS


class WebhookBase(BaseModel):
    """Shared fields and configuration for webhook models."""

    integration_name: str = Field(..., min_length=1, max_length=100)
    credential_id: UUID | str | None = None
    enforce_schema: bool = False
    expected_schema: dict[str, Any] | None = None

    model_config = ConfigDict(extra="ignore")


class RegisteredWebhookItem(WebhookBase):
    """Model used for stored items and API responses."""

    user_id: UUID
    webhook_id: UUID = Field(alias="id")
    provider: str  # Overrides/re-specifies type as string if needed
    created_at: datetime
    last_used_at: datetime | None = None
    is_active: bool = (True,)

    @computed_field
    @property
    def webhook_url(self) -> str:
        return f"{PUBLIC_WEBHOOK_PATHS.base}/{self.webhook_id}"


class DeleteResponse(BaseModel):
    status: str
    message: str


class ToggleWebhookIntegration(BaseModel):
    is_active: bool


class ListWebhooksResponse(BaseModel):
    items: list[RegisteredWebhookItem]

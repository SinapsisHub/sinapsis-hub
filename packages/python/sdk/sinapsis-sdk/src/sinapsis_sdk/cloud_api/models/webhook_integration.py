"""HTTP view of management-owned webhook integrations."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from sinapsis_contracts.cloud_api.paths import PUBLIC_WEBHOOK_PATHS


class WebhookRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: UUID
    owner_type: str
    owner_id: UUID
    created_by: UUID
    provider: str
    integration_name: str
    credential_id: UUID | None = None
    enforce_schema: bool = False
    expected_schema: dict | None = None
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None = None

    @property
    def webhook_id(self) -> UUID:
        return self.id

    @property
    def webhook_url(self) -> str:
        return f"{PUBLIC_WEBHOOK_PATHS.base}/{self.id}"


class WebhookList(BaseModel):
    items: list[WebhookRecord]

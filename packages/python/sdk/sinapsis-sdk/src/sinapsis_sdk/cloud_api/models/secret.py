"""Models for Sinapsis user secrets."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class SecretMetadata(BaseModel):
    """Metadata for a stored user secret.

    Args:
        metadata_id: Unique identifier for the secret metadata.
        label: User-defined label for the secret.
    """

    metadata_id: UUID
    label: str

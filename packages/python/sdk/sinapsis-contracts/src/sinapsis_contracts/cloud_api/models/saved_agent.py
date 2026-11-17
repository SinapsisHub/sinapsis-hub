"""Saved-agent HTTP metadata with opaque, canonical runtime definitions.

Transport must NOT validate or reinterpret Sinapsis graphs. The only validator
is the runtime generic_agent_schema_builder.
"""

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    """Reject unknown fields rather than silently losing persisted content."""

    model_config = ConfigDict(extra="forbid")


class AgentRegistrationSource(StrEnum):
    EXPLICIT = "EXPLICIT"
    EXECUTION = "EXECUTION"
    UNKNOWN = "UNKNOWN"


# Compatibility import for callers that used the old name. This is JSON data,
# NOT a competing Pydantic schema: only Sinapsis AgentSchema defines the graph.
AgentDefinition = dict[str, Any]


class Agent(StrictModel):
    id: UUID
    name: str
    description: str | None = None
    owner_type: Literal["USER", "TEAM"]
    owner_id: UUID
    created_by: UUID
    visibility: Literal["PRIVATE", "TEAM", "ORGANIZATION", "PUBLIC"]
    registration_source: AgentRegistrationSource = AgentRegistrationSource.UNKNOWN
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class AgentVersion(StrictModel):
    id: UUID
    agent_id: UUID
    version: str
    # The Sinapsis AgentSchema JSON dump is the entire stored definition.
    # Do not revalidate it with an independent transport schema.
    definition: dict[str, Any]
    checksum_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    created_by: UUID
    created_at: datetime


class AgentRegistration(StrictModel):
    agent_id: UUID
    agent_version_id: UUID
    version: str
    checksum_sha256: str


class AgentRegisterRequest(StrictModel):
    name: str | None = None
    version: str = Field(min_length=1)
    # Raw user graph: validation belongs exclusively to generic_agent_schema_builder.
    definition: dict[str, Any]
    description: str | None = None


class AgentVersionPublishRequest(StrictModel):
    version: str = Field(min_length=1)
    definition: dict[str, Any]

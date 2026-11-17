"""Bounded contracts between uv index gateway, Cloud and Management."""
from __future__ import annotations

from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class IndexFilesQuery(BaseModel):
    """Request a user-visible project listing; never includes object keys."""
    model_config = ConfigDict(extra='forbid')
    registry: Literal['sinapsis-dependencies', 'sinapsis-community', 'sinapsis-internal']
    distribution: str | None = Field(default=None, pattern=r'^[A-Za-z0-9][A-Za-z0-9._-]{0,254}$')


class IndexArtifactQuery(BaseModel):
    """Authorise one exact artifact file, never caller-supplied storage keys."""
    model_config = ConfigDict(extra='forbid')
    registry: Literal['sinapsis-dependencies', 'sinapsis-community', 'sinapsis-internal']
    distribution: str = Field(pattern=r'^[A-Za-z0-9][A-Za-z0-9._-]{0,254}$')
    filename: str = Field(pattern=r'^[A-Za-z0-9][A-Za-z0-9_.+-]{1,254}$')
    track_download: bool = True


class IndexArtifactDecision(BaseModel):
    """Storage capability released only after authenticated package ACL check."""
    model_config = ConfigDict(extra='forbid')
    package_id: UUID
    package_version_id: UUID
    artifact_id: UUID
    filename: str
    object_key: str
    sha256: str
    size_bytes: int
    download_id: UUID | None = None


class IndexFile(BaseModel):
    """Public file metadata for Simple API HTML generation."""
    model_config = ConfigDict(extra='forbid')
    filename: str
    sha256: str
    size_bytes: int
    version: str


class IndexProjectListResponse(BaseModel):
    """Authorized project-name list for the Python Simple Repository root."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    packages: list[str] = Field(max_length=1000)


class IndexFilesResponse(BaseModel):
    """Authorized immutable distribution-file listing."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    files: list[IndexFile] = Field(max_length=10000)

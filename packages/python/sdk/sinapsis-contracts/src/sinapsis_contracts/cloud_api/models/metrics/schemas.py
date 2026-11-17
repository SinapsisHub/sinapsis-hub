"""JSON response contract for asynchronous, distributed execution telemetry."""

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class JobMetricsResponse(BaseModel):
    """Per-job reconciled observations; not a billing invoice or quota settlement."""

    job_id: str = Field(min_length=1, max_length=256)
    agent_id: str = Field(min_length=1, max_length=256)
    saved_agent_id: UUID | None = None
    user_id: UUID | None = None
    owner_type: Literal["USER", "TEAM"]
    owner_id: UUID
    agent_observations: int = Field(ge=0)
    template_observations: int = Field(ge=0)
    failed_template_observations: int = Field(ge=0)
    agent_elapsed_ms: Decimal | None = Field(default=None, ge=0)
    template_elapsed_ms: Decimal | None = Field(default=None, ge=0)
    template_thread_cpu_ms: Decimal | None = Field(default=None, ge=0)
    agent_thread_cpu_ms: Decimal | None = Field(default=None, ge=0)
    gpu_samples: int = Field(ge=0)
    gpu_memory_byte_seconds: Decimal | None = Field(default=None, ge=0)
    gpu_peak_memory_bytes: int | None = Field(default=None, ge=0)
    gpu_sm_activity_seconds_estimate: Decimal | None = Field(default=None, ge=0)
    gpu_request_compute_seconds: Decimal | None = Field(default=None, ge=0)
    gpu_samples_without_utilization: int = Field(ge=0)
    reconciled_at: datetime

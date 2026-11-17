"""Models for Sinapsis jobs."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

# TODO import from core
AgentDefinition = dict[str, Any]


class JobSubmission(BaseModel):
    """Response returned after submitting a job."""

    model_config = ConfigDict(extra="ignore")

    job_id: str


#
class JobStatus(BaseModel):
    """Current status of a Sinapsis job.

    Args:
        job_id: ID of the job.
        state: Current state of the job.
        updated_at: Time at which the job status was last updated.
        heartbeat: Most recent heartbeat reported by the job.
        error: Error information if the job failed.
        result_url: URL from which the job result can be retrieved.
        agent_name: Name of the agent associated with the job.
        agent_def: Agent definition when verbose status information was requested.
    """

    model_config = ConfigDict(extra="ignore")

    job_id: str
    state: str
    updated_at: datetime | None = None
    heartbeat: datetime | None = None
    error: str | None = None
    result_url: str | None = None
    agent_name: str | None = None
    agent_def: AgentDefinition | None = None

    @property
    def is_complete(self) -> bool:
        """Whether the job has reached a terminal state."""
        return self.state.lower() in {"completed", "failed", "cancelled", "canceled"}

    @property
    def has_error(self) -> bool:
        """Whether the job has reported an error."""
        return self.error is not None


class JobResultItem(BaseModel):
    """A single result produced by an agent."""

    model_config = ConfigDict(extra="allow")

    agent_id: str
    timestamp: datetime
    template_name: str
    status: str
    output: Any = None
    error: str | None = None


class JobResult(BaseModel):
    """The final result of a Sinapsis job."""

    model_config = ConfigDict(extra="allow")

    agent_id: str
    agent_status: str
    agent_error: str | None = None
    timestamp: datetime
    data: list[JobResultItem]

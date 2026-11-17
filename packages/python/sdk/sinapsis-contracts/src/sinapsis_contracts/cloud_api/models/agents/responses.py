from typing import Literal

from pydantic import BaseModel, ConfigDict

from sinapsis_contracts.cloud_api.models.agents.payloads import StrictAgentSchema


class AgentCreateResponse(BaseModel):
    job_id: str


class AgentStatusResponse(BaseModel):
    job_id: str
    state: str
    updated_at: float
    heartbeat: float
    error: str | None = None
    result_url: str | None = None
    agent_name: str
    agent_def: StrictAgentSchema | None = None


class AgentListResponse(BaseModel):
    user_id: str
    active_jobs: dict[str, str]


class AgentCancelResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["cancelled"]

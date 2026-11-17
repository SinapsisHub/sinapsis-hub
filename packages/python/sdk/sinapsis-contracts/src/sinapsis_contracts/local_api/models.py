"""Public HTTP API models."""

from pydantic import BaseModel, Field


class StartJobRequest(BaseModel):
    """Start a finite job with a base64-encoded serialized DataContainer."""

    agent_id: str
    job_id: str | None = None
    payload: str | None = Field(default=None, description="Base64-encoded serialized DataContainer.")


class ApprovalRequest(BaseModel):
    request_id: str
    approved: bool


class HealthResponse(BaseModel):
    status: str
    stream_id: str


class AgentResponse(BaseModel):
    agent_id: str
    status: str
    stream_id: str | None = None


class AgentsResponse(BaseModel):
    agents: list[str]
    stream_id: str


class StartJobResponse(BaseModel):
    job_id: str
    agent_id: str
    status: str


class JobResponse(BaseModel):
    job_id: str
    agent_id: str
    instance_id: str
    status: str
    error: str | None = None


class JobActionResponse(BaseModel):
    job_id: str
    accepted: bool


class ApprovalResponse(BaseModel):
    job_id: str
    request_id: str
    accepted: bool

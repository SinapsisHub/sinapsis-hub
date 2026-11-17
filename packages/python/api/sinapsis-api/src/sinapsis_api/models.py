"""Router-owned runtime records."""

import asyncio
from dataclasses import dataclass, field
from typing import Any

from sinapsis_api.constants import JobStatus


@dataclass(slots=True)
class AgentHandle:
    """A live OS process for one logical agent."""

    agent_id: str
    instance_id: str
    process: asyncio.subprocess.Process
    identity: bytes
    agent_definition: dict[str, Any]
    ready: asyncio.Event = field(default_factory=asyncio.Event)


@dataclass(slots=True)
class JobRecord:
    """Control-plane job state independent of opaque event semantics."""

    job_id: str
    agent_id: str
    instance_id: str
    status: str = JobStatus.QUEUED.value
    error: str | None = None

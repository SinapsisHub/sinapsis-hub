from dataclasses import dataclass

from sinapsis_contracts.common.paths import BaseApiPaths


@dataclass(frozen=True)
class AgentPaths:
    base: str = f"{BaseApiPaths.base}/agents"
    item: str = "/{job_id}"
    cancel: str = "/{job_id}/cancel"
    stream: str = "/{job_id}/stream"
    results: str = "/{job_id}/results"
    events: str = "/{job_id}/events"
    retry: str = "/{job_id}/retry"


AGENT_PATHS = AgentPaths()

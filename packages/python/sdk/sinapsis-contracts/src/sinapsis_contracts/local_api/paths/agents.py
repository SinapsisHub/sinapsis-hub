from dataclasses import dataclass

from sinapsis_contracts.common.paths import BaseApiPaths


@dataclass(frozen=True)
class _AgentPaths:
    base: str = f"{BaseApiPaths.base}/agents"
    start: str = ""
    agent: str = "/{agent_id}"
    events: str = "/{agent_id}/events"
    events_ws: str = "/{agent_id}/events/ws"


API_AGENT_PATHS = _AgentPaths()

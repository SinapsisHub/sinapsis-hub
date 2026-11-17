"“”Authenticated Management endpoints for owned saved agents and versions.“”"

from dataclasses import dataclass

from sinapsis_contracts.common.paths import BaseApiPaths


@dataclass(frozen=True, slots=True)
class SavedAgentPaths:
    base: str = f"{BaseApiPaths.base}/management/agents"
    register: str = "/register"
    agent: str = "/{agent_id}"
    versions: str = "/{agent_id}/versions"
    version: str = "/{agent_id}/versions/{version_id}"


SAVED_AGENT_PATHS = SavedAgentPaths()

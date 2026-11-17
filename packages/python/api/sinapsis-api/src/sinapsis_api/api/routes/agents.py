"""Agent API routes."""

import uuid

from fastapi import APIRouter, Query, WebSocket
from fastapi.responses import Response
from sinapsis.agent import AgentSchema
from sinapsis_contracts.common.constants import ApiConstants
from sinapsis_contracts.local_api.models import AgentResponse, AgentsResponse
from sinapsis_contracts.local_api.paths import API_AGENT_PATHS

from sinapsis_api.constants import AgentStatus, ControlType
from sinapsis_api.env_vars import SINAPSIS_API_EVENT_REPLAY_LIMIT

from ._common import (
    command,
    encode_replay_body,
    require_success,
    router_client,
    stream_agent_events,
)

agents_router = APIRouter(prefix=API_AGENT_PATHS.base)


@agents_router.post(API_AGENT_PATHS.start, response_model=AgentResponse, status_code=201, tags=["agents"])
async def start_agent(agent_definition: AgentSchema) -> AgentResponse:
    if not agent_definition.agent.attributes.agent_id:
        agent_definition.agent.attributes.agent_id = str(uuid.uuid4())

    agent_id = agent_definition.agent.attributes.agent_id

    response = require_success(
        await router_client.request(
            command(
                ControlType.START_AGENT,
                agent_id=agent_id,
                agent_definition=agent_definition.model_dump(mode="json"),
            )
        )
    )

    return AgentResponse(agent_id=agent_id, status=AgentStatus.RUNNING.value, stream_id=response["stream_id"])


@agents_router.delete(API_AGENT_PATHS.agent, response_model=AgentResponse, tags=["agents"])
async def stop_agent(agent_id: str) -> AgentResponse:
    require_success(await router_client.request(command(ControlType.STOP_AGENT, agent_id=agent_id)))

    return AgentResponse(agent_id=agent_id, status=AgentStatus.STOPPED.value)


@agents_router.get(API_AGENT_PATHS.base, response_model=AgentsResponse, tags=["agents"])
async def list_agents() -> AgentsResponse:
    response = require_success(await router_client.request(command(ControlType.LIST_AGENTS)))

    return AgentsResponse(agents=response["agents"], stream_id=response["stream_id"])


@agents_router.get(API_AGENT_PATHS.events, tags=["events"])
async def replay_agent_events(
    agent_id: str,
    after: int = Query(default=0, ge=0),
    job_id: str | None = None,
    limit: int = Query(default=SINAPSIS_API_EVENT_REPLAY_LIMIT, ge=1, le=SINAPSIS_API_EVENT_REPLAY_LIMIT),
) -> Response:
    page = await router_client.replay(agent_id=agent_id, after=after, job_id=job_id, limit=limit)

    metadata = page.metadata

    headers = {
        ApiConstants.headers.stream_id: str(metadata["stream_id"]),
        ApiConstants.headers.oldest_cursor: str(metadata["oldest_cursor"]),
        ApiConstants.headers.latest_cursor: str(metadata["latest_cursor"]),
        ApiConstants.headers.next_cursor: str(metadata["next_cursor"]),
        ApiConstants.headers.truncated: str(bool(metadata["truncated"])).lower(),
        ApiConstants.headers.has_more: str(bool(metadata["has_more"])).lower(),
    }

    return Response(
        content=encode_replay_body(page.events),
        media_type="application/x-sinapsis-events",
        headers=headers,
    )


@agents_router.websocket(API_AGENT_PATHS.events_ws)
async def agent_event_socket(
    websocket: WebSocket, agent_id: str, after: int | None = None, job_id: str | None = None
) -> None:
    await stream_agent_events(websocket, agent_id=agent_id, after=after, job_id=job_id)

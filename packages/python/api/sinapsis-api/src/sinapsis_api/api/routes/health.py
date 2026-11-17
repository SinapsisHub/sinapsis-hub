"""Health API routes."""

from fastapi import APIRouter
from sinapsis_contracts.common.paths import API_HEALTH_PATHS
from sinapsis_contracts.local_api.models import HealthResponse

from sinapsis_api.constants import ControlType

from ._common import command, require_success, router_client

health_router = APIRouter()


@health_router.get(API_HEALTH_PATHS.base, response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    agent_router_response = await router_client.request(command(ControlType.HEALTH))
    response = require_success(agent_router_response)
    return HealthResponse(status=response["status"], stream_id=response["stream_id"])

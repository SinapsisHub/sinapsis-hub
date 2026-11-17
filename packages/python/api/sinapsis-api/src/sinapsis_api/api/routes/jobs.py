"""Job API routes."""

import uuid

from fastapi import APIRouter, WebSocket
from sinapsis_contracts.local_api.models import (
    ApprovalRequest,
    ApprovalResponse,
    JobActionResponse,
    JobResponse,
    StartJobRequest,
    StartJobResponse,
)
from sinapsis_contracts.local_api.paths import API_JOB_PATHS

from sinapsis_api.constants import ControlType, JobStatus

from ._common import (
    command,
    decode_job_payload,
    require_success,
    router_client,
    stream_agent_events,
)

jobs_router = APIRouter(prefix=API_JOB_PATHS.base)


@jobs_router.post(API_JOB_PATHS.start, response_model=StartJobResponse, status_code=202, tags=["jobs"])
async def start_job(body: StartJobRequest) -> StartJobResponse:
    job_id = body.job_id or str(uuid.uuid4())

    require_success(
        await router_client.request(
            command(
                ControlType.START_JOB,
                job_id=job_id,
                agent_id=body.agent_id,
                payload=decode_job_payload(body.payload),
            )
        )
    )

    return StartJobResponse(job_id=job_id, agent_id=body.agent_id, status=JobStatus.QUEUED.value)


@jobs_router.get(API_JOB_PATHS.job, response_model=JobResponse, tags=["jobs"])
async def get_job(job_id: str) -> JobResponse:
    response = require_success(await router_client.request(command(ControlType.GET_JOB, job_id=job_id)))

    return JobResponse.model_validate(response["job"])


@jobs_router.post(API_JOB_PATHS.cancel, response_model=JobActionResponse, status_code=202, tags=["jobs"])
async def cancel_job(job_id: str) -> JobActionResponse:
    require_success(await router_client.request(command(ControlType.CANCEL_JOB, job_id=job_id)))

    return JobActionResponse(job_id=job_id, accepted=True)


@jobs_router.post(API_JOB_PATHS.feedback, response_model=ApprovalResponse, status_code=202, tags=["jobs"])
async def feedback(job_id: str, body: ApprovalRequest) -> ApprovalResponse:
    require_success(
        await router_client.request(
            command(
                ControlType.APPROVAL_RESPONSE,
                job_id=job_id,
                request_id=body.request_id,
                approved=body.approved,
            )
        )
    )

    return ApprovalResponse(job_id=job_id, request_id=body.request_id, accepted=True)


@jobs_router.websocket(API_JOB_PATHS.events)
async def job_event_socket(websocket: WebSocket, job_id: str, after: int | None = None) -> None:
    response = require_success(await router_client.request(command(ControlType.GET_JOB, job_id=job_id)))

    await stream_agent_events(websocket, agent_id=response["job"]["agent_id"], after=after, job_id=job_id)

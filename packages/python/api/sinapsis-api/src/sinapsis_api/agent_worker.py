"""Isolated Sinapsis agent subprocess."""

import argparse
import asyncio
from dataclasses import dataclass
from typing import Any

import zmq
import zmq.asyncio
from sinapsis.agent import AgentMode
from sinapsis.logging import sinapsis_logger
from sinapsis_protocol import (
    EventType,
    SSEEnvelope,
    deserialize_data_container,
    serialize_sse_envelope,
)

from sinapsis_api.constants import ControlType, JobStatus, WorkerFrame
from sinapsis_api.env_vars import (
    SINAPSIS_API_WORKER_OUTBOUND_QUEUE_SIZE,
    SINAPSIS_API_ZMQ_RECEIVE_HWM,
    SINAPSIS_API_ZMQ_SEND_HWM,
)
from sinapsis_api.protocol import pack_control, unpack_control
from sinapsis_api.sinapsis_runtime import build_agent, execute_agent


@dataclass(slots=True)
class AgentContext:
    """Application event boundary exposed to an executing agent job."""

    agent_id: str
    instance_id: str
    outbound: asyncio.Queue[tuple[bytes, ...]]
    inbound: asyncio.Queue[dict[str, Any]]
    job_id: str | None = None

    async def send(
        self,
        data: Any = None,
        *,
        event_type: EventType = EventType.DATA,
        agent_status: Any = None,
        errors: tuple[Any, ...] = (),
        request_type: Any = None,
    ) -> None:
        """Serialize one SSEEnvelope at the worker/application boundary."""
        envelope = SSEEnvelope(
            agent_id=self.agent_id,
            agent_status=agent_status,
            data=data,
            errors=errors,
            event_type=event_type,
            request_type=request_type,
            job_id=self.job_id,
        )
        await self.send_envelope(envelope)

    async def send_envelope(self, envelope: SSEEnvelope) -> None:
        """Serialize and queue an application envelope exactly once."""
        await self.outbound.put(
            (
                WorkerFrame.EVENT.value,
                (self.job_id or "").encode(),
                serialize_sse_envelope(envelope),
            )
        )

    async def receive(self) -> dict[str, Any]:
        """Wait for a routed control response such as approval feedback."""
        return await self.inbound.get()


class AgentWorker:
    """Own one Sinapsis Agent inside an isolated OS process."""

    def __init__(self, endpoint: str, agent_id: str, instance_id: str) -> None:
        self.endpoint = endpoint
        self.agent_id = agent_id
        self.instance_id = instance_id
        self.zmq_context = zmq.asyncio.Context.instance()
        self.socket = self.zmq_context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.setsockopt(zmq.SNDHWM, SINAPSIS_API_ZMQ_SEND_HWM)
        self.socket.setsockopt(zmq.RCVHWM, SINAPSIS_API_ZMQ_RECEIVE_HWM)
        self.socket.setsockopt(zmq.IDENTITY, f"agent:{agent_id}:{instance_id}".encode())
        self.outbound: asyncio.Queue[tuple[bytes, ...]] = asyncio.Queue(maxsize=SINAPSIS_API_WORKER_OUTBOUND_QUEUE_SIZE)
        self.contexts: dict[str, AgentContext] = {}
        self.tasks: dict[str, asyncio.Task[None]] = {}
        self.production_task: asyncio.Task[None] | None = None
        self.agent: Any | None = None
        self.stopping = False

    async def run(self) -> None:
        """Connect to the Router and process commands until stopped."""
        self.socket.connect(self.endpoint)
        await self.socket.send_multipart(
            [
                WorkerFrame.HELLO.value,
                pack_control({"agent_id": self.agent_id, "instance_id": self.instance_id}),
            ]
        )
        sender_task = asyncio.create_task(self._sender())
        try:
            while not self.stopping:
                frames = await self.socket.recv_multipart(copy=False)
                if bytes(frames[0]) != WorkerFrame.COMMAND.value:
                    continue
                try:
                    await self._handle_command(unpack_control(frames[1].buffer))
                except Exception:
                    sinapsis_logger.exception("Agent worker failed to handle a command for agent %s.", self.agent_id)
                    raise
        except Exception:
            sinapsis_logger.exception("Agent worker failed for agent %s.", self.agent_id)
            raise
        finally:
            for task in tuple(self.tasks.values()):
                task.cancel()
            if self.production_task is not None:
                self.production_task.cancel()
            sender_task.cancel()
            await asyncio.gather(*self.tasks.values(), sender_task, return_exceptions=True)
            if self.production_task is not None:
                await asyncio.gather(self.production_task, return_exceptions=True)
            self.socket.close()

    async def _handle_command(self, command: dict[str, Any]) -> None:
        command_type = ControlType(command["type"])
        if command_type == ControlType.INIT:
            self.agent = build_agent(command["agent_definition"])
            await self.socket.send_multipart([WorkerFrame.READY.value, pack_control({"agent_id": self.agent_id})])
            if self.agent.agent_attributes.agent_mode == AgentMode.LOOP_FOREVER:
                context = AgentContext(
                    agent_id=self.agent_id,
                    instance_id=self.instance_id,
                    outbound=self.outbound,
                    inbound=asyncio.Queue(),
                )
                self.production_task = asyncio.create_task(execute_agent(self.agent, None, context, production=True))
            return
        if command_type == ControlType.STOP:
            self.stopping = True
            return
        if command_type == ControlType.START_JOB:
            await self._start_job(command)
            return
        if command_type == ControlType.CANCEL_JOB:
            task = self.tasks.get(command["job_id"])
            if task is not None:
                task.cancel()
            return
        if command_type == ControlType.APPROVAL_RESPONSE:
            context = self.contexts.get(command["job_id"])
            if context is not None:
                await context.inbound.put(command)
            return
        sinapsis_logger.error("Unsupported worker command: %s.", command_type.value)
        raise ValueError(f"Unsupported worker command: {command_type.value}.")

    async def _start_job(self, command: dict[str, Any]) -> None:
        if self.agent is None:
            sinapsis_logger.error("Start-job received before agent initialization for %s.", self.agent_id)
            raise RuntimeError("Agent worker is not initialized.")
        job_id = command["job_id"]
        if job_id in self.tasks:
            return
        payload_bytes = command.get("payload")
        payload = deserialize_data_container(payload_bytes) if payload_bytes is not None else None
        context = AgentContext(
            agent_id=self.agent_id,
            instance_id=self.instance_id,
            job_id=job_id,
            outbound=self.outbound,
            inbound=asyncio.Queue(),
        )
        self.contexts[job_id] = context
        self.tasks[job_id] = asyncio.create_task(self._run_job(context, payload))

    async def _run_job(self, context: AgentContext, payload: Any) -> None:
        try:
            await self._send_job_state(context.job_id, JobStatus.RUNNING)

            await execute_agent(self.agent, payload, context)

            # execute_agent() has exhausted the finite execution here.
            # COMPLETED is placed onto the same FIFO outbound queue after all
            # events emitted by context.send().
            await self._send_job_state(context.job_id, JobStatus.COMPLETED)

        except asyncio.CancelledError:
            await self._send_job_state(context.job_id, JobStatus.CANCELLED)
            raise

        except Exception as exception:
            sinapsis_logger.exception("Job %s failed in agent %s.", context.job_id, self.agent_id)
            await self._send_job_state(context.job_id, JobStatus.FAILED, str(exception))

        finally:
            if context.job_id is not None:
                self.contexts.pop(context.job_id, None)
                self.tasks.pop(context.job_id, None)

    async def _send_job_state(self, job_id: str | None, status: JobStatus, error: str | None = None) -> None:
        if job_id is None:
            return
        await self.outbound.put(
            (
                WorkerFrame.JOB_STATE.value,
                pack_control({"job_id": job_id, "status": status.value, "error": error}),
            )
        )

    async def _sender(self) -> None:
        while True:
            frames = await self.outbound.get()
            try:
                await self.socket.send_multipart(list(frames), copy=False)
            finally:
                self.outbound.task_done()


def parse_args() -> argparse.Namespace:
    """Parse subprocess command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--instance-id", required=True)
    return parser.parse_args()


async def main() -> None:
    """Run the agent worker entry point."""
    arguments = parse_args()
    await AgentWorker(arguments.endpoint, arguments.agent_id, arguments.instance_id).run()


if __name__ == "__main__":
    asyncio.run(main())

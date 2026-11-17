"""Narrow integration boundary with the Sinapsis agent runtime."""

import asyncio
from typing import TYPE_CHECKING, Any

from sinapsis.agent import Agent, AgentMode, AgentSchema
from sinapsis.data_transport import DataContainer
from sinapsis.logging import sinapsis_logger

if TYPE_CHECKING:
    from sinapsis_api.agent_worker import AgentContext


def build_agent(agent_definition: dict[str, Any]) -> Agent:
    """Build a Sinapsis Agent from its validated schema definition."""
    schema = AgentSchema.model_validate(agent_definition)
    return Agent(schema)


async def execute_agent(
    agent: Agent,
    payload: DataContainer | None,
    context: "AgentContext",
    *,
    production: bool = False,
) -> None:
    """Execute the configured Sinapsis mode without blocking IPC handling."""
    mode = agent.agent_attributes.agent_mode
    if mode == AgentMode.LOOP_FOREVER:
        if not production:
            sinapsis_logger.error("LOOP_FOREVER agent invoked as a finite job.")
            raise ValueError("LOOP_FOREVER agents must execute as production tasks.")
        await asyncio.to_thread(agent, agent_mode=AgentMode.LOOP_FOREVER)
        return
    payload = payload if isinstance(payload, DataContainer) else DataContainer()

    if production:
        sinapsis_logger.error("Finite agent mode %s invoked as production.", mode)
        raise ValueError(f"{mode} is a job execution mode, not a production mode.")
    if not isinstance(payload, DataContainer):
        sinapsis_logger.error("Job payload did not deserialize to DataContainer.")
        raise TypeError("Job payload must deserialize to DataContainer.")

    if mode == AgentMode.SINGLE:
        result = await asyncio.to_thread(agent, payload, agent_mode=AgentMode.SINGLE)
        if result is not None:
            await context.send(result)
        return

    if mode == AgentMode.GENERATOR:
        generator = agent(payload, agent_mode=AgentMode.GENERATOR)
        sentinel = object()

        def next_result() -> Any:
            return next(generator, sentinel)

        num_iterations = 0
        while True:
            result = await asyncio.to_thread(next_result)
            print("calling next iteration ", num_iterations)
            num_iterations += 1

            if result is sentinel:
                return
            await context.send(result)

    sinapsis_logger.error("Unsupported agent mode: %s.", mode)
    raise ValueError(f"Unsupported agent mode: {mode}.")

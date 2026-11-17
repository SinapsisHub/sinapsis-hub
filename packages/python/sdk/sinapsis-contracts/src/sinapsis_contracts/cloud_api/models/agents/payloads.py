# -*- coding: utf-8 -*-

from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from sinapsis.agent import AgentAttributes, AgentDef, AgentSchema


class StrictAgentAttributes(AgentAttributes):
    user_id: str
    agent_id: str


class StrictAgentDef(AgentDef):
    attributes: StrictAgentAttributes = Field(default_factory=StrictAgentAttributes)


class StrictAgentSchema(AgentSchema):
    agent: StrictAgentDef


class InlineAgentExecutionRequest(BaseModel):
    """Submit any valid runtime graph without saving an agent or version.

    Identity, template permissions and resource budgets are verified by the server.
    """

    model_config = ConfigDict(extra="forbid")
    agent_definition: dict[str, Any]

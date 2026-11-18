from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from sinapsis.agent import SinapsisStatusCodes
from sinapsis.data_transport import DataContainer
from sinapsis.sentinels import SinapsisSentinel


@dataclass
class AgentResponseFieldNames:
    """Dataclass to handle Agent Response messages"""

    agent_id: str = "agent_id"
    agent_status: str = "agent_status"
    template_data: str = "template_data"
    timestamp: str = "timestamp"
    agent_error: str = "agent_error"


@dataclass
class TemplateResponseFieldNames:
    """Dataclass to handle Template Response messages"""

    template_name: str = "template_name"
    error: str = "error"
    output: str = "output"
    status: str = "status"


class TemplateStreamingResponse(BaseModel):
    """Basemodel where information regarding the template response is contained.
    It includes the agent_id, the time of execution, template name, template status, the output container
    from that template, if there has been any execution errors.
    """

    parent_agent_id: str
    timestamp: datetime
    template_name: str
    template_status: SinapsisStatusCodes
    template_output_container: DataContainer | SinapsisSentinel
    template_error: str | None = None
    model_config = ConfigDict(arbitrary_types_allowed=True)


class AgentResponse(BaseModel):
    """Basemodel for the Agent response to be added in the SSE message.
    It includes the agent_id, the time of execution, template name, template status,
    the output container and execution errors.
    """

    agent_id: str
    timestamp: datetime
    template_name: str
    status: SinapsisStatusCodes
    output: DataContainer | str
    error: str | None = None


class SSEMessage(BaseModel):
    """Schema for Server-Sent Events (SSE) emitted during agent execution.

    This model defines the structured data packet used for real-time
    communication between the execution engine and external consumers. It
    tracks the agent's lifecycle state, payload delivery, and error reporting
    within a streaming context.

    Attributes:
        agent_id: Unique identifier for the agent instance being executed.
        agent_status: The current phase of execution (e.g., 'queued', 'processing', 'completed', 'failed').
        template_data: A list of `AgentResponse` objects containing the
            Agent response per template; defaults to None if the agent hasn't produced data yet.
        agent_error: Descriptive error message if the execution fails.
        timestamp: The UTC time when the message was generated.
    """

    agent_id: str
    agent_status: str
    template_data: list[AgentResponse] | None = None
    agent_error: str | None = None
    timestamp: datetime = datetime.now()

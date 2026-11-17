from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, slots=True)
class _AgentJobState:
    QUEUED: ClassVar[str] = "QUEUED"  # Waiting in queue
    PROCESSING: ClassVar[str] = "PROCESSING"  # Active and running
    UPLOADING: ClassVar[str] = "UPLOADING"  # Done and uploading artifacts
    COMPLETED: ClassVar[str] = "COMPLETED"  # Success
    FAILED: ClassVar[str] = "FAILED"  # Exception raised
    CANCELLED: ClassVar[str] = "CANCELLED"  # User terminated


SINAPSIS_AGENT_STATE = _AgentJobState()

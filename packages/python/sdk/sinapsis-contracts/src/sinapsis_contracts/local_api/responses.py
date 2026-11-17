# sinapsis_contracts/api/responses.py

from pydantic import BaseModel, ConfigDict


class OperationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str

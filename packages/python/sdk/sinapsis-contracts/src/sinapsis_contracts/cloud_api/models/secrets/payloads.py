from pydantic import BaseModel, Field


class CreateSecretRequest(BaseModel):
    label: str = Field(min_length=3, max_length=64)
    secret: str = Field(min_length=3, max_length=64)

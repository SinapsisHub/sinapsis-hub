from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApiKeyGenerateResponse(BaseModel):
    api_key_name: str
    api_key: str = Field(pattern=r"^sk_.+-\*{5}$")


class ApiKeyListResponse(BaseModel):
    keys: list[ApiKeyGenerateResponse]


class ApiKeyResponse(BaseModel):
    key: str


class ApiKeyValidateResponse(BaseModel):
    valid: bool


class UserSecretResponse(BaseModel):
    """ "
    Does NOT hold the actual secret value
    """

    id: UUID
    label: str
    model_config = ConfigDict(extra="ignore")


class UserSecretListResponse(BaseModel):
    secrets: list[UserSecretResponse]


class DeleteSecretResponse(BaseModel):
    status: str = "success"
    deleted_id: UUID

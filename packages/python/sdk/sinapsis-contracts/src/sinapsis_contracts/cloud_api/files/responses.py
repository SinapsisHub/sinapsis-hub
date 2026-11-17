from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    path: str
    size: int | float
    status: str
    filename: str
    mime_type: str
    sha256: str


class DeleteFileResponse(BaseModel):
    path: str
    freed: int | float
    status: str = "deleted"

"""Models for Sinapsis webhook integrations."""

import base64
import json
import mimetypes
from pathlib import Path
from uuid import UUID

from pydantic import BaseModel, model_validator


class TriggerPayload(BaseModel):
    file_id: UUID | str
    agent_id: UUID | str
    content: str | bytes
    content_type: str

    @model_validator(mode="before")
    @classmethod
    def infer_content_type(cls, values: dict) -> dict:
        if values.get("content_type"):
            return values

        content = values.get("content")

        if isinstance(content, str):
            content_type, _ = mimetypes.guess_type(content)
            if content_type:
                values["content_type"] = content_type

        if not values.get("content_type"):
            raise ValueError("content_type must be provided when it cannot be inferred from content")

        return values

    def _read_content(self) -> bytes:
        if isinstance(self.content, bytes):
            return self.content

        return Path(self.content).read_bytes()

    def dump_body(self) -> bytes:
        content = self._read_content()

        payload = {
            "file_id": str(self.file_id),
            "agent_id": str(self.agent_id),
            "content": base64.b64encode(content).decode("ascii"),
            "content_type": self.content_type,
        }

        return json.dumps(payload, separators=(",", ":")).encode("utf-8")

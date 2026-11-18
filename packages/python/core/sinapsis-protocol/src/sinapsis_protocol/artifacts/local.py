import hashlib
import mimetypes
import os
import re
import shutil
from pathlib import Path
from typing import Any, Mapping

from sinapsis_protocol.artifacts.base import ArtifactStore
from sinapsis_protocol.artifacts.ref import ArtifactRef
from sinapsis_protocol.errors import ArtifactError

_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_component(value: str) -> str:
    cleaned = _SAFE.sub("_", value).strip(".")
    if not cleaned or cleaned in {".", ".."}:
        raise ArtifactError("Invalid artifact path component")
    return cleaned


class LocalArtifactStore(ArtifactStore):
    def __init__(self, root: str | os.PathLike[str], username: str, agent_id: str) -> None:
        self.root = Path(root)
        self.username = _safe_component(username)
        self.agent_id = _safe_component(agent_id)
        self.base = self.root / self.username / self.agent_id
        self.base.mkdir(parents=True, exist_ok=True)

    def _ref(
        self,
        path: Path,
        *,
        filename: str,
        mime_type: str | None,
        metadata: Mapping[str, Any] | None,
        sha256: str | None = None,
        size: int | None = None,
    ) -> ArtifactRef:
        if sha256 is None or size is None:
            data = path.read_bytes()
            sha256 = hashlib.sha256(data).hexdigest()
            size = len(data)
        digest = sha256
        return ArtifactRef(
            artifact_id=digest,
            filename=filename,
            size=size,
            sha256=digest,
            mime_type=mime_type or mimetypes.guess_type(filename)[0],
            uri=f"artifact://{digest}",
            extras=dict(metadata or {}),
        )

    def put_bytes(
        self, data: bytes, *, filename: str, mime_type: str | None = None, metadata: Mapping[str, Any] | None = None
    ) -> ArtifactRef:
        safe_name = _safe_component(Path(filename).name)
        digest = hashlib.sha256(data).hexdigest()
        path = self.base / digest
        if not path.exists():
            path.write_bytes(data)
        elif path.stat().st_size != len(data):
            raise ArtifactError(f"Existing artifact has unexpected size: {digest}")
        return self._ref(
            path, filename=safe_name, mime_type=mime_type, metadata=metadata, sha256=digest, size=len(data)
        )

    def put_file(
        self,
        path: str,
        *,
        filename: str | None = None,
        mime_type: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> ArtifactRef:
        source = Path(path)
        if not source.is_file():
            raise ArtifactError(f"File does not exist: {source}")
        safe_name = _safe_component(Path(filename or source.name).name)
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        destination = self.base / digest
        if not destination.exists():
            if source.resolve() == destination.resolve():
                return self._ref(
                    destination,
                    filename=safe_name,
                    mime_type=mime_type,
                    metadata=metadata,
                    sha256=digest,
                    size=source.stat().st_size,
                )
            shutil.copy2(source, destination)
        elif destination.stat().st_size != source.stat().st_size:
            raise ArtifactError(f"Existing artifact has unexpected size: {digest}")
        return self._ref(
            destination,
            filename=safe_name,
            mime_type=mime_type,
            metadata=metadata,
            sha256=digest,
            size=source.stat().st_size,
        )

    def read_bytes(self, artifact: ArtifactRef) -> bytes:
        # artifact_id is the content identity. filename is only descriptive metadata
        # and is not unique (e.g. every tensor codec uses ``tensor.bin``).
        path = self.base / artifact.artifact_id
        if not path.is_file():
            raise ArtifactError(f"Artifact not found: {artifact.artifact_id}")
        data = path.read_bytes()
        if len(data) != artifact.size:
            raise ArtifactError(f"Size mismatch for artifact {artifact.artifact_id}")
        if hashlib.sha256(data).hexdigest() != artifact.sha256:
            raise ArtifactError(f"Checksum mismatch for artifact {artifact.artifact_id}")
        return data

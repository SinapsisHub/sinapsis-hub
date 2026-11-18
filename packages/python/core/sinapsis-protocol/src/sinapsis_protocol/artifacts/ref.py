from typing import Any

from sinapsis.data_transport import dataclass


@dataclass(frozen=True, slots=True)
class ArtifactRef:
    """Reference to externally stored payload bytes."""

    artifact_id: str
    filename: str
    size: int
    sha256: str
    mime_type: str | None = None
    uri: str | None = None
    extras: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.extras is None:
            object.__setattr__(self, "extras", {})

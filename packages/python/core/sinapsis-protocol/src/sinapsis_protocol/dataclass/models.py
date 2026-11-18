from typing import Any

from sinapsis.data_transport import dataclass


@dataclass(frozen=True, slots=True)
class DataclassWire:
    name: str
    version: int
    fields: dict[str, Any]

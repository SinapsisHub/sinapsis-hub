from sinapsis_protocol.dataclass.decode import decode_dataclass
from sinapsis_protocol.dataclass.encode import encode_dataclass
from sinapsis_protocol.dataclass.models import DataclassWire
from sinapsis_protocol.dataclass.registry import DataclassRegistry, DataclassSpec

__all__ = ["DataclassRegistry", "DataclassSpec", "DataclassWire", "decode_dataclass", "encode_dataclass"]

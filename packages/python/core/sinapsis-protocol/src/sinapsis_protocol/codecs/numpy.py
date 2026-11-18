import numpy as np

from sinapsis_protocol.codecs.base import make_payload, read_payload
from sinapsis_protocol.types import Adapter as AdapterBase
from sinapsis_protocol.types import DecodeContext, EncodeContext
from sinapsis_protocol.wire.constants import PayloadCodec
from sinapsis_protocol.wire.models import ArrayMetadata, PayloadDescriptor, TransportValue


class Adapter(AdapterBase):
    type_name = "array"
    library = "numpy"
    version = 1

    @classmethod
    def can_encode(cls, value: object) -> bool:
        return isinstance(value, np.ndarray)

    @classmethod
    def encode(cls, value: object, context: EncodeContext) -> TransportValue:
        array = np.ascontiguousarray(value)
        data = array.tobytes(order="C")
        return TransportValue(
            descriptor=PayloadDescriptor(cls.type_name, cls.version, cls.library, PayloadCodec.RAW),
            metadata=ArrayMetadata(shape=tuple(array.shape), dtype=array.dtype.str, order="C"),
            payload=make_payload(data, context, filename="array.bin", mime_type="application/octet-stream"),
        )

    @classmethod
    def decode(cls, value: TransportValue, context: DecodeContext) -> object:
        metadata = value.metadata
        if not isinstance(metadata, ArrayMetadata):
            raise TypeError("NumPy payload requires ArrayMetadata")
        data = read_payload(value.payload, context)
        dtype = np.dtype(metadata.dtype)
        expected = int(np.prod(metadata.shape, dtype=np.int64)) * dtype.itemsize
        if expected != len(data) or len(data) > context.limits.max_array_bytes:
            raise ValueError("Array payload size does not match metadata")
        return np.frombuffer(data, dtype=dtype).reshape(metadata.shape).copy()

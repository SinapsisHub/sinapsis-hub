import ctypes
import math

import torch

from sinapsis_protocol.codecs.base import make_payload, read_payload
from sinapsis_protocol.types import Adapter as AdapterBase
from sinapsis_protocol.types import DecodeContext, EncodeContext
from sinapsis_protocol.wire.constants import PayloadCodec
from sinapsis_protocol.wire.models import PayloadDescriptor, TorchMetadata, TransportValue

_SUPPORTED_DTYPES = {
    torch.bool,
    torch.uint8,
    torch.int8,
    torch.int16,
    torch.int32,
    torch.int64,
    torch.float16,
    torch.float32,
    torch.float64,
    torch.complex64,
    torch.complex128,
}


class Adapter(AdapterBase):
    type_name = "array"
    library = "torch"
    version = 1

    @classmethod
    def can_encode(cls, value: object) -> bool:
        return isinstance(value, torch.Tensor)

    @classmethod
    def encode(cls, value: object, context: EncodeContext) -> TransportValue:
        tensor = value.detach().cpu().contiguous()
        if tensor.dtype not in _SUPPORTED_DTYPES:
            raise TypeError(f"Unsupported torch dtype: {tensor.dtype}")
        size = tensor.numel() * tensor.element_size()
        if size == 0:
            data = b""
        else:
            data = ctypes.string_at(tensor.data_ptr(), size)
        return TransportValue(
            descriptor=PayloadDescriptor(cls.type_name, cls.version, cls.library, PayloadCodec.RAW),
            metadata=TorchMetadata(
                shape=tuple(tensor.shape),
                dtype=str(tensor.dtype).removeprefix("torch."),
                order="C",
                device="cpu",
                requires_grad=bool(value.requires_grad),
            ),
            payload=make_payload(data, context, filename="tensor.bin", mime_type="application/octet-stream"),
        )

    @classmethod
    def decode(cls, value: TransportValue, context: DecodeContext) -> object:
        metadata = value.metadata
        if not isinstance(metadata, TorchMetadata):
            raise TypeError("Torch payload requires ArrayMetadata")
        torch_dtype = getattr(torch, metadata.dtype, None)
        if torch_dtype not in _SUPPORTED_DTYPES:
            raise TypeError(f"Unsupported torch dtype: {metadata.dtype}")
        data = read_payload(value.payload, context)
        count = math.prod(metadata.shape)
        expected = count * torch.empty((), dtype=torch_dtype).element_size()
        if expected != len(data) or len(data) > context.limits.max_array_bytes:
            raise ValueError("Tensor payload size does not match metadata")
        return torch.frombuffer(bytearray(data), dtype=torch_dtype, count=count).reshape(metadata.shape).clone()

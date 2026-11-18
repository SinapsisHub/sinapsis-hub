import cv2
import numpy as np

from sinapsis_protocol.codecs.base import make_payload, read_payload
from sinapsis_protocol.types import Adapter as AdapterBase
from sinapsis_protocol.types import DecodeContext, EncodeContext
from sinapsis_protocol.wire.constants import PayloadCodec
from sinapsis_protocol.wire.models import ImageMetadata, PayloadDescriptor, TransportValue


class Adapter(AdapterBase):
    type_name = "image"
    library = "opencv"
    version = 1

    @classmethod
    def can_encode(cls, value: object) -> bool:
        return isinstance(value, np.ndarray) and value.dtype == np.uint8 and value.ndim in (2, 3)

    @classmethod
    def encode(cls, value: object, context: EncodeContext) -> TransportValue:
        array = np.ascontiguousarray(value)
        ok, encoded = cv2.imencode(".png", array)
        if not ok:
            raise ValueError("OpenCV failed to encode image")
        return TransportValue(
            descriptor=PayloadDescriptor(cls.type_name, cls.version, cls.library, PayloadCodec.RAW),
            metadata=ImageMetadata(shape=tuple(array.shape), format="png"),
            payload=make_payload(encoded.tobytes(), context, filename="image.png", mime_type="image/png"),
        )

    @classmethod
    def decode(cls, value: TransportValue, context: DecodeContext) -> object:
        metadata = value.metadata
        if not isinstance(metadata, ImageMetadata):
            raise TypeError("OpenCV payload requires ImageMetadata")
        image = cv2.imdecode(np.frombuffer(read_payload(value.payload, context), dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        if image is None or tuple(image.shape) != metadata.shape:
            raise ValueError("Decoded image shape does not match metadata")
        return image

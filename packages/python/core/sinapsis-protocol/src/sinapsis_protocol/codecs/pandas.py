import io

import pandas as pd
import pyarrow as pa
import pyarrow.ipc as ipc

from sinapsis_protocol.codecs.base import make_payload, read_payload
from sinapsis_protocol.types import Adapter as AdapterBase
from sinapsis_protocol.types import DecodeContext, EncodeContext
from sinapsis_protocol.wire.constants import PayloadCodec
from sinapsis_protocol.wire.models import DataFrameMetadata, PayloadDescriptor, TransportValue


class Adapter(AdapterBase):
    type_name = "dataframe"
    library = "pandas"
    version = 1

    @classmethod
    def can_encode(cls, value: object) -> bool:
        return isinstance(value, pd.DataFrame)

    @classmethod
    def encode(cls, value: object, context: EncodeContext) -> TransportValue:
        table = pa.Table.from_pandas(value, preserve_index=True)
        sink = io.BytesIO()
        with ipc.new_stream(sink, table.schema) as writer:
            writer.write_table(table)
        return TransportValue(
            descriptor=PayloadDescriptor(cls.type_name, cls.version, cls.library, PayloadCodec.ARROW),
            metadata=DataFrameMetadata(),
            payload=make_payload(
                data=sink.getvalue(),
                context=context,
                filename="dataframe.arrow",
                mime_type="application/vnd.apache.arrow.stream",
                codec=PayloadCodec.ARROW,
            ),
        )

    @classmethod
    def decode(cls, value: TransportValue, context: DecodeContext) -> object:
        with ipc.open_stream(read_payload(value.payload, context)) as reader:
            return reader.read_all().to_pandas()

from datetime import datetime
from typing import Any

import msgpack
from sinapsis_contracts.common.sentinels import SINAPSIS_END_OF_STREAM

from sinapsis_deserialization.data_container_decoders import DataContainerDecoder
from sinapsis_deserialization.schemas.messaging_base_models import (
    AgentResponse,
    AgentResponseFieldNames,
    SSEMessage,
    TemplateResponseFieldNames,
)

data_decoder = DataContainerDecoder()


def agent_response_decoder(data: dict[str, Any]) -> AgentResponse:
    """Decodes a dictionary format back into an AgentResponse instance.

    Reconstructs datetime objects from ISO strings and resolves encoded
    DataContainer payloads back into DataContainer instances.

    Args:
        data: A dictionary containing the serialized agent response fields.

    Returns:
        An instantiated AgentResponse object.
    """
    raw_output = data.get(TemplateResponseFieldNames.output)

    # Resolve DataContainer if output was encoded as a container payload/URL
    if isinstance(raw_output, dict) and getattr(data_decoder, "is_container", lambda x: True)(raw_output):
        output = data_decoder.decode_container(raw_output)
    else:
        output = raw_output

    raw_timestamp = data.get(AgentResponseFieldNames.timestamp)
    timestamp = datetime.fromisoformat(raw_timestamp) if isinstance(raw_timestamp, str) else raw_timestamp

    return AgentResponse(
        agent_id=data.get(AgentResponseFieldNames.agent_id),
        timestamp=timestamp,
        template_name=data.get(TemplateResponseFieldNames.template_name),
        status=data.get(TemplateResponseFieldNames.status),
        output=output,
        error=data.get(TemplateResponseFieldNames.error),
    )


def sse_decoder(data: dict[str, Any]) -> SSEMessage:
    """Decodes a primitive dictionary structure back into an SSEMessage instance.

    Deserializes nested `template_data` items into `AgentResponse` objects
    and restores ISO timestamps to `datetime` objects.

    Args:
        data: The dictionary representation of an SSE message.

    Returns:
        An SSEMessage instance with fully reconstructed child objects.
    """
    raw_template_data = data.get(AgentResponseFieldNames.template_data, [])

    template_data = [agent_response_decoder(item) if isinstance(item, dict) else item for item in raw_template_data]

    raw_timestamp = data.get(AgentResponseFieldNames.timestamp)
    timestamp = datetime.fromisoformat(raw_timestamp) if isinstance(raw_timestamp, str) else raw_timestamp
    return SSEMessage(
        agent_id=data.get(AgentResponseFieldNames.agent_id),
        agent_status=data.get(AgentResponseFieldNames.agent_status),
        template_data=template_data,
        agent_error=data.get(AgentResponseFieldNames.agent_error),
        timestamp=timestamp,
    )


def deserialize_sse_message(payload: bytes | str) -> SSEMessage:
    """Deserializes a msgpack binary payload back into an SSEMessage instance.

    Args:
        payload: The binary or byte-string msgpack payload to unpack.

    Returns:
        The fully restored SSEMessage instance.

    Raises:
        ValueError: If the payload is invalid or msgpack unpacking fails.
    """
    if not payload:
        return SINAPSIS_END_OF_STREAM

    if isinstance(payload, str):
        payload = payload.encode("utf-8")

    # raw=False ensures msgpack returns str objects instead of bytes for keys/values
    raw_dict: dict[str, Any] = msgpack.unpackb(payload, raw=False)
    if AgentResponseFieldNames.template_data not in raw_dict:
        return SINAPSIS_END_OF_STREAM
    return sse_decoder(raw_dict)


class MsgpackStreamDecoder:
    def __init__(self) -> None:
        self._unpacker = msgpack.Unpacker(raw=False)

    def sse_decode(self, chunk: bytes):
        self._unpacker.feed(chunk)

        for raw_dict in self._unpacker:
            if AgentResponseFieldNames.template_data not in raw_dict:
                yield SINAPSIS_END_OF_STREAM
                return

            yield sse_decoder(raw_dict)

<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Deserialization
<br>
</h1>

<h3 align="center">Reconstruct typed Sinapsis data and execution messages.</h3>

`sinapsis-deserialization` decodes the structured dictionary representation of Sinapsis `DataContainer` objects and the MessagePack-backed execution messages used by the corresponding messaging integrations. It restores packet types and supported array payloads, and offers helpers for decoding streamed execution events.

`DataContainer` and the packet classes belong to Sinapsis Core; this package reconstructs them from encoded input. It is designed to work with the **dictionary/message format** used by `sinapsis-serializer-core` and related integrations—not as a replacement for `sinapsis-protocol`'s versioned binary decoder.

> [!WARNING]
> **Planned Deprecation**
>
> This package is currently used exclusively by the Sinapsis Cloud API and is maintained for compatibility with the existing serialization infrastructure.
>
> It is planned for deprecation in favour of [`sinapsis-protocol`](https://pypi.org/project/sinapsis-protocol/), which provides the unified, versioned serialization and communication protocol for the Sinapsis ecosystem.
>
> For new integrations, use `sinapsis-protocol` instead. Existing integrations will continue to be supported during the transition.

## Installation

Requires **Python 3.13+**.

```bash
uv pip install 'sinapsis-deserialization[msgpack]'
# or: pip install 'sinapsis-deserialization[msgpack]'
```

The `msgpack` extra is needed for execution-message decoding. Depending on the payloads you expect, additional extras include `numpy`, `pandas`, `torch`, `darts`, `soundfile`, and `sinapsis-generic-data-tools`.

```bash
uv pip install 'sinapsis-deserialization[numpy,pandas]'
```

## DataContainer decoding

`DataContainerDecoder` accepts a dictionary containing the `container_id` field and recognized packet collections. It reconstructs a `DataContainer` and its typed packets, decoding supported embedded array envelopes and nested generic data.

```python
from sinapsis_deserialization import DataContainerDecoder

encoded = {
    "container_id": "example-container",
    "texts": [
        {
            "type": "text",
            "content": "Hello Sinapsis",
            "id": "text-1",
            "source": None,
            "embedding": [],
            "generic_data": {},
            "annotations": [],
        }
    ],
}

result = DataContainerDecoder()(encoded)
```

In a real integration, pass a dictionary produced by the corresponding Sinapsis encoder rather than constructing packet fields manually. If the input dictionary does **not** contain a recognized container identifier, the decoder returns it unchanged.

### Supported packet families

| Decoder method | Restored type |
| --- | --- |
| `decode_image` | `ImagePacket` |
| `decode_audio` | `AudioPacket` |
| `decode_text` | `TextPacket` |
| `decode_file` | `FilePacket` |
| `decode_data_frame` | `DataFramePacket` |
| `decode_time_series` | `TimeSeriesPacket` |
| `decode_binary` | `BinaryPacket` |
| `decode_generic_dict` | Nested generic metadata and supported values |
| `array_type_decoder` | Encoded array and data representations |

The decoder uses the embedded type and metadata fields to select a reconstruction path. Successful restoration of a specialized type depends on having the associated library available and on the payload using a compatible encoded representation. **Only decode payloads from trusted sources**: some legacy specialized decoding paths reconstruct Pandas objects through pickle and evaluate Torch dtype strings.

## Decoding execution messages

The package also supplies typed models for execution streams:

- `SSEMessage`: Agent-level status and a collection of per-Template responses.
- `AgentResponse`: A Template name, status, timestamp, output, and optional error.
- `TemplateStreamingResponse`: A typed representation of streaming Template output.

For a complete serialized message:

```python
from sinapsis_deserialization import deserialize_sse_message

# payload is a MessagePack-encoded SSE message from the matching Sinapsis API.
message = deserialize_sse_message(payload)
```

`deserialize_sse_message` decodes a message and reconstructs supported `DataContainer` output values and timestamps. An empty payload or a control frame without `template_data` is interpreted as an **end-of-stream marker**, not an ordinary `SSEMessage`.

### Incremental MessagePack stream decoding

`MsgpackStreamDecoder` keeps an incremental unpacker so that a message does not need to arrive in a single network chunk:

```python
from sinapsis_deserialization import MsgpackStreamDecoder

decoder = MsgpackStreamDecoder()

for chunk in network_chunks:  # successive bytes from your transport
    for event in decoder.sse_decode(chunk):
        handle_event(event)
```

The decoder yields restored messages and can yield the end-of-stream sentinel. Consumers should handle the sentinel separately from Template data. `network_chunks` and `handle_event` above are placeholders for your application's transport loop.

## Format boundaries

```text
Encoded DataContainer dictionary
            |
            v
    DataContainerDecoder
            |
            v
 DataContainer + typed packets

MessagePack execution event
            |
            v
 deserialize_sse_message / MsgpackStreamDecoder
            |
            v
 SSEMessage + AgentResponse (or control sentinel)
```

This package **decodes** existing Sinapsis message formats. It does not construct or execute Agents, provide an HTTP client, or decode `sinapsis-protocol`'s versioned envelope format. Use the matching encoder/decoder pair for the transport you are integrating.

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.
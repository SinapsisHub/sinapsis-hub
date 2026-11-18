<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Serializer Core
<br>
</h1>

<h3 align="center">DataContainer encoding and payload staging.</h3>

`sinapsis-serializer-core` provides utilities for turning Sinapsis `DataContainer` values into structured dictionaries for messaging and result presentation. It includes packet-aware encoders, file-staging helpers, and shared sentinel definitions for consumers that need them.

It **does not define the data model**: Agents and Templates use `DataContainer` and typed packets from `sinapsis.data_transport`. It also does not, by itself, implement the versioned MessagePack wire format provided by `sinapsis-protocol`.

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
uv pip install sinapsis-serializer-core
# or: pip install sinapsis-serializer-core
```

Install the optional dependencies needed for the types you process:

```bash
uv pip install 'sinapsis-serializer-core[data]'
uv pip install 'sinapsis-serializer-core[torch]'
uv pip install 'sinapsis-serializer-core[audio]'
uv pip install 'sinapsis-serializer-core[timeseries]'
uv pip install 'sinapsis-serializer-core[vision]'

# Install all declared optional feature groups
uv pip install 'sinapsis-serializer-core[all]'
```

Some staging and encoding modules import their media and array libraries directly, so choose the extras needed by your runtime before importing those modules.

## Encoding a DataContainer

`DataContainerEncoder` walks packet collections and their metadata to produce a dictionary representation. Packet content is encoded according to its type; metadata such as packet identifiers, sources, embeddings, generic data, and annotations is retained in the corresponding fields.

```python
from sinapsis.data_transport import DataContainer, TextPacket
from sinapsis_serializer_core.serialization.data_container_encoders import DataContainerEncoder

container = DataContainer(texts=[TextPacket(content="Hello Sinapsis")])
encoder = DataContainerEncoder(replace_content_with_url=False)

encoded: dict = encoder.container_encoder(container, agent_id="example-agent")
```

`container_encoder` returns a **Python dictionary**, not an HTTP response and not MessagePack bytes. A higher-level component is responsible for choosing how the dictionary is transported. For matching dictionary-format decoding, see `sinapsis-deserialization`.

### Supported packet families

| Packet family | Encoder method | Encoded information |
| --- | --- | --- |
| Images | `image_packet_encoder` | Content, color space, annotations, common metadata |
| Audio | `audio_packet_encoder` | Content, sample rate, duration, annotations, common metadata |
| Text | `text_packet_encoder` | Text content, annotations, common metadata |
| Dataframes | `data_frame_packet_encoder` | Tabular content and common metadata |
| Time series | `time_series_packet_encoder` | Series content and common metadata |
| Binary | `binary_packet_encoder` | Binary content and common metadata |
| Files | `file_packet_encoder` | File content representation and common metadata |
| Generic data | `generic_data_encoder` | Recursively handled nested values |

The actual binary representation depends on the content type. The array encoder can describe NumPy arrays, Torch tensors, selected Pandas and Darts values, strings, and byte content. Unsupported types are not automatically made losslessly serializable; use supported packet content types and validate the output at your integration boundary.

## Inline content versus staged content

The encoder exposes two modes:

```python
from sinapsis_serializer_core.serialization.data_container_encoders import DataContainerEncoder

inline_encoder = DataContainerEncoder(replace_content_with_url=False)
staged_encoder = DataContainerEncoder(replace_content_with_url=True)
```

- **Inline:** packet content is represented directly in the encoded dictionary, with metadata needed by the corresponding decoder.
- **Staged:** supported payloads are written to staging storage; the dictionary contains a reference to the saved content (and, where supported, a smaller preview).

Staging is useful when returning images, audio, arrays, or other substantial outputs without embedding all their bytes in a streamed result. The consumer must be able to access the staged files; the encoder does not host or serve them.

### Staging helpers

| Helper | Responsibility |
| --- | --- |
| `StagingFileManager` | Common staging path and reference helpers |
| `StagingImageManager` | Full image output and preview image |
| `StagingAudioManager` | Full audio output and preview |
| `StagingGenericArrayManager` | Arrays, tensors, text, bytes, dataframes, and related values |
| `StagingTimeSeriesManager` | Time-series data and related series fields |

`StagingVideoManager` is present as a class, but its staging method is not implemented in the inspected source. Do not rely on it to export video payloads.

Staging uses `STREAMING_STAGING_DIR` (default `/data/staging` in the current implementation). Ensure that the selected directory exists and is writable by the running process.

## Sentinels and protocol-related schemas

Besides payload encoding, the package contains shared control-message primitives:

| Symbol | Role |
| --- | --- |
| `ProtocolSentinel` | Associates a Sinapsis sentinel with an integer signal |
| `SinapsisMsgPackProtocol` | Names known control signals for MessagePack-based messaging |
| `SerializationError`, `DeserializationError` | Error classes for encoding and decoding boundaries |

These definitions help messaging integrations distinguish **control signals** from data payloads. They are not substitutes for the `DataContainer` schema or for the transport framing and versioning in `sinapsis-protocol`.

## How it fits with related packages

```text
DataContainer / typed packets  (sinapsis)
             |
             v
DataContainerEncoder           (sinapsis-serializer-core)
             |
             +--> encoded dictionary --> messaging / API integration
             |
             +--> optional staged files + content references

Encoded dictionary --> DataContainerDecoder (sinapsis-deserialization)
```

Use the serializer and decoder together only when they are configured for the same dictionary representation. For a versioned byte-oriented UDT exchange, use the matching `sinapsis-protocol` encoder and decoder instead.

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.
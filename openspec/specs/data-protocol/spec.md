# Data Protocol (sinapsis-protocol)

## Purpose
`sinapsis-protocol` defines "Universal Data Transport", a MessagePack wire format named `sinapsis-data` v1.0. Sinapsis uses it to move `DataContainer`s, SSE envelopes and control sentinels between processes and services: the local API, the SDK and the CLI. Large payloads are offloaded to a content-addressed artifact store. Optional adapters encode numpy, torch, pandas, polars and OpenCV values.

Citations are relative to `packages/python/core/sinapsis-protocol/src/sinapsis_protocol/`.

## Requirements

### Requirement: Protocol envelope
`serialize(container)` SHALL produce a msgpack map with the keys `protocol`, `major`, `minor`, `kind` and `payload`. (src: container/serialize.py:120-144)

#### Scenario: Envelope fields
- **WHEN** a non-empty `DataContainer` is serialized
- **THEN** the map SHALL be `{"protocol": "sinapsis-data", "major": 1, "minor": 0, "kind": "container", "payload": ...}`

#### Scenario: Round trip
- **GIVEN** a non-empty `DataContainer` with a `TextPacket`
- **WHEN** it is serialized and then deserialized with the default registry
- **THEN** the result SHALL be a `DataContainer` with an equal text packet

### Requirement: Envelope validation on decode
`deserialize` SHALL reject any packet whose protocol, major version or kind it does not support. It SHALL NOT currently check `minor`. (src: container/deserialize.py:101-122)

#### Scenario: Future major version
- **WHEN** a packet with `major: 2` is deserialized
- **THEN** `UnsupportedProtocolVersionError("Unsupported protocol major: 2")` SHALL be raised

#### Scenario: Wrong protocol or kind
- **WHEN** the protocol field is missing or wrong
- **THEN** `InvalidPacketError("Missing or invalid protocol envelope")` SHALL be raised
- **AND** when `kind` is not `container`, `InvalidPacketError("Unsupported packet kind")` SHALL be raised

### Requirement: Empty-container sentinel
Serializing a container whose `is_empty` is truthy SHALL return a 3-byte msgpack extension sentinel (ext code 42). Deserializing it SHALL return the `ProtocolSentinel` enum, not a `DataContainer`. (src: wire/constants.py:57-81; wire/format.py:120-154)

#### Scenario: Empty container
- **WHEN** an empty `DataContainer` is serialized
- **THEN** the output SHALL be exactly the bytes `D4 2A 01`
- **AND** deserializing it SHALL return `ProtocolSentinel.EMPTY_CONTAINER`

#### Scenario: Sentinel values
- **WHEN** `ProtocolSentinel` is inspected
- **THEN** its values SHALL be `EMPTY_CONTAINER=1`, `EMPTY_PACKET=2`, `NULL_VALUE=3`, `HEARTBEAT=4` and `END_OF_STREAM=5`

### Requirement: Serialization limits
The serializer SHALL enforce `SerializationLimits` on size, collection length and nesting depth, and SHALL raise a typed error when any limit is exceeded. (src: types.py:10-17; container/serialize.py:26-117; codecs/base.py:12-27)

#### Scenario: Default limits
- **WHEN** no custom limits are given
- **THEN** `max_packet_bytes` SHALL be 256 MiB × 100
- **AND** `max_inline_bytes` SHALL be 16 MiB × 100
- **AND** `max_array_bytes` SHALL be 512 MiB × 100
- **AND** `max_string_bytes` SHALL be 16 MiB × 100
- **AND** `max_collection_length` SHALL be 1,000,000
- **AND** `max_nesting_depth` SHALL be 64
- **AND** `SerializationConfig.inline_binary_limit` SHALL be 16 MiB

#### Scenario: Deep nesting rejected
- **WHEN** a value nested deeper than 64 levels is serialized
- **THEN** `PayloadTooLargeError("Maximum nesting depth exceeded")` SHALL be raised

#### Scenario: Oversized values
- **WHEN** a string exceeds the string limit
- **THEN** `PayloadTooLargeError("String exceeds max_string_bytes")` SHALL be raised
- **AND** a collection over the length limit SHALL raise `"Collection exceeds max_collection_length"`
- **AND** an array payload over the array limit SHALL raise `ValueError("Payload exceeds max_array_bytes")`

### Requirement: Value normalization
The serializer SHALL normalize Python values into wire primitives or typed values before encoding. Wire models SHALL drop fields whose value is `None` or `{}`. (src: container/serialize.py:51-117; wire/format.py:23-24)

#### Scenario: Type mapping
- **WHEN** values of each supported type are serialized
- **THEN** a `Path` SHALL become a FILE artifact
- **AND** `UUID` and `datetime`/`date`/`time` values SHALL become typed values
- **AND** an `Enum` SHALL become its `.value`, which is lossy
- **AND** list, tuple, set and frozenset SHALL all become a list, which is lossy
- **AND** a registered pydantic dataclass SHALL become `{"__type__": "dataclass", name, version, fields}`

#### Scenario: Non-primitive mapping keys
- **WHEN** a dict with tuple keys is serialized
- **THEN** `TypeError("Wire mapping keys must be primitive MessagePack-compatible values")` SHALL be raised

#### Scenario: Unregistered dataclass or unknown type
- **WHEN** a pydantic dataclass that is not in the registry is serialized
- **THEN** `UnsupportedTypeError("Dataclass is not registered: ...")` SHALL be raised
- **AND** an unsupported type that no adapter accepts SHALL raise `UnsupportedTypeError("No adapter can encode {type}")`

### Requirement: Default type registry
`default_registry()` SHALL register every dataclass in `sinapsis.data_transport.__all__` under the name `{module}.{qualname}`. It SHALL then try adapters lazily, skipping any whose library is missing. (src: codecs/registry.py:15-87)

#### Scenario: Adapter order
- **WHEN** an `np.ndarray` is serialized with the default registry
- **THEN** adapters SHALL be tried in the order numpy, torch, pandas, polars, cv2
- **AND** the numpy adapter SHALL win, so the cv2 PNG adapter is never selected by default

#### Scenario: Optional library missing
- **GIVEN** torch is not installed
- **WHEN** a numpy array is serialized
- **THEN** the torch adapter SHALL be skipped and the array SHALL be encoded with numpy

### Requirement: Array and dataframe codecs
Each codec SHALL encode its library's values into raw or Arrow payloads with metadata. Inline payloads SHALL carry a sha256 checksum. (src: codecs/*.py)

#### Scenario: Numpy and dataframes
- **WHEN** arrays and dataframes are encoded
- **THEN** numpy arrays SHALL be encoded as C-contiguous bytes with `ArrayMetadata(shape, dtype, order="C")`
- **AND** pandas and polars frames SHALL use an Arrow IPC stream
- **AND** pandas SHALL preserve the index

#### Scenario: GPU tensor
- **WHEN** a CUDA tensor with `requires_grad=True` is serialized and then deserialized
- **THEN** the result SHALL be a CPU tensor with equal values and `requires_grad=False`
- **AND** a tensor whose dtype is not one of the 11 supported dtypes SHALL raise `TypeError("Unsupported torch dtype: ...")`

#### Scenario: Checksum mismatch
- **WHEN** an inline payload's bytes do not match its sha256
- **THEN** `"Payload checksum mismatch"` SHALL be raised

### Requirement: Artifact store
Payloads larger than the inline limit, and every FILE/BINARY transport, SHALL be stored in `LocalArtifactStore(root, username, agent_id)` at `root/username/agent_id/<sha256>`, with the reference URI `artifact://<sha256>`. (src: artifacts/local.py)

#### Scenario: Default store and sanitizing
- **WHEN** no store is passed
- **THEN** a store at `/tmp/sinapsis-staging/default/default` SHALL be created on each call
- **AND** every path component SHALL have `[^A-Za-z0-9._-]+` replaced with `_`

#### Scenario: Tampered artifact
- **GIVEN** an artifact file whose bytes changed after it was stored
- **WHEN** the referencing packet is deserialized
- **THEN** `ArtifactError("Checksum mismatch for artifact {id}")` SHALL be raised
- **AND** a missing artifact SHALL raise `ArtifactError("Artifact not found: {id}")`

### Requirement: SSE envelope
`SSEEnvelope` SHALL be encoded with `kind: "sse-envelope"`. It SHALL carry an agent id and status, optional container `data`, errors, an event type, a request type and a job id. (src: wire/envelope.py:25-153)

#### Scenario: Enumerated fields
- **WHEN** an envelope is built
- **THEN** `agent_status` SHALL be one of `idle`, `running`, `completed`, `error` or `cancelled`
- **AND** `event_type` SHALL be one of `data`, `status`, `error`, `complete`, `heartbeat` or `callback`
- **AND** `request_type` SHALL be one of `execute`, `stream`, `status` or `cancel`
- **AND** errors SHALL be `EnvelopeError(code, message, details)` items

#### Scenario: Envelope with non-container data
- **WHEN** an envelope whose `data` does not decode to a `DataContainer` is decoded
- **THEN** `"SSE envelope data must decode to a DataContainer"` SHALL be raised

### Requirement: WebSocket frame splitting
`split_websocket_frame(frame)` SHALL return a tuple of the metadata dict and a memoryview of the envelope bytes. (src: wire/frame_splitter.py:7-44)

#### Scenario: Malformed frame
- **WHEN** a frame has metadata that is not a map
- **THEN** `ValueError("Event frame metadata must be a map.")` SHALL be raised

# Legacy Serializer (sinapsis-serializer-core)

## Purpose
`sinapsis-serializer-core` encodes `DataContainer`s into JSON-friendly dicts for the Sinapsis Cloud API. Rich content can optionally be staged to disk and replaced with URLs. Its README marks it for **planned deprecation**: only Sinapsis Cloud uses it, and `sinapsis-protocol` will replace it.

Citations are relative to `packages/python/core/sinapsis-serializer-core/src/sinapsis_serializer_core/`.

## Requirements

### Requirement: Container encoding
`DataContainerEncoder(replace_content_with_url=False).container_encoder(obj, agent_id)` SHALL return a dict with one key per container field. (src: encoders/data_container_encoders.py:55-89)

#### Scenario: Encode a container
- **WHEN** a container with images and texts is encoded inline
- **THEN** the result SHALL contain encoded entries for every container field

### Requirement: Array-like content encoding
Array-like content SHALL be encoded as `{content, shape, device, dtype, array_type}`, with a rule for each supported type. (src: encoders/data_container_encoders.py:122-209)

#### Scenario: Per-type rules
- **WHEN** content of each supported type is encoded
- **THEN** numpy arrays SHALL be encoded as raw bytes
- **AND** str values SHALL be utf-8 encoded
- **AND** torch tensors SHALL be encoded via numpy with device always `"cpu"`
- **AND** bytes SHALL be encoded with `shape=-1`
- **AND** pandas DataFrames SHALL be encoded with `to_json(orient="split")`
- **AND** pandas Series SHALL be pickled
- **AND** darts series SHALL be encoded with `to_json`

#### Scenario: Unsupported content silently dropped
- **WHEN** a packet's content has an unsupported type
- **THEN** the encoded content SHALL be `{}`, with only a debug log
- **AND** no error SHALL be raised

### Requirement: Staged content
With `replace_content_with_url=True`, content SHALL be written under `{STREAMING_STAGING_DIR}/{agent_id}/` and replaced by `{"sample": ..., "original": ...}` relative paths. (src: staging/staging_file_manager.py:53-315)

#### Scenario: Image staging
- **GIVEN** `STREAMING_STAGING_DIR=/data/staging`
- **WHEN** an RGB image packet is encoded with URL replacement
- **THEN** a full JPEG and a sample JPEG of at most 200x200 SHALL be written as `{YYYYmmdd_HHMMSS}_{uuid4}_original.jpg` and `..._sample.jpg`
- **AND** the packet SHALL be converted from RGB to BGR in place

#### Scenario: Other content types
- **WHEN** audio is staged
- **THEN** it SHALL be saved as `.ogg` with a 2-second preview
- **AND** arrays and tables SHALL be saved by type as `.npy`, `.pt`, `.txt`, `.bin` or `.csv`
- **AND** staging a video SHALL raise `NotImplementedError`

### Requirement: Serializer env vars
The serializer SHALL read its staging directories and size thresholds from env vars, falling back to built-in defaults. (src: env_vars/env_vars.py:5-86)

#### Scenario: Defaults
- **WHEN** no env vars are set
- **THEN** `STREAMING_STAGING_DIR` SHALL be `/data/staging`
- **AND** `SAVING_PERSISTENT_DIR` SHALL be `/data/persistent`
- **AND** `IN_MEMORY_DB_THR` SHALL be 20971520 (its field name is `IN_MEMORY_DB_OBJECT_SIZE_THR`)
- **AND** `SHM_DB_OBJECT_SIZE_THR` SHALL be 0
- **AND** `RMQ_OBJECT_SIZE_THR` SHALL be 131072
- **AND** `DISK_OBJECT_SIZE_THR` SHALL be 524288000
- **AND** `S3_OBJECT_SHARING_ENABLED` SHALL be False
- **AND** `SHM_ROOT_DIR` SHALL be `/dev/shm`
- **AND** `TRANSIENT_ROOT_DIR` SHALL be `/data/worker_temp`

### Requirement: Control-signal table
`SinapsisMsgPackProtocol` SHALL define numbered control signals 1-9. `signal_to_sentinel` SHALL map an int to its sentinel. This table is currently incompatible with the values of `sinapsis-protocol`'s `ProtocolSentinel`. (src: schemas/sentinel_protocol.py:30-76)

#### Scenario: Signal values
- **WHEN** the enum is inspected
- **THEN** its values SHALL be `EMPTY_CONTAINER=1`, `TEMPLATE_FINISHED=2`, `AGENT_FINISHED=3`, `REDIS_REF=4`, `DISK_REF=5`, `CLOUD_REF=6`, `RMQ_REF=7`, `SHM_REF=8` and `START_WORKER=9`

#### Scenario: Unknown signal
- **WHEN** `signal_to_sentinel(99)` is called
- **THEN** `ValueError("Unknown signal: 99")` SHALL be raised

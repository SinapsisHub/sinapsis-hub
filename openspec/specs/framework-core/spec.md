# Framework Core (sinapsis facade)

## Purpose
The `sinapsis` package is the public facade of the framework. It re-exports the runtime from the external `sinapsis-core` distribution: `Template`, the Agent schemas, `DataContainer` and the packet types. It adds template discovery, sentinels and env-var access on top. Capabilities are packaged as **Templates**, which are composed into **Agents** declared in YAML.

This spec covers only code in this repository. The Agent execution loop, execution strategies and packet field definitions live in `sinapsis-core` and are out of scope.

Citations are relative to `packages/python/core/sinapsis/` unless they are prefixed with another package path.

## Requirements

### Requirement: Facade top-level exports
The `sinapsis` package SHALL export `Template`, `DataContainer`, `sinapsis_logger` and `SinapsisSentinel` from its top level. It SHALL NOT currently export `Agent` from the top level. (src: src/sinapsis/__init__.py:14-35)

#### Scenario: Import the template base class
- **GIVEN** `sinapsis` is installed
- **WHEN** a user runs `from sinapsis import Template, DataContainer`
- **THEN** the import SHALL succeed and resolve to the `sinapsis_core` implementations

#### Scenario: Agent is available only from the agent submodule
- **WHEN** a user runs `from sinapsis.agent import Agent`
- **THEN** the import SHALL succeed
- **AND** `from sinapsis import Agent` SHALL fail, because the export is commented out
- **AND** the module docstring SHALL still show `from sinapsis import Agent`, which is a known doc/code mismatch

### Requirement: Facade submodules
The facade SHALL re-export the `sinapsis_core` template, agent, data-transport, env-var, logging and exception symbols through the submodules `sinapsis.template`, `sinapsis.agent`, `sinapsis.data_transport`, `sinapsis.env_vars`, `sinapsis.logging` and `sinapsis.exceptions`. (src: src/sinapsis/template/__init__.py; src/sinapsis/agent/__init__.py)

#### Scenario: Submodule imports
- **WHEN** a user imports `generic_agent_schema_builder` from `sinapsis.agent`
- **THEN** the import SHALL succeed
- **AND** `AgentCancelledException` SHALL be importable from `sinapsis.exceptions`

### Requirement: Data model packet types
`sinapsis.data_transport` SHALL expose every packet type, `DataContainer`, the annotation types, the speech result types and the LLM context types. (src: src/sinapsis/data_transport/__init__.py:1-44)

#### Scenario: Exported data types
- **WHEN** a user inspects `sinapsis.data_transport`
- **THEN** it SHALL expose these packets: `ImagePacket`, `AudioPacket`, `TextPacket`, `TimeSeriesPacket`, `DataFramePacket`, `BinaryPacket`, `FilePacket`, `LLMConversationPacket`
- **AND** these annotation types: `ImageAnnotations`, `AudioAnnotations`, `TextAnnotations`, `BoundingBox`, `OrientedBoundingBox`, `KeyPoint`, `Segmentation`
- **AND** these speech types: `DiarizedTranscript`, `SpeakerTurn`, `TranscriptSegment`, `PredictedEmotion`

### Requirement: DataContainer collections
A `DataContainer` SHALL carry one collection per modality plus a free-form `generic_data` dict. (src: packages/python/core/sinapsis-serializer-core/src/sinapsis_serializer_core/encoders/data_container_encoders.py:72-88)

#### Scenario: Container carries mixed modalities
- **GIVEN** a `DataContainer` with one `ImagePacket` and one `TextPacket`
- **WHEN** a Template's `execute(container)` runs
- **THEN** the Template SHALL be able to read `container.images` and `container.texts` and append to either one
- **AND** the container SHALL also expose `audios`, `files`, `data_frames`, `time_series`, `binary_data` and `generic_data`

### Requirement: Template contract
A Template SHALL subclass `Template`, declare a nested `AttributesBaseModel(TemplateAttributes)` pydantic model that is validated at construction, and implement `execute(self, container) -> DataContainer`. (src: src/sinapsis/templates/hello_world.py:13-48)

#### Scenario: HelloWorld appends a text packet
- **GIVEN** a `HelloWorld` template with `display_text: "Hello from Sinapsis!"`
- **WHEN** it executes on an empty container
- **THEN** the container SHALL contain a `TextPacket` whose content is `"Hello from Sinapsis!"`
- **AND** inside `execute`, the attributes SHALL be available as `self.attributes.<field>` and the instance name as `self.instance_name`

#### Scenario: Invalid attribute rejected
- **WHEN** a Template is constructed with an attribute value that fails its pydantic type
- **THEN** construction SHALL raise a validation error

### Requirement: Built-in templates
`sinapsis.templates` SHALL statically map eight built-in template names and import each one lazily on first access. (src: src/sinapsis/templates/__init__.py:13-22)

#### Scenario: Lazy access to a built-in template
- **WHEN** code accesses `sinapsis.templates.InputTemplate`
- **THEN** the class SHALL be imported from `sinapsis_core.template_base` and returned
- **AND** the same SHALL hold for `OutputTemplate`, `CopyDataContainer`, `TransferDataContainer`, `SplitDataFlow` and `MergeDataFlow`
- **AND** `HelloWorld` and `DisplayHelloWorld` SHALL resolve from `sinapsis.templates`

### Requirement: Template package auto-discovery
When `sinapsis.templates` is imported, the system SHALL import `<dist>.templates` for every installed distribution named `sinapsis_*` except `sinapsis_core`, and register the names in that module's `__all__`. Discovery SHALL NOT use entry points. (src: src/sinapsis/templates/__init__.py:25-82)

#### Scenario: Installed package exposes its templates
- **GIVEN** `sinapsis-ultralytics` is installed and its `templates.__all__` contains `UltralyticsPredict`
- **WHEN** an Agent config references `class_name: UltralyticsPredict`
- **THEN** the class SHALL resolve with no extra registration

#### Scenario: Package without templates module
- **GIVEN** an installed distribution `sinapsis_foo` that has no `templates` subpackage
- **WHEN** discovery runs
- **THEN** it SHALL be skipped, with the debug log `Skipping package: {package_name}, does it have a `templates` directory?`
- **AND** no error SHALL be raised

#### Scenario: Monorepo checkout skipped
- **GIVEN** a distribution whose file paths contain a `packages` path segment
- **WHEN** discovery runs
- **THEN** the distribution SHALL be skipped

### Requirement: Additional template paths
When a template name is not in the registry, the system SHALL search the paths listed in the `ADDITIONAL_TEMPLATE_PATHS` env var, loading `f"{path}__init__.py"` from each. (src: src/sinapsis/templates/__init__.py:36-103)

#### Scenario: Path without trailing slash
- **GIVEN** `ADDITIONAL_TEMPLATE_PATHS` contains `my_pkg/templates`, with no trailing slash
- **WHEN** a lookup falls back to it
- **THEN** the module path SHALL be built as `my_pkg/templates__init__.py`, so paths MUST end with `/`

#### Scenario: Unknown template
- **WHEN** code accesses `sinapsis.templates.DoesNotExist` and `ADDITIONAL_TEMPLATE_PATHS` is unset
- **THEN** an `AttributeError` SHALL be raised that starts with ``Template `DoesNotExist` not found. Please ensure it is in sinapsis.templates.``

### Requirement: Agent configuration file
An Agent SHALL be declared in YAML with a top-level `agent` mapping and a `templates` list. `generic_agent_schema_builder(dict) -> AgentSchema` SHALL be the canonical validator. (src: src/sinapsis/configs/hello_world_agent.yml; README.md:108-144)

#### Scenario: Config keys
- **WHEN** an agent YAML is written
- **THEN** `agent` SHALL hold `name` and optional `attributes`, such as `description` and `templates_to_profile`
- **AND** each `templates` entry SHALL have `template_name` (unique within the agent), `class_name`, optional `template_input` (the upstream `template_name`) and `attributes`

#### Scenario: Hello-world agent
- **GIVEN** the shipped `configs/hello_world_agent.yml`, which chains `InputTemplate` → `HelloWorld`
- **WHEN** it is run with `sinx jobs run`
- **THEN** both templates SHALL execute in dependency order
- **AND** the text packet SHALL be output

### Requirement: Sinapsis sentinels
`SinapsisSentinel(value: str)` SHALL be interned per value, and SHALL compare equal only to sentinels that have the same value. (src: src/sinapsis/sentinels/__init__.py:14-61)

#### Scenario: Interned identity
- **WHEN** `SinapsisSentinel("x")` is constructed twice
- **THEN** both calls SHALL return the same object
- **AND** its `repr` SHALL be `x`

#### Scenario: Non-string value
- **WHEN** `SinapsisSentinel(1)` is constructed
- **THEN** `TypeError("Expected 1 to be a string.")` SHALL be raised

#### Scenario: Built-ins and hashing
- **WHEN** the module is imported
- **THEN** `SENTINEL_GENERIC_KEY`, `SINAPSIS_NOT_SET` and `SINAPSIS_EMPTY_CONTAINER` SHALL exist
- **AND** instances SHALL currently be unhashable, because `__eq__` is defined without `__hash__`

### Requirement: Env-var access
`sinapsis.env_vars.<NAME>` SHALL return the default value of the matching `SinapsisEnvVarDefaults` field. (src: src/sinapsis/env_vars/__init__.py:13-18)

#### Scenario: Unknown env var
- **WHEN** code accesses `sinapsis.env_vars.NOPE`
- **THEN** ``AttributeError("Agent does not have `NOPE` env var")`` SHALL be raised

### Requirement: Packaging and distribution
Every Python package in the monorepo SHALL require Python `>=3.13`, be built with hatchling, and be versioned independently, currently at `1.0.0`. (src: pyproject.toml:2-46)

#### Scenario: Licensing and index
- **WHEN** any package manifest is inspected
- **THEN** its license SHALL be `MIT OR Apache-2.0`, except `sinapsis-api`, which currently omits the license field
- **AND** Sinapsis dependencies SHALL resolve from the uv index `https://pypi.sinapsis.tech/`

#### Scenario: Independent install
- **WHEN** a user installs only `sinapsis` and `sinapsis-doctr`
- **THEN** no other template package SHALL be required

from sinapsis_protocol.container.deserialize import deserialize
from sinapsis_protocol.container.serialize import SerializationConfig, serialize

serialize_data_container = serialize
deserialize_data_container = deserialize

__all__ = ["SerializationConfig", "deserialize", "deserialize_data_container", "serialize", "serialize_data_container"]

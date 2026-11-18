import dataclasses
from typing import Any

from sinapsis.data_transport import dataclass

from sinapsis_protocol.errors import InvalidPayloadError, UnsupportedTypeError


@dataclass(frozen=True, slots=True)
class DataclassSpec:
    cls: type[Any]
    type_name: str
    version: int = 1


class DataclassRegistry:
    def __init__(self) -> None:
        self._by_cls: dict[type[Any], DataclassSpec] = {}
        self._by_wire: dict[tuple[str, int], DataclassSpec] = {}

    def register(self, cls: type[Any], *, type_name: str | None = None, version: int = 1) -> None:
        if not dataclasses.is_dataclass(cls) or not isinstance(cls, type):
            raise TypeError(f"Expected a dataclass type, got {cls!r}")
        name = type_name or f"{cls.__module__}.{cls.__qualname__}"
        spec = DataclassSpec(cls, name, version)
        self._by_cls[cls] = spec
        self._by_wire[(name, version)] = spec

    def find_for_value(self, value: object) -> DataclassSpec | None:
        cls = type(value)
        if cls in self._by_cls:
            return self._by_cls[cls]
        for base in cls.__mro__[1:]:
            spec = self._by_cls.get(base)
            if spec is not None:
                return spec
        return None

    def resolve(self, type_name: str, version: int) -> DataclassSpec:
        try:
            return self._by_wire[(type_name, version)]
        except KeyError as exc:
            raise UnsupportedTypeError(f"No registered dataclass for {type_name!r} v{version}") from exc


def register_sinapsis_dataclasses(registry: DataclassRegistry) -> None:
    """Register the built-in Sinapsis data-transport dataclasses when available."""

    import sinapsis.data_transport as data_transport

    for data_class in data_transport.__all__:
        cls_obj = getattr(data_transport, data_class)
        if not dataclasses.is_dataclass(cls_obj):
            continue

        registry.register(cls_obj)

    # registry.register(ImagePacket)


def encode_dataclass(
    value: object, encode_value: Any, registry: DataclassRegistry, context: Any, depth: int
) -> dict[str, Any]:
    spec = registry.find_for_value(value)
    if spec is None:
        raise UnsupportedTypeError(f"Dataclass is not registered: {type(value)!r}")
    fields: dict[str, Any] = {}
    for field in dataclasses.fields(value):
        if field.init:
            fields[field.name] = encode_value(getattr(value, field.name), context, depth + 1)
    return {"__type__": "dataclass", "version": spec.version, "name": spec.type_name, "fields": fields}


def decode_dataclass(
    value: dict[str, Any], decode_value: Any, registry: DataclassRegistry, context: Any, depth: int
) -> object:
    name = value.get("name")
    version = value.get("version")
    raw_fields = value.get("fields")
    if not isinstance(name, str) or not isinstance(version, int) or not isinstance(raw_fields, dict):
        raise InvalidPayloadError("Invalid dataclass wire representation")
    spec = registry.resolve(name, version)
    kwargs: dict[str, Any] = {}
    for field in dataclasses.fields(spec.cls):
        if not field.init:
            continue
        if field.name in raw_fields:
            kwargs[field.name] = decode_value(raw_fields[field.name], context, depth + 1)
        elif field.default is dataclasses.MISSING and field.default_factory is dataclasses.MISSING:
            raise InvalidPayloadError(f"Missing required field {field.name!r} for {name}")
    try:
        return spec.cls(**kwargs)
    except Exception as exc:
        raise InvalidPayloadError(f"Could not construct dataclass {name!r}") from exc

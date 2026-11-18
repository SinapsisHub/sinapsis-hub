import importlib
from typing import Any, Type

from sinapsis_protocol.dataclass.registry import DataclassRegistry, register_sinapsis_dataclasses
from sinapsis_protocol.errors import UnsupportedTypeError
from sinapsis_protocol.types import Adapter, DecodeContext, EncodeContext
from sinapsis_protocol.wire.models import TransportValue


class AdapterSpec:
    def __init__(
        self, type_name: str, library: str | None, version: int, module: str, attribute: str = "Adapter"
    ) -> None:
        self.type_name = type_name
        self.library = library
        self.version = version
        self.module = module
        self.attribute = attribute


class AdapterRegistry:
    def __init__(self) -> None:
        self._specs: list[AdapterSpec] = []
        self._overrides: dict[tuple[str, str | None, int], Type[Adapter]] = {}
        self._loaded: dict[tuple[str, str | None, int], Type[Adapter]] = {}
        self.dataclasses = DataclassRegistry()

    def add_lazy(self, spec: AdapterSpec) -> None:
        self._specs.append(spec)

    def register(self, adapter: Type[Adapter]) -> None:
        key = (adapter.type_name, adapter.library, adapter.version)
        self._overrides[key] = adapter
        self._loaded[key] = adapter

    def register_dataclass(self, cls: type[Any], *, type_name: str | None = None, version: int = 1) -> None:
        self.dataclasses.register(cls, type_name=type_name, version=version)

    def _resolve(self, type_name: str, library: str | None, version: int) -> Type[Adapter]:
        key = (type_name, library, version)
        if key in self._loaded:
            return self._loaded[key]
        for spec in self._specs:
            if (spec.type_name, spec.library, spec.version) == key:
                module = importlib.import_module(spec.module)
                adapter = getattr(module, spec.attribute)
                self._loaded[key] = adapter
                return adapter
        raise UnsupportedTypeError(f"No adapter for {type_name}/{library or '-'} v{version}")

    def _resolve_optional(self, type_name: str, library: str | None, version: int) -> Type[Adapter] | None:
        try:
            return self._resolve(type_name, library, version)
        except ModuleNotFoundError as exc:
            # A lazy adapter may legitimately be unavailable because its optional
            # dependency is not installed. Only suppress that case when the
            # missing module is the adapter's declared optional library. An import
            # failure inside the adapter itself must remain visible.
            if library is not None and exc.name == library:
                return None
            raise

    def encode(self, value: object, context: EncodeContext) -> TransportValue:
        for adapter in self._overrides.values():
            if adapter.can_encode(value):
                return adapter.encode(value, context)
        for spec in self._specs:
            adapter = self._resolve_optional(spec.type_name, spec.library, spec.version)
            if adapter is not None and adapter.can_encode(value):
                return adapter.encode(value, context)
        raise UnsupportedTypeError(f"No adapter can encode {type(value)!r}")

    def decode(self, value: TransportValue, context: DecodeContext) -> object:
        descriptor = value.descriptor
        adapter = self._resolve(descriptor.kind, descriptor.library, descriptor.version)
        return adapter.decode(value, context)


def default_registry() -> AdapterRegistry:
    registry = AdapterRegistry()
    register_sinapsis_dataclasses(registry.dataclasses)
    registry.add_lazy(AdapterSpec("array", "numpy", 1, "sinapsis_protocol.codecs.numpy"))
    registry.add_lazy(AdapterSpec("array", "torch", 1, "sinapsis_protocol.codecs.torch"))
    registry.add_lazy(AdapterSpec("dataframe", "pandas", 1, "sinapsis_protocol.codecs.pandas"))
    registry.add_lazy(AdapterSpec("dataframe", "polars", 1, "sinapsis_protocol.codecs.polars"))
    registry.add_lazy(AdapterSpec("image", "opencv", 1, "sinapsis_protocol.codecs.cv2"))
    return registry

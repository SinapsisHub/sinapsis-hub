import importlib
from collections.abc import Callable
from typing import cast

from sinapsis.templates import _import_template_package

_root_lib_path = "sinapsis_polyfuzz.templates"

_template_lookup: dict = {
    "USEEmbeddingsWrapper": f"{_root_lib_path}.polyfuzz_use_embedding",
    "ExactMatch": f"{_root_lib_path}.exact_match",
}

_ADDITIONAL_TEMPLATE_MODULES = [
    f"{_root_lib_path}.polyfuzz_dynamic",
    f"{_root_lib_path}.polyfuzz_pair_dynamic",
]


for t_module in _ADDITIONAL_TEMPLATE_MODULES:
    _template_lookup |= _import_template_package(t_module)


def __getattr__(name: str) -> Callable:
    """Dynamically imports and returns a template callable.

    This function implements module-level attribute access to allow for lazy loading
    of templates defined in the lookup table.

    Args:
        name: The name of the template to retrieve.

    Returns:
        The callable template corresponding to the given name.

    Raises:
        AttributeError: If the template name is not found in the lookup table.
    """
    if name in _template_lookup:
        module = importlib.import_module(_template_lookup[name])
        return cast(Callable, getattr(module, name))
    raise AttributeError(f"template `{name}` not found in {_root_lib_path}")


__all__ = list(_template_lookup.keys())

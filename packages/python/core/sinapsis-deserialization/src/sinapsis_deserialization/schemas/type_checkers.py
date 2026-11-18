from __future__ import annotations

import importlib
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, TypeGuard

if TYPE_CHECKING:
    import darts
    import numpy as np
    import pandas as pd
    import torch

    ARRAY_CONTENT_TYPES = torch.Tensor | np.ndarray | pd.Series | pd.DataFrame | darts.TimeSeries

# Module-level cache to avoid import/lookup overhead on repeated function calls
_ARRAY_TYPES_CACHE: tuple[type, ...] | None = None


def _get_array_types() -> tuple[type, ...]:
    """Dynamically imports available packages once and caches their type classes."""
    global _ARRAY_TYPES_CACHE
    if _ARRAY_TYPES_CACHE is None:
        target_specs = [
            ("torch", ["Tensor"]),
            ("numpy", ["ndarray"]),
            ("pandas", ["Series", "DataFrame"]),
            ("darts", ["TimeSeries"]),
        ]
        resolved_types: list[type] = []

        for module_name, class_names in target_specs:
            try:
                mod = importlib.import_module(module_name)
                for class_name in class_names:
                    if hasattr(mod, class_name):
                        resolved_types.append(getattr(mod, class_name))
            except (ImportError, AttributeError):
                continue

        _ARRAY_TYPES_CACHE = tuple(resolved_types)

    return _ARRAY_TYPES_CACHE


def is_array_content(obj: Any) -> TypeGuard[ARRAY_CONTENT_TYPES]:
    """Determines if an object belongs to a supported numerical or tabular data type.

    Args:
        obj: The object to evaluate.

    Returns:
        True if the object is a Tensor, ndarray, Series, DataFrame, or TimeSeries.
    """
    return isinstance(obj, _get_array_types())


def is_builtin_type(obj: Any) -> bool:
    """Checks if an object is a standard Python primitive type.

    Args:
        obj: The object to evaluate.

    Returns:
        True if the object is an int, float, bool, None, str, bytes, or bytearray.
    """
    return isinstance(obj, (int, float, bool, type(None), str, bytes, bytearray))


def is_iterable(obj: Any) -> bool:
    """Checks if an object can be iterated over, excluding string-like types.

    Args:
        obj: The object to evaluate.

    Returns:
        True if the object is an Iterable and not a string or byte sequence.
    """
    return isinstance(obj, Iterable) and not isinstance(obj, (str, bytes))


def is_encoded_array_type(obj: Any) -> bool:
    """Identifies if a dictionary represents a previously encoded array structure.

    Args:
        obj: The object to evaluate.

    Returns:
        True if the object is a dictionary containing both 'content' and
        'array_type' keys.
    """
    return isinstance(obj, dict) and "content" in obj and "array_type" in obj

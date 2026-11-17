from pydantic import BaseModel
from sinapsis.env_vars import return_docs_for_vars

from .env_vars import _SinapsisAPIEnvVars

SinapsisAPIEnvVarDefaults: BaseModel = _SinapsisAPIEnvVars()

__doc__ = return_docs_for_vars(SinapsisAPIEnvVarDefaults)


def __getattr__(name: str) -> str:
    """To use as an import, when updating the value is not important"""
    if name in SinapsisAPIEnvVarDefaults.model_fields:
        return SinapsisAPIEnvVarDefaults.model_fields[name].default.value

    raise AttributeError(f"Sinapsis API env module does not have `{name}` env var")


__all__ = (*list(SinapsisAPIEnvVarDefaults.model_fields.keys()), "SinapsisAPIEnvVarDefaults")

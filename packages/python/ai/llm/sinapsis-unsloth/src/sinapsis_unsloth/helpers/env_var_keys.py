from typing import Any

from pydantic import BaseModel
from sinapsis.env_vars import EnvVarEntry, doc_str, return_docs_for_vars


class _HuggingFaceKeys(BaseModel):
    """Env vars for Hugging Face."""

    HF_TOKEN: EnvVarEntry = EnvVarEntry(
        var_name="HF_TOKEN", default_value="", allowed_values=None, description="set API token for Hugging Face"
    )


HuggingFaceEnvVars = _HuggingFaceKeys()

doc_str = return_docs_for_vars(
    HuggingFaceEnvVars, docs=doc_str, string_for_doc="""Hugging Face env vars available: \n"""
)
__doc__ = doc_str


def __getattr__(name: str) -> Any:
    """To use as an import, when updating the value is not important."""
    if name in HuggingFaceEnvVars.model_fields:
        return HuggingFaceEnvVars.model_fields[name].default.value

    raise AttributeError(f"Agent does not have `{name}` env var")


_all__ = (*list(HuggingFaceEnvVars.model_fields.keys()), "HuggingFaceEnvVars")

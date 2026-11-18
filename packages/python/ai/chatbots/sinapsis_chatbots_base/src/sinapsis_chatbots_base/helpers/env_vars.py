from typing import Any

from pydantic import BaseModel
from sinapsis.env_vars import EnvVarEntry, doc_str, return_docs_for_vars


class _ChatbotsBaseEnvVars(BaseModel):
    """Env vars for Sinapsis Chatbots Base."""

    HF_TOKEN: EnvVarEntry = EnvVarEntry(
        var_name="HF_TOKEN", default_value="", allowed_values=None, description="Set API key for HuggingFace API"
    )

    LLM_API_KEY: EnvVarEntry = EnvVarEntry(
        var_name="LLM_API_KEY",
        default_value="",
        allowed_values=None,
        description="Set API key for generic LLM endpoints (OpenAI-compatible API)",
    )


ChatbotsBaseEnvVars = _ChatbotsBaseEnvVars()

doc_str = return_docs_for_vars(
    ChatbotsBaseEnvVars, docs=doc_str, string_for_doc="""Sinapsis Chatbots Base env vars available: \n"""
)
__doc__ = doc_str


def __getattr__(name: str) -> Any:
    """Allows accessing environment variable default values directly as module attributes.

    Args:
        name (str): The name of the environment variable.

    Returns:
        Any: The default value of the requested environment variable.

    Raises:
        AttributeError: If the requested attribute `name` is not a defined
                        environment variable.
    """
    if name in ChatbotsBaseEnvVars.model_fields:
        return ChatbotsBaseEnvVars.model_fields[name].default.value

    raise AttributeError(f"Agent does not have `{name}` env var")


__all__ = (*list(ChatbotsBaseEnvVars.model_fields.keys()), "ChatbotsBaseEnvVars")

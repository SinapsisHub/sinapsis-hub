from sinapsis_core.utils.env_var_keys import (
    EnvVarEntry,
    SinapsisEnvVarDefaults,
    return_docs_for_vars,
)

doc_str = return_docs_for_vars(SinapsisEnvVarDefaults)


__doc__ = doc_str


def __getattr__(name: str) -> str:
    """To use as an import, when updating the value is not important"""
    if name in SinapsisEnvVarDefaults.model_fields:
        return SinapsisEnvVarDefaults.model_fields[name].default.value

    raise AttributeError(f"Agent does not have `{name}` env var")


__all__ = (
    *list(SinapsisEnvVarDefaults.model_fields.keys()),
    "SinapsisEnvVarDefaults",
    "EnvVarEntry",
    "return_docs_for_vars",
)

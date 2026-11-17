from .sdk_env_vars import SinapsisSDKEnvVarDefaults


def __getattr__(name: str) -> str:
    """To use as an import, when updating the value is not important."""
    if name in SinapsisSDKEnvVarDefaults.model_fields:
        return SinapsisSDKEnvVarDefaults.model_fields[name].default.value

    raise AttributeError(f"Agent does not have `{name}` env var")


__all__ = (*list(SinapsisSDKEnvVarDefaults.model_fields.keys()), "SinapsisSDKEnvVarDefaults")

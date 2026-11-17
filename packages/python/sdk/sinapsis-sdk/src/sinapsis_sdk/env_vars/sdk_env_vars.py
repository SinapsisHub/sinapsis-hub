from pydantic import BaseModel
from sinapsis.env_vars import EnvVarEntry, return_docs_for_vars


class _SinapsisSDKEnvVarDefaults(BaseModel):
    SINAPSIS_CLOUD_API_URL: EnvVarEntry = EnvVarEntry(
        var_name="SINAPSIS_API_URL",
        default_value="https://api.sinapsis.tech/",
        description="api url, traditionally api.sinapsis.tech unless self hosting",
        return_type=str,
    )
    SINAPSIS_LOCAL_API_URL: EnvVarEntry = EnvVarEntry(
        var_name="SINAPSIS_API_URL",
        default_value="http://localhost:8080/",
        description="local api host with port",
        return_type=str,
    )
    SINAPSIS_BASE_API_URL: EnvVarEntry = EnvVarEntry(
        var_name="SINAPSIS_BASE_API_URL",
        default_value="/api/v1",
        allowed_values=None,
        description="Cloud API base url. When using locally this can remain empty.",
        return_type=str,
    )
    SINAPSIS_EXECUTION_MODE: EnvVarEntry = EnvVarEntry(
        var_name="SINAPSIS_EXECUTION_MODE",
        default_value="",
        allowed_values=["local", "cloud", "local-api"],
        description="Superseding execution mode. Usually used when a user wants to override the mode in configuration.",
        return_type=str,
    )


SinapsisSDKEnvVarDefaults: BaseModel = _SinapsisSDKEnvVarDefaults()


__doc__ = return_docs_for_vars(SinapsisSDKEnvVarDefaults)

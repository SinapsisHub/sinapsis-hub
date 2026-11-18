from pydantic import BaseModel
from sinapsis.env_vars import EnvVarEntry, return_docs_for_vars


class _SinapsisSerializerCoreEnvVarDefaults(BaseModel):
    STREAMING_STAGING_DIR: EnvVarEntry = EnvVarEntry(
        var_name="STREAMING_STAGING_DIR",
        default_value="/data/staging",
        allowed_values=None,
        description="Path to the directory where streaming data will be stored temporarily",
        return_type=str,
    )
    SAVING_PERSISTENT_DIR: EnvVarEntry = EnvVarEntry(
        var_name="SAVING_PERSISTENT_DIR",
        default_value="/data/persistent",
        allowed_values=None,
        description="Path to the persistent directory where streaming data will be stored",
        return_type=str,
    )
    IN_MEMORY_DB_OBJECT_SIZE_THR: EnvVarEntry = EnvVarEntry(
        var_name="IN_MEMORY_DB_THR",
        default_value=20 * 1024 * 1024,  # 20MB
        allowed_values=None,
        description="If set to a positive integer, representing megabytes of data, data transfers will be done through"
        "a combination of in-memory databases (e.g. redis) and rmq control signals",
        return_type=int,
    )
    SHM_DB_OBJECT_SIZE_THR: EnvVarEntry = EnvVarEntry(
        var_name="SHM_DB_OBJECT_SIZE_THR",
        default_value=0,  # 50 * 1024 * 1024,     #50MB
        allowed_values=None,
        description="If set to a positive integer, representing megabytes of data, data transfers will be done through"
        "shared memory. Note that this only applies to side car mode, where containers live on the same"
        "hardware. This also takes precedence over in-memory databases.",
        return_type=int,
    )
    RMQ_OBJECT_SIZE_THR: EnvVarEntry = EnvVarEntry(
        var_name="RMQ_OBJECT_SIZE_THR",
        default_value=128 * 1024,  # 128 KB
        allowed_values=None,
        description="If set to a positive integer, data will be transferred will be done through RabbitMQ",
        return_type=int,
    )
    DISK_OBJECT_SIZE_THR: EnvVarEntry = EnvVarEntry(
        var_name="DISK_OBJECT_SIZE_THR",
        default_value=500 * 1024 * 1024,  # 500 MB
        allowed_values=None,
        description="Threshold for data in Containers to be saved in disk. This is particularly useful for models, "
        "images, and data in general that is saved by a given template",
        return_type=int,
    )
    S3_OBJECT_SHARING_ENABLED: EnvVarEntry = EnvVarEntry(
        var_name="S3_OBJECT_SHARING_ENABLED",
        default_value=False,
        allowed_values=None,
        description="Flag to determine whether the data should be transferred through a S3 bucket.",
        return_type=bool,
    )
    SHM_ROOT_DIR: EnvVarEntry = EnvVarEntry(
        var_name="SHM_ROOT_DIR",
        default_value="/dev/shm",
        allowed_values=None,
        description="Path to the Shared memory root directory",
        return_type=str,
    )
    TRANSIENT_ROOT_DIR: EnvVarEntry = EnvVarEntry(
        var_name="TRANSIENT_ROOT_DIR",
        default_value="/data/worker_temp",
        allowed_values=None,
        description="Path to the Worker temporary directory",
        return_type=str,
    )


SinapsisSerializerCoreEnvVarDefaults: BaseModel = _SinapsisSerializerCoreEnvVarDefaults()


__doc__ = return_docs_for_vars(SinapsisSerializerCoreEnvVarDefaults)


def __getattr__(name: str) -> str:
    """to use as an import, when updating the value is not important"""
    if name in SinapsisSerializerCoreEnvVarDefaults.model_fields:
        return SinapsisSerializerCoreEnvVarDefaults.model_fields[name].default.value

    raise AttributeError(f"Agent does not have `{name}` env var")

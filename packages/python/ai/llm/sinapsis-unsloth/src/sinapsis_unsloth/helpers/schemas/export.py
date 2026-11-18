from pydantic import BaseModel


class UnslothExportBaseArgs(BaseModel):
    """Base arguments for exporting models with Unsloth.

    Attributes:
        save_path (str): The path where the exported model will be saved. Can be used for both local saves and hub
            pushes.
        max_shard_size (str | int, optional): The maximum size of each shard in bytes or a string like "5GB".
            Defaults to "5GB".
        maximum_memory_usage (float, optional): The maximum memory usage as a fraction of available memory.
            Defaults to 0.75.
    """

    save_path: str
    max_shard_size: str | int = "5GB"
    maximum_memory_usage: float = 0.75


class UnslothExportGGUFArgs(UnslothExportBaseArgs):
    """Arguments for exporting GGUF models with Unsloth.

    Attributes:
        quantization_method (str | list[str], optional): The method used for quantization. Defaults to "fast_quantized".
    """

    quantization_method: str | list[str] = "fast_quantized"


class UnslothExportMergedArgs(UnslothExportBaseArgs):
    """Arguments for exporting merged models with Unsloth.

    Attributes:
        save_method (str): The method to use for saving the export. Defaults to 'merged_16bit'.
    """

    save_method: str = "merged_16bit"

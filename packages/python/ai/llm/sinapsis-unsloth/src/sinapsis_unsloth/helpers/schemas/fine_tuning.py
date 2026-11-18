from sinapsis_unsloth.helpers.chat_templates import UNSLOTH_TEMPLATES
from sinapsis_unsloth.helpers.schemas.base import ChatTemplateConfig

from typing import Literal

from datasets.features import Features
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sinapsis.env_vars import SINAPSIS_CACHE_DIR


class UnslothLoraArgs(BaseModel):
    """Configuration arguments for LoRA (Low-Rank Adaptation) initialization.

    Attributes:
        r (int): The rank of the LoRA matrices. Higher rank allows for more expressivity
            but increases trainable parameters and memory usage. Defaults to 16.
        target_modules (list[str]): List of module names to apply LoRA adapters to.
            Defaults to all linear layers ["q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj"].
        lora_alpha (int): The scaling factor for LoRA. A higher alpha places more
            emphasis on the adapter weights. Defaults to 16.
        lora_dropout (float): The dropout probability for LoRA layers. Unsloth recommends
            0.0 for optimized performance. Defaults to 0.0.
        bias (str): Specifies how biases are handled. Options are "none", "all", or
            "lora_only". Unsloth optimizes for "none". Defaults to "none".
        use_gradient_checkpointing (str | bool): Enables gradient checkpointing to save VRAM.
            "unsloth" uses optimized kernels, True uses standard PyTorch checkpointing.
            Defaults to "unsloth".
        random_state (int): Random seed for initialization reproducibility. Defaults to 3407.
        use_rslora (bool): If True, uses Rank-Stabilized LoRA (scaling = alpha / sqrt(r))
            instead of standard LoRA (scaling = alpha / r). Defaults to False.
        modules_to_save (list[str] | None): List of additional modules (like "embed_tokens"
            or "lm_head") to be set as trainable and saved. Defaults to None.
        loftq_config (dict | None): Configuration for LoftQ initialization. Used only if
            LoftQ is required. Defaults to an empty dict.
    """

    r: int = 16
    target_modules: list[str] = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    lora_alpha: int = 16
    lora_dropout: float = 0.0
    bias: str = "none"
    use_gradient_checkpointing: str | bool = "unsloth"
    random_state: int = 3407
    use_rslora: bool = False
    modules_to_save: list[str] | None = None
    loftq_config: dict = Field(default_factory=dict)


class UnslothTrainerArgs(BaseModel):
    """Arguments specific to the Unsloth/SFT Trainer initialization.

    Attributes:
        dataset_text_field (str): Name of the column containing the text data.
            Defaults to "text".
        dataset_num_proc (int | None): Number of processes to use for processing the dataset.
            Defaults to None.
        max_length (int): Maximum length of the tokenized sequence. Sequences longer than
            this are truncated. Defaults to 1024.
        packing (bool): Whether to group multiple sequences into fixed-length blocks to
            improve computational efficiency. Defaults to False.
        packing_strategy (Literal["bfd", "wrapped"]): Strategy for packing sequences.
            "bfd" (Best-Fit Decreasing) or "wrapped". Defaults to "bfd".
        eval_packing (bool): Whether to pack the eval dataset. Defaults to False.
        completion_only_loss (bool | None): Whether to compute loss only on the completion
            part of the sequence. Supported for prompt-completion datasets. Defaults to None.
        assistant_only_loss (bool): Whether to compute loss only on the assistant part of
            the sequence. Supported for conversational datasets. Defaults to False.
        loss_type (Literal["nll", "dft"]): Type of loss to use. "nll" (Negative Log-Likelihood)
            or "dft" (Dynamic Fine-Tuning). Defaults to "nll".
        activation_offloading (bool): Whether to offload activations to the CPU to save
            VRAM. Defaults to False.
    """

    dataset_text_field: str = "text"
    dataset_num_proc: int | None = None
    max_length: int = 1024
    packing: bool = False
    packing_strategy: Literal["bfd", "wrapped"] = "bfd"
    eval_packing: bool = False
    completion_only_loss: bool | None = None
    assistant_only_loss: bool = False
    loss_type: Literal["nll", "dft"] = "nll"
    activation_offloading: bool = False


class UnslothTrainingArgs(BaseModel):
    """Arguments for the Hugging Face TrainingArguments class.

    Attributes:
        output_dir (str): Directory where checkpoints and model outputs will be saved.
        overwrite_output_dir (bool): If True, overwrite the content of the output directory.
        eval_strategy (Literal["no", "steps", "epoch"]): Strategy for evaluation.
        eval_steps (int | float | None): Number of steps between evaluations.
        per_device_train_batch_size (int): Batch size per GPU for training.
        per_device_eval_batch_size (int): Batch size per GPU for evaluation.
        gradient_accumulation_steps (int): Number of update steps to accumulate gradients for.
        eval_accumulation_steps (int | None): Number of steps to accumulate evaluation predictions.
        learning_rate (float): Initial learning rate for AdamW.
        weight_decay (float): Weight decay to apply to all layers except bias/LayerNorm.
        num_train_epochs (float): Total number of training epochs.
        max_steps (int | None): Total number of training steps. Overrides epochs.
        lr_scheduler_type (str): Scheduler type (e.g., "linear", "cosine").
        warmup_ratio (float): Ratio of total steps used for linear warmup.
        logging_steps (int | float): Number of steps between logging events.
        save_strategy (Literal["no", "steps", "epoch"]): Strategy for saving checkpoints.
        save_steps (int | float): Number of steps between saves.
        fp16 (bool): Whether to use FP16 16-bit precision.
        bf16 (bool): Whether to use BF16 16-bit precision (requires Ampere+ GPU).
        optim (str): Optimizer name (e.g., "adamw_torch", "adamw_8bit").
        report_to (str | list[str]): List of integrations to report to (e.g., "wandb").
        push_to_hub (bool): Whether to push the model to the Hub after training.
    """

    output_dir: str = "trainer_output"
    overwrite_output_dir: bool = False
    eval_strategy: Literal["no", "steps", "epoch"] = "no"
    eval_steps: int | float | None = None
    per_device_train_batch_size: int = 8
    per_device_eval_batch_size: int = 8
    gradient_accumulation_steps: int = 1
    eval_accumulation_steps: int | None = None
    torch_empty_cache_steps: int | None = None
    learning_rate: float = 5e-5
    weight_decay: float = 0.0
    max_grad_norm: float = 1.0
    num_train_epochs: float = 3.0
    max_steps: int | None = None
    lr_scheduler_type: str = "linear"
    warmup_ratio: float = 0.0
    warmup_steps: int | None = None
    logging_strategy: Literal["no", "steps", "epoch"] = "steps"
    logging_first_step: bool = False
    logging_steps: int | float = 500
    save_strategy: Literal["no", "steps", "epoch", "best"] = "steps"
    save_steps: int | float = 500
    save_only_model: bool = False
    use_cpu: bool = False
    seed: int = 3407
    data_seed: int | None = None
    bf16: bool = False
    fp16: bool = False
    dataloader_drop_last: bool = False
    dataloader_num_workers: int = 0
    remove_unused_columns: bool = True
    load_best_model_at_end: bool = False
    metric_for_best_model: str = "loss"
    optim: str = "adamw_torch"
    report_to: str | list[str] = "none"
    push_to_hub: bool = False
    hub_model_id: str | None = None


class DataLoaderArgs(BaseModel):
    """Arguments for the `load_dataset` function.

    Attributes:
        path (str): The path or identifier of the dataset (e.g., 'imdb', 'json').
        name (str | None): The configuration name of the dataset.
        data_dir (str | None): Path to the directory containing the data files.
        data_files (str | list | dict | None): Path(s) to source data files.
        split (str | None): Which split of the data to load (e.g., 'train').
        cache_dir (str): Directory to read/write data. Defaults to SINAPSIS_CACHE_DIR.
        num_proc (int | None): Number of processes for loading.
    """

    path: str
    name: str | None = None
    data_dir: str | None = None
    data_files: str | None = None
    split: str | None = None
    cache_dir: str = SINAPSIS_CACHE_DIR
    features: Features | None = None
    num_proc: int | None = None
    model_config = ConfigDict(arbitrary_types_allowed=True)


class MapArgs(BaseModel):
    """Arguments for the `dataset.map` function.

    Attributes:
        batched (bool): Whether to provide a batch of examples to the function.
        batch_size (int): Number of examples per batch. Defaults to 1000.
        num_proc (int): Number of processes for multiprocessing.
        desc (str | None): Meaningful description for the progress bar.
        remove_columns (str | list[str] | None): Columns to remove after mapping.
    """

    desc: str | None = None
    batched: bool = False
    batch_size: int = 1000
    num_proc: int = 0
    keep_in_memory: bool = False
    load_from_cache_file: bool = True


class ShuffleArgs(BaseModel):
    """Arguments for the `dataset.shuffle` function.

    Attributes:
        seed (int | None): Random seed for shuffling.
        keep_in_memory (bool): Whether to keep the shuffled dataset in memory.
    """

    seed: int | None = None
    keep_in_memory: bool = False
    load_from_cache_file: bool = True


class ShuffleConfig(BaseModel):
    """Configuration grouping for dataset shuffling.

    Attributes:
        enabled (bool): Whether to shuffle the dataset. Defaults to False.
        shuffle_args (ShuffleArgs): Arguments passed to the shuffle method.
    """

    enabled: bool = False
    args: ShuffleArgs = Field(default_factory=ShuffleArgs)


class TokenizerArgs(BaseModel):
    """Arguments for the tokenizer's `__call__` method.

    Attributes:
        add_special_tokens (bool): Whether to encode the sequences with special tokens.
        padding (str | bool): Padding strategy ("longest", "max_length", etc.).
        truncation (str | bool): Truncation strategy.
        max_length (int | None): Maximum length of the returned list and/or tensor.
        stride (int): Window overlap for overflowing tokens.
        return_tensors (str | None): If set, will return tensors instead of lists ('pt', 'tf', 'np').
    """

    add_special_tokens: bool = True
    padding: Literal["longest", "max_length", "do_not_pad"] = "do_not_pad"
    truncation: Literal["longest_first", "only_first", "only_second", "do_not_truncate"] = "do_not_truncate"
    max_length: int | None = None
    stride: int = 0
    is_split_into_words: bool = False
    padding_side: str | None = None
    verbose: bool = True


class PreTokenizeConfig(BaseModel):
    """Configuration grouping for dataset pre-tokenization.

    Attributes:
        enabled (bool): Whether to pre-tokenize the dataset before training.
        tokenization_args (TokenizerArgs): Arguments passed to the tokenizer.
        map_args (MapArgs): Arguments passed to the map function during tokenization.
    """

    enabled: bool = False
    args: TokenizerArgs = Field(default_factory=TokenizerArgs)
    map_args: MapArgs = Field(default_factory=MapArgs)


class DatasetConfig(BaseModel):
    """Configuration grouping for dataset loading and processing.

    Attributes:
        loader_args (DataLoaderArgs): Arguments for loading the dataset.
        map_args (MapArgs): Arguments for general dataset mapping operations.
    """

    loader_args: DataLoaderArgs
    map_args: MapArgs = Field(default_factory=MapArgs)
    shuffle: ShuffleConfig = Field(default_factory=ShuffleConfig)
    pre_tokenize: PreTokenizeConfig = Field(default_factory=PreTokenizeConfig)


class AlpacaConfig(BaseModel):
    """Configuration settings for the Alpaca attribute.

    Attributes:
        task_preamble (str): A string that serves as a preamble to an instruction.
        instruction_key (str): The key used in the input dictionary to identify the instruction text.
        input_key (str | None): The key used in the input dictionary to identify the input text, for context.
        output_key (str): The key used in the output dictionary to identify the generated response.
    """

    task_preamble: str = """Below is an instruction that describes a task, paired with an input that provides further
    context. Write a response that appropriately completes the request.\n\n"""
    instruction_key: str = "instruction"
    input_key: str = "input"
    output_key: str = "output"


class ToShareGPTArgs(BaseModel):
    """Configuration attributes for the `to_sharegpt` conversion method.

    Attributes:
        merged_prompt (str): Prompt string for merging instruction and input.
        merged_column_name (str): Column name for the merged instruction.
        output_column_name (str): Column name for the response output.
        remove_unused_columns (bool): Whether to remove columns not used in conversion.
        conversation_extension (int): Number of additional messages for multi-turn simulation.
        random_state (int): Random seed for reproducibility.
    """

    merged_prompt: str = ""
    merged_column_name: str = "instruction"
    output_column_name: str = "output"
    remove_unused_columns: bool = True
    conversation_extension: int = 1
    random_state: int = 3407


class DataCollatorArgs(BaseModel):
    """Configuration for DataCollatorForSeq2Seq.

    Attributes:
        max_length (int | None): Max sequence length for padding.
        padding (Literal["longest", "max_length", "do_not_pad"]): Padding strategy.
        label_pad_token_id (int): Token ID used for padding labels. Defaults to -100.
    """

    max_length: int | None = None
    padding: Literal["longest", "max_length", "do_not_pad"] = "do_not_pad"
    label_pad_token_id: int = -100


class ConversationalDatasetConfig(DatasetConfig):
    """Extended dataset configuration for conversational training.

    Attributes:
        input_format (Literal["alpaca", "sharegpt"]): Input dataset format.
        to_sharegpt_args (ToShareGPTArgs): Arguments for converting Alpaca to ShareGPT.
    """

    input_format: Literal["alpaca", "sharegpt"]
    to_sharegpt_args: ToShareGPTArgs = Field(default_factory=ToShareGPTArgs)


class TrainingChatTemplateConfig(ChatTemplateConfig):
    """Configuration for the target chat template and formatting.

    Attributes:
        target_format (str): The name of the target chat template (e.g., 'deepseek-r1').
        mapping (ChatMapping): Role mapping configuration.
        map_eos_token (bool): Whether to map the EOS token.
        system_message (str | None): System message to prepend to conversations.
    """

    target_format: str

    @field_validator("target_format")
    @classmethod
    def validate_chat_template(cls, v: str) -> str:
        """Validate that the target dataset format is a supported chat template.

        Args:
            v (str): The template name to validate

        Raises:
            ValueError: If the chat template is not found in available CHAT_TEMPLATES

        Returns:
            The validated template name if supported
        """
        if v not in UNSLOTH_TEMPLATES:
            raise ValueError(f"Invalid chat template. Available: {UNSLOTH_TEMPLATES}")
        return v

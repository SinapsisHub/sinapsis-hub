from typing import Literal

import torch
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.dataclasses import dataclass
from sinapsis.env_vars import SINAPSIS_CACHE_DIR


@dataclass(frozen=True)
class RoleDelimiters:
    """Defines delimiters for different conversation roles in chat templates.

    These delimiters mark the beginning of different conversation turns in a chat-based
    language model interaction.

    Attributes:
        instruction (str): String that marks the start of a user instruction/input.
        response (str): String that marks the start of the model's response.
        system (str): Optional string that marks the start of a system message.
    """

    instruction: str
    response: str
    system: str | None = None


@dataclass(frozen=True, config=ConfigDict(arbitrary_types_allowed=True))
class ChatTemplatePatterns:
    """Registry of chat template patterns compatible with Unsloth's chat templates.

    Contains predefined sets of role delimiters for various popular chat-based language
    model formats. Each attribute represents a different template style with its specific
    delimiters for user instructions, model responses, and system messages.
    """

    unsloth: RoleDelimiters = RoleDelimiters(instruction=">>> User: ", response=">>> Assistant: ")
    zephyr: RoleDelimiters = RoleDelimiters(instruction="<|user|>\n", response="<|assistant|>\n", system="<|system|>\n")
    chatml: RoleDelimiters = RoleDelimiters(
        instruction="<|im_start|>user\n", response="<|im_start|>assistant\n", system="<|im_start|>system\n"
    )
    mistral: RoleDelimiters = RoleDelimiters(instruction="[INST] ", response=" [/INST]")
    llama: RoleDelimiters = RoleDelimiters(instruction="[INST] <<SYS>>\n", response="[/INST]", system="<<SYS>>")
    vicuna: RoleDelimiters = RoleDelimiters(instruction="USER: ", response="ASSISTANT: ")
    vicuna_old: RoleDelimiters = RoleDelimiters(instruction="### Human: ", response="### Assistant: ")
    alpaca: RoleDelimiters = RoleDelimiters(
        instruction="### Instruction:\n", response="### Response:\n", system="### Input:\n"
    )
    gemma: RoleDelimiters = RoleDelimiters(instruction="<start_of_turn>user\n", response="<start_of_turn>model\n")
    gemma_chatml: RoleDelimiters = chatml
    gemma2: RoleDelimiters = gemma
    gemma2_chatml: RoleDelimiters = gemma_chatml
    llama_3: RoleDelimiters = RoleDelimiters(
        instruction="<|start_header_id|>user<|end_header_id|>\n\n",
        response="<|start_header_id|>assistant<|end_header_id|>\n\n",
        system="<|start_header_id|>system<|end_header_id|>\n\n",
    )
    llama3: RoleDelimiters = llama_3
    phi_3: RoleDelimiters = RoleDelimiters(instruction="<|user|>\n", response="<|assistant|>\n", system="<|system|>\n")
    phi_35: RoleDelimiters = phi_3
    phi_3_5: RoleDelimiters = phi_3
    llama_3_1: RoleDelimiters = llama_3
    llama_31: RoleDelimiters = llama_3
    llama_3_2: RoleDelimiters = llama_3
    llama_3_3: RoleDelimiters = llama_3
    llama_32: RoleDelimiters = llama_3
    llama_33: RoleDelimiters = llama_3
    qwen_2_5: RoleDelimiters = chatml
    qwen_25: RoleDelimiters = qwen_2_5
    qwen25: RoleDelimiters = qwen_2_5
    qwen2_5: RoleDelimiters = qwen_2_5
    phi_4: RoleDelimiters = RoleDelimiters(
        instruction="<|im_start|>user<|im_sep|>",
        response="<|im_start|>assistant<|im_sep|>",
        system="<|im_start|>system<|im_sep|>",
    )
    gemma_3: RoleDelimiters = gemma
    gemma3: RoleDelimiters = gemma
    deepseek_r1: RoleDelimiters = RoleDelimiters(instruction="<\uff5cUser\uff5c>", response="<\uff5cAssistant\uff5c>")
    qwen_3: RoleDelimiters = chatml
    qwen3: RoleDelimiters = chatml
    qwen3_instruct: RoleDelimiters = chatml
    qwen3_thinking: RoleDelimiters = chatml

    gemma_3n: RoleDelimiters = gemma
    gemma3n: RoleDelimiters = gemma
    lfm_2: RoleDelimiters = chatml
    yi_chat: RoleDelimiters = chatml
    starling: RoleDelimiters = RoleDelimiters(
        instruction="GPT4 Correct User: ",
        response="<|end_of_turn|>GPT4 Correct Assistant: ",
        system="GPT4 Correct System: ",
    )
    gpt_oss: RoleDelimiters = RoleDelimiters(
        instruction="<|start|>user<|message|>", response="<|start|>assistant", system="<|start|>system<|message|>"
    )
    gptoss: RoleDelimiters = gpt_oss


class UnslothModelArgs(BaseModel):
    """Configuration attributes for Unsloth model loading.

    Attributes:
        model_name (str): The name of the model to be used.
        cache_dir (str, optional): Directory where models are cached. Defaults to SINAPSIS_CACHE_DIR.
        max_seq_length (int, optional): Maximum sequence length for input data. Defaults to 2048.
        dtype (Literal["auto", "bfloat16", "float16"], optional): Data type for model weights. Defaults to "auto".
        load_in_4bit (bool, optional): Whether to use 4-bit quantization. Defaults to True.
        load_in_8bit (bool, optional): Whether to use 8-bit quantization. Defaults to False.
        load_in_16bit (bool, optional): Whether to use 16-bit quantization. Defaults to False.
        full_finetuning (bool, optional): Whether to perform full fine-tuning. Defaults to False.
        device_map (str, optional): Device mapping strategy for model parallelism. Defaults to "sequential".
        use_gradient_checkpointing (str, optional): Gradient checkpointing strategy. Defaults to "unsloth".
        fast_inference (bool, optional): Whether to enable fast inference mode. Defaults to False.
        gpu_memory_utilization (float, optional): Maximum GPU memory utilization as a fraction of total available
            memory. Defaults to 0.5.
        random_state (int, optional): Random state for reproducibility. Defaults to 3407.
        max_lora_rank (int, optional): Maximum rank for LoRA layers. Defaults to 64.
    """

    model_name: str
    cache_dir: str = SINAPSIS_CACHE_DIR
    max_seq_length: int = 2048
    dtype: Literal["auto", "bfloat16", "float16"] = "auto"
    load_in_4bit: bool = True
    load_in_8bit: bool = False
    load_in_16bit: bool = False
    full_finetuning: bool = False
    device_map: str = "sequential"
    use_gradient_checkpointing: str = "unsloth"
    fast_inference: bool = False
    gpu_memory_utilization: float = 0.5
    random_state: int = 3407
    max_lora_rank: int = 64
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("dtype", mode="after")
    def convert_dtype(cls, v: str) -> torch.dtype | None:
        """Convert a string to a torch dtype or None for Unsloth to automatically assign it.

        Args:
            cls (type): The class instance.
            v (str): The dtype as string.

        Returns:
            torch.dtype | None: The converted torch dtype if the input is valid, otherwise None
                to let Unsloth assign it.
        """
        if v == "bfloat16":
            return torch.bfloat16
        elif v == "float16":
            return torch.float16

        return None


class ChatMapping(BaseModel):
    """Configuration for chat template role mapping.

    Attributes:
        role (str): Key name for the role field.
        content (str): Key name for the content field.
        user (str): Value identifying the user role.
        assistant (str): Value identifying the assistant role.
    """

    role: str = "role"
    content: str = "content"
    user: str = "user"
    assistant: str = "assistant"


class ChatTemplateConfig(BaseModel):
    """Configuration for the target chat template and formatting.

    Attributes:
        target_format (str): The name of the target chat template (e.g., 'deepseek-r1').
        mapping (ChatMapping): Role mapping configuration.
        map_eos_token (bool): Whether to map the EOS token.
        system_message (str | None): System message to prepend to conversations.
    """

    mapping: ChatMapping = Field(default_factory=ChatMapping)
    map_eos_token: bool = True
    system_message: str | None = None

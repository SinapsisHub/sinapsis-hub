from sinapsis_unsloth.helpers.chat_templates import UNSLOTH_TEMPLATES
from sinapsis_unsloth.helpers.schemas.base import ChatTemplateConfig

from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator


class UnslothGenerateArgs(BaseModel):
    """Configuration arguments for model generation.

    Attributes:
        max_new_tokens (int): The maximum number of tokens to generate.
        min_new_tokens (int | None, optional): The minimum number of tokens to generate.
            Defaults to None.
        stop_strings (str | list[str] | None, optional): A string or list of strings that
            should stop generation when encountered. Defaults to None.
        do_sample (bool, optional): Whether to use sampling; use greedy decoding otherwise.
            Defaults to True.
        num_beams (int, optional): Number of beams for beam search. 1 means no beam search.
            Defaults to 1.
        use_cache (bool, optional): Whether to use key/value cache for faster generation.
            Defaults to True.
        cache_implementation (Literal["dynamic", "static", "offloaded", "offloaded_static", "quantized"], optional):
            The cache implementation to use. "dynamic" is standard, "static" pre-allocates
            memory (faster but higher VRAM), "offloaded" moves cache to CPU. Defaults to "dynamic".
        temperature (float, optional): The value used to modulate the next token probabilities.
            1.0 is neutral. Lower is more deterministic. Defaults to 1.0.
        top_k (int, optional): The number of highest probability vocabulary tokens to keep
            for top-k-filtering. Defaults to 50.
        top_p (float, optional): If set to float < 1, only the smallest set of most probable
            tokens with probabilities that add up to top_p or higher are kept for generation.
            Defaults to 1.0.
        min_p (float | None, optional): Minimum probability for a token to be considered.
            Defaults to None.
        repetition_penalty (float, optional): The parameter for repetition penalty. 1.0 means
            no penalty. Defaults to 1.0.
    """

    max_new_tokens: int
    min_new_tokens: int | None = None
    stop_strings: str | list[str] | None = None
    do_sample: bool = True
    num_beams: int = 1
    use_cache: bool = True
    cache_implementation: Literal["dynamic", "static", "offloaded", "offloaded_static", "quantized"] = "dynamic"
    temperature: float = 1.0
    top_k: int = 50
    top_p: float = 1.0
    min_p: float | None = None
    repetition_penalty: float = 1.0
    model_config = ConfigDict(extra="allow")


class InstructChatConfig(BaseModel):
    """Configuration for instruction-based chat templates (e.g., Alpaca).

    Attributes:
        task_preamble (str): The system prompt or instruction preamble prepended
            to the user input (e.g., 'Below is an instruction...').
    """

    task_preamble: str


class ConversationalChatConfig(ChatTemplateConfig):
    """Configuration for the target chat template and formatting.

    Attributes:
        chat_template (str): The name of the target chat template (e.g., 'deepseek-r1').
        mapping (ChatMapping): Role mapping configuration.
        map_eos_token (bool): Whether to map the EOS token.
        system_message (str | None): System message to prepend to conversations.
    """

    chat_template: str

    @field_validator("chat_template")
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


class ReasoningChatConfig(ConversationalChatConfig):
    """Configuration for reasoning-based chat templates (e.g., DeepSeek R1).

    Extends ConversationalChatConfig to support Chain-of-Thought (CoT) parsing.

    Attributes:
        reasoning_open_tag (str): The tag marking the start of the reasoning/thought block
            (e.g., '<think>').
        reasoning_close_tag (str): The tag marking the end of the reasoning/thought block
            (e.g., '</think>').
    """

    reasoning_open_tag: str
    reasoning_close_tag: str

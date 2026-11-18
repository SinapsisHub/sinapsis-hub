from sinapsis_unsloth.helpers.schemas.base import RoleDelimiters
from sinapsis_unsloth.helpers.schemas.inference import InstructChatConfig
from sinapsis_unsloth.templates.inference.unsloth_inference_base import (
    UnslothInferenceBase,
    UnslothInferenceBaseAttributes,
)

from sinapsis.data_transport import TextPacket
from transformers import PreTrainedTokenizer


class UnslothInferenceInstruct(UnslothInferenceBase):
    """Template for instruction-tuned models (e.g., Alpaca style).

    Handles formatting of instruction prompts with optional context injection.

    Usage example:

    agent:
      name: my_test_agent
    templates:
    - template_name: InputTemplate
      class_name: InputTemplate
      attributes: {}
    - template_name: UnslothInferenceInstruct
      class_name: UnslothInferenceInstruct
      template_input: InputTemplate
      attributes:
        model_args:
          model_name: 'unsloth/Llama-3.2-3B-Instruct'
          max_seq_length: 2048
          dtype: auto
          load_in_4bit: true
          load_in_8bit: false
          load_in_16bit: false
          full_finetuning: false
          device_map: sequential
          use_gradient_checkpointing: unsloth
          fast_inference: false
          gpu_memory_utilization: 0.5
          random_state: 3407
          max_lora_rank: 64
        rag_context_key: null
        generate_args:
          max_new_tokens: 256
          min_new_tokens: null
          stop_strings: null
          do_sample: true
          num_beams: 1
          use_cache: true
          cache_implementation: dynamic
          temperature: 1.0
          top_k: 50
          top_p: 1.0
          min_p: null
          repetition_penalty: 1.0
        stream: false
        chat_config:
          task_preamble: Write a response that appropriately completes the request

    """

    class AttributesBaseModel(UnslothInferenceBaseAttributes):
        """Configuration attributes for Unsloth instruction inference.

        Extends the base inference attributes to support standard instruction-response
        formats (Alpaca style) with configurable task preambles.

        Attributes:
            chat_config (InstructChatConfig): Configuration object defining the
                task preamble (system instruction) to be prepended to the user input.
        """

        chat_config: InstructChatConfig

    def _setup_patterns(self) -> RoleDelimiters | None:
        """Set up patterns for role delimiters.

        Returns:
            RoleDelimiters: An instance of RoleDelimiters or None if not set.
        """
        return self.PATTERNS.alpaca

    def _prepare_tokenizer(self) -> PreTrainedTokenizer:
        """Returns the tokenizer as-is without chat template application.

        Returns:
            PreTrainedTokenizer: Same tokenizer as loaded by the parent class.
        """
        return self.tokenizer

    def _format_inputs(self, text_packet: TextPacket) -> str:
        """Formats the input for the instruct model by combining various components.

        Args:
            text_packet (TextPacket): The input packet containing the content and other relevant information.

        Returns:
            str: The formatted input string to be used with the instruct model.

        Raises:
            ValueError: If the pattern is not initialized for the instruct model type.
        """
        if self.pattern is None:
            raise ValueError("Pattern not initialized for instruct model type")
        extra_context = self.get_extra_context(text_packet)
        return (
            f"{self.attributes.chat_config.task_preamble}"
            f"{self.pattern.instruction}"
            f"{text_packet.content}\n\n"
            f"{self.pattern.system}"
            f"{extra_context or ''}\n\n"
            f"{self.pattern.response}"
        )

    def _extract_response(self, output: str) -> str:
        """Extracts the response from the given output string based on the pattern and tokenizer.

        Args:
            output (str): The output string containing the response.

        Returns:
            str: The extracted response.

        Raises:
            ValueError: If the pattern is not initialized for instruct model type.
        """
        if self.pattern is None:
            raise ValueError("Pattern not initialized for instruct model type")
        return self.extract_between_markers(output, self.pattern.response, self.tokenizer.eos_token)

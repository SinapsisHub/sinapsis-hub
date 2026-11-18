from sinapsis_unsloth.helpers.schemas.base import RoleDelimiters
from sinapsis_unsloth.templates.inference.unsloth_inference_base import UnslothInferenceBase

from sinapsis.data_transport import TextPacket
from transformers import PreTrainedTokenizer


class UnslothInferenceCompletion(UnslothInferenceBase):
    """Template for raw text completion using Unsloth.

    Useful for base models (non-instruct) or custom formatting where no chat template is required.

    Usage example:

    agent:
      name: my_test_agent
    templates:
    - template_name: InputTemplate
      class_name: InputTemplate
      attributes: {}
    - template_name: UnslothInferenceCompletion
      class_name: UnslothInferenceCompletion
      template_input: InputTemplate
      attributes:
        model_args:
          model_name: unsloth/Meta-Llama-3.1-8B
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

    """

    def _setup_patterns(self) -> RoleDelimiters | None:
        """Set up patterns for role delimiters.

        Returns:
            RoleDelimiters | None: The configured role delimiters, or None if not set.
        """
        return None

    def _prepare_tokenizer(self) -> PreTrainedTokenizer:
        """Returns the tokenizer as-is without chat template application.

        Returns:
            PreTrainedTokenizer: Same tokenizer as loaded by the parent class.
        """
        return self.tokenizer

    def _format_inputs(self, text_packet: TextPacket) -> str:
        """Formats the input text packet by returning its content.

        Args:
            text_packet (TextPacket): The text packet to format.

        Returns:
            str: The formatted content of the text packet.
        """
        return text_packet.content

    def _extract_response(self, output: str) -> str:
        """Extracts the response from the given output string.

        Args:
            output (str): The output string containing the response and other tokens.

        Returns:
            str: The extracted response.
        """
        return self.extract_between_markers(output, self.tokenizer.bos_token, self.tokenizer.eos_token)

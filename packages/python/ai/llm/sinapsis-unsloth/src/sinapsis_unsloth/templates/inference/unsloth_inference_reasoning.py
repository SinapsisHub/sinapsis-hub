from unsloth.chat_templates import get_chat_template

from sinapsis_unsloth.helpers.chat_templates import DEEPSEEK_R1_CHAT_TEMPLATE
from sinapsis_unsloth.helpers.schemas.inference import ReasoningChatConfig
from sinapsis_unsloth.templates.inference.unsloth_inference_conversational import (
    UnslothInferenceConversational,
    UnslothInferenceConversationalAttributes,
)

from transformers import PreTrainedTokenizer


class UnslothInferenceReasoning(UnslothInferenceConversational):
    """Template for reasoning-based models (e.g., DeepSeek R1).

    Extends conversational inference to support Chain-of-Thought (CoT) extraction.

    Usage example:

    agent:
      name: my_test_agent
    templates:
    - template_name: InputTemplate
      class_name: InputTemplate
      attributes: {}
    - template_name: UnslothInferenceReasoning
      class_name: UnslothInferenceReasoning
      template_input: InputTemplate
      attributes:
        model_args:
          model_name: unsloth/DeepSeek-R1-0528-Qwen3-8B
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
        chat_history_key: null
        chat_config:
          mapping:
            role: role
            content: content
            user: user
            assistant: assistant
          map_eos_token: true
          system_message: null
          chat_template: deepseek-r1
          reasoning_open_tag: '<think>'
          reasoning_close_tag: '</think>'

    """

    class AttributesBaseModel(UnslothInferenceConversationalAttributes):
        """Configuration attributes for Unsloth reasoning inference.

        Extends the conversational attributes to support Chain-of-Thought (CoT)
        processing. Uses a specialized configuration that defines start/end tags
        for extracting the model's internal reasoning steps.

        Attributes:
            chat_config (ReasoningChatConfig): Configuration object containing
                conversational settings plus specific tags for reasoning blocks
                (e.g., <think>, </think>).
        """

        chat_config: ReasoningChatConfig

    def _prepare_tokenizer(self) -> PreTrainedTokenizer:
        """Apply chat template formatting to the tokenizer.

        Returns:
            PreTrainedTokenizer: Same tokenizer with but with apply chat template functionality.
        """
        if self.attributes.chat_config.chat_template in ["deepseek_r1", "deepseek-r1"]:
            chat_template = (
                (self.tokenizer.chat_template, self.tokenizer.eos_token)
                if hasattr(self.tokenizer, "chat_template")
                else (DEEPSEEK_R1_CHAT_TEMPLATE)
            )
        else:
            chat_template = self.attributes.chat_config.chat_template
        return get_chat_template(
            tokenizer=self.tokenizer,
            mapping=self.attributes.chat_config.mapping.model_dump(),
            chat_template=chat_template,
            map_eos_token=self.attributes.chat_config.map_eos_token,
            system_message=self.attributes.chat_config.system_message,
        )

    def _extract_response(self, output: str) -> str | tuple[str, str]:
        """Processes raw model output into final response format.

        Args:
            output (str): Complete generated text including any special tokens

        Returns:
            str | tuple[str, str]: For simple responses (non-reasoning models) a plan string
                is returned, otherwise a tuple of (reasoning_steps, final_answer)
        """
        if self.pattern is None:
            raise ValueError("Pattern not initialized for reasoning model type")
        thinking = self.extract_between_markers(
            output, self.attributes.chat_config.reasoning_open_tag, self.attributes.chat_config.reasoning_close_tag
        )
        answer = self.extract_between_markers(
            output, self.attributes.chat_config.reasoning_close_tag, self.tokenizer.eos_token
        )
        return thinking, answer

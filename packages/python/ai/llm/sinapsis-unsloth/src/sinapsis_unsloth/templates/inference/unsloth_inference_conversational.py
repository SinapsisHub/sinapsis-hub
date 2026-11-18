from unsloth.chat_templates import get_chat_template

from sinapsis_unsloth.helpers.schemas.base import RoleDelimiters
from sinapsis_unsloth.helpers.schemas.inference import ConversationalChatConfig
from sinapsis_unsloth.templates.inference.unsloth_inference_base import (
    UnslothInferenceBase,
    UnslothInferenceBaseAttributes,
)

from sinapsis.data_transport import TextPacket
from transformers import PreTrainedTokenizer


class UnslothInferenceConversationalAttributes(UnslothInferenceBaseAttributes):
    """Configuration attributes for Unsloth conversational inference.

    Extends the base inference attributes to include specific configuration
    for chat templates, role mapping, and system messages.

    Attributes:
        chat_config (ConversationalChatConfig): Configuration object containing the
            target chat template name (e.g., 'llama-3'), role mappings, and
            optional system prompts.
        chat_history_key (str | None): Metadata key to retrieve conversation history.
    """

    chat_history_key: str | None = None
    chat_config: ConversationalChatConfig


class UnslothInferenceConversational(UnslothInferenceBase):
    """Template for optimized conversational LLM inference using Unsloth.

    Handles chat-based interactions, including history retrieval, context injection,
    and chat template application via the tokenizer.

    Usage example:

    agent:
      name: my_test_agent
    templates:
    - template_name: InputTemplate
      class_name: InputTemplate
      attributes: {}
    - template_name: UnslothInferenceConversational
      class_name: UnslothInferenceConversational
      template_input: InputTemplate
      attributes:
        model_args:
          model_name: unsloth/Llama-3.2-3B-Instruct
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
          chat_template: llama-3.2

    """

    AttributesBaseModel = UnslothInferenceConversationalAttributes

    def _setup_patterns(self) -> RoleDelimiters | None:
        """Set up patterns based on the normalized chat template name.

        Returns:
            RoleDelimiters: The role delimiters for the chat template or None if not found.
        """
        normalized_name = self.normalize_template_name(self.attributes.chat_config.chat_template)
        return getattr(self.PATTERNS, normalized_name)

    def _prepare_tokenizer(self) -> PreTrainedTokenizer:
        """Apply chat template formatting to the tokenizer.

        Returns:
            PreTrainedTokenizer: Same tokenizer with but with apply chat template functionality.
        """
        if hasattr(self.tokenizer, "chat_template"):
            chat_template = (self.tokenizer.chat_template, self.tokenizer.eos_token)
        else:
            chat_template = self.attributes.chat_config.chat_template
        return get_chat_template(
            tokenizer=self.tokenizer,
            mapping=self.attributes.chat_config.mapping.model_dump(),
            chat_template=chat_template,
            map_eos_token=self.attributes.chat_config.map_eos_token,
            system_message=self.attributes.chat_config.system_message,
        )

    def _retrieve_history(self, text_packet: TextPacket) -> list[dict[str, str]]:
        """Retrieves the chat history from the text packet, if the key is defined.

        Args:
            text_packet (TextPacket): Tex packet used to retrieve the chat history

        Returns:
            list[dict[str, str]]: OpenAI-style list of dictionaries with the history from oldest to latest.
        """
        if self.attributes.chat_history_key:
            return text_packet.generic_data.get(self.attributes.chat_history_key, [])
        return []

    def _format_inputs(self, text_packet: TextPacket) -> list[str]:
        """Formats the input for the conversational model.

        Args:
            text_packet (TextPacket): The input packet containing the query and context.

        Returns:
            list[str]: A list of formatted messages to be used as input for the conversational model.
        """
        if self.pattern is None:
            raise ValueError("Pattern not initialized for conversational model type")

        extra_context = self.get_extra_context(text_packet)
        prompt = f"Context:\n{extra_context}\n\nQuery:\n{text_packet.content}" if extra_context else text_packet.content
        messages = []

        if self.attributes.chat_config.system_message:
            messages.append({"role": "system", "content": self.attributes.chat_config.system_message})

        messages.extend(self._retrieve_history(text_packet))
        messages.append({"role": "user", "content": prompt})

        return self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    def _extract_response(self, output: str) -> str | tuple[str, str]:
        """Processes raw model output into final response format.

        Args:
            output (str): Complete generated text including any special tokens

        Returns:
            str | tuple[str, str]: For simple responses (non-reasoning models) a plan string
                is returned, otherwise a tuple of (chain_of_though, final_answer)
        """
        if self.pattern is None:
            raise ValueError("Pattern not initialized for conversational model type")
        return self.extract_between_markers(output, self.pattern.response, self.tokenizer.eos_token)

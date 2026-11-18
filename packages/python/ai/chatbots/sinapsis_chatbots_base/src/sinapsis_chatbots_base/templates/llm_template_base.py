import json
import re
from abc import abstractmethod
from typing import Any

from pydantic import Field
from sinapsis.data_transport import DataContainer, LLMContextItem, LLMConversationPacket, LLMMessage
from sinapsis.template import OutputTypes, Template, TemplateAttributes, TemplateAttributeType, UIPropertiesMetadata

from sinapsis_chatbots_base.helpers.llm_conversation import build_chat_message
from sinapsis_chatbots_base.helpers.llm_keys import LLMChatKeys
from sinapsis_chatbots_base.helpers.postprocess_text import postprocess_text
from sinapsis_chatbots_base.helpers.schemas import LLMCompletionArgs, LLMInitArgs
from sinapsis_chatbots_base.helpers.tags import Tags


class LLMTemplateBaseAttributes(TemplateAttributes):
    """Shared attributes for LLM conversation templates.

    Attributes:
        init_args (LLMInitArgs): Backend initialization arguments.
        completion_args (LLMCompletionArgs): Shared completion arguments.
        reasoning_start_tag (str | None): Opening tag used to detect reasoning blocks.
        reasoning_end_tag (str | None): Closing tag used to detect reasoning blocks.
        cleanup_response (bool): Whether to clean the final assistant response text.
    """

    init_args: LLMInitArgs
    completion_args: LLMCompletionArgs = Field(default_factory=LLMCompletionArgs)
    reasoning_start_tag: str | None = "<think>"
    reasoning_end_tag: str | None = "</think>"
    cleanup_response: bool = True


class LLMTemplateBase(Template):
    """Base template for processing `LLMConversationPacket` objects."""

    AttributesBaseModel = LLMTemplateBaseAttributes
    UIProperties = UIPropertiesMetadata(
        category="Chatbots",
        output_type=OutputTypes.TEXT,
        tags=[Tags.CHATBOTS, Tags.CONTEXT, Tags.LLM, Tags.TEXT_COMPLETION, Tags.TEXT],
    )
    attributes: AttributesBaseModel

    def __init__(self, attributes: TemplateAttributeType) -> None:
        super().__init__(attributes)
        self.llm: Any | None = None
        self.initialize()

    def initialize(self) -> None:
        """Initialize the backend instance."""
        self.llm = self.init_llm_model()

    @abstractmethod
    def init_llm_model(self) -> Any:
        """Initialize the backend used by the template.

        Returns:
            Any: The initialized backend instance.
        """

    @abstractmethod
    def build_backend_payload(
        self, llm_conversation: LLMConversationPacket, container: DataContainer | None = None
    ) -> Any:
        """Build the backend payload.

        Args:
            llm_conversation (LLMConversationPacket): Conversation packet to convert.
            container (DataContainer | None): Optional container holding shared context.

        Returns:
            Any: Backend-specific payload.
        """

    @abstractmethod
    def invoke_backend(self, payload: Any, llm_conversation: LLMConversationPacket) -> Any:
        """Invoke the backend.

        Args:
            payload (Any): Backend-specific payload.
            llm_conversation (LLMConversationPacket): Conversation packet being processed.

        Returns:
            Any: Backend-specific response object.
        """

    @abstractmethod
    def update_packet_from_response(self, llm_conversation: LLMConversationPacket, response: Any) -> None:
        """Update a packet from a backend response.

        Args:
            llm_conversation (LLMConversationPacket): Conversation packet to update.
            response (Any): Backend-specific response object.
        """

    def execute(self, container: DataContainer) -> DataContainer:
        """Process all conversation packets in a container.

        Args:
            container (DataContainer): Input container.

        Returns:
            DataContainer: Updated container.
        """
        if not container.llm_conversations:
            self.logger.debug("Container has no llm conversations to process. Returning.")
            return container

        for llm_conversation in container.llm_conversations:
            self.process_llm_packet(llm_conversation=llm_conversation, container=container)

        return container

    @staticmethod
    def build_system_message(llm_conversation: LLMConversationPacket) -> dict[str, Any] | None:
        """Build a single system message from prompt and context data.

        Args:
            llm_conversation (LLMConversationPacket): Conversation packet to read.

        Returns:
            dict[str, Any] | None: Combined system message when available.
        """
        system_parts: list[str] = []

        if llm_conversation.system_prompt:
            system_parts.append(llm_conversation.system_prompt)

        if llm_conversation.contexts:
            context_lines: list[str] = [
                LLMTemplateBase.format_context_item(context) for context in llm_conversation.contexts
            ]
            context_text = "\n\n".join(context_lines)
            system_parts.append(f"Use the following context:\n{context_text}")

        if not system_parts:
            return None

        return build_chat_message(LLMChatKeys.system_value, "\n\n".join(system_parts))

    @staticmethod
    def format_context_item(context: LLMContextItem) -> str:
        """Format one context item.

        Args:
            context (LLMContextItem): Context item to format.

        Returns:
            str: Formatted context text.
        """
        header = f"[{context.category}]"
        if context.source:
            header = f"{header} {context.source}"
        return f"{header}\n{context.content}"

    def build_history_messages(self, llm_conversation: LLMConversationPacket) -> list[dict[str, Any]]:
        """Build messages from packet history.

        Args:
            llm_conversation (LLMConversationPacket): Conversation packet to read.

        Returns:
            list[dict[str, Any]]: History messages.
        """
        return [self.build_message_dict(message) for message in llm_conversation.messages]

    @staticmethod
    def build_message_dict(message: LLMMessage) -> dict[str, Any]:
        """Convert an `LLMMessage` into a backend message dictionary.

        Args:
            message (LLMMessage): Normalized message to convert.

        Returns:
            dict[str, Any]: Backend message dictionary.
        """
        msg = build_chat_message(message.role, message.content)
        if message.name:
            msg[LLMChatKeys.name] = message.name
        return msg

    @staticmethod
    def build_tool_messages(llm_conversation: LLMConversationPacket) -> list[dict[str, Any]]:
        """Build messages from tool results.

        Args:
            llm_conversation (LLMConversationPacket): Conversation packet to read.

        Returns:
            list[dict[str, Any]]: Tool result messages.
        """
        tool_messages: list[dict[str, Any]] = []
        for tool_result in llm_conversation.tool_results:
            message = build_chat_message(LLMChatKeys.tool_value, tool_result.content)
            if tool_result.tool_call_id:
                message[LLMChatKeys.tool_call_id] = tool_result.tool_call_id
            elif tool_result.name:
                message[LLMChatKeys.name] = tool_result.name
            tool_messages.append(message)
        return tool_messages

    @staticmethod
    def should_append_prompt_message(llm_conversation: LLMConversationPacket) -> bool:
        """Return whether the current prompt should be appended.

        Args:
            llm_conversation (LLMConversationPacket): Conversation packet to inspect.

        Returns:
            bool: Whether to append the current prompt.
        """
        if llm_conversation.content is None:
            return False

        if not llm_conversation.messages:
            return True

        last_message = llm_conversation.messages[-1]
        return not (last_message.role == LLMChatKeys.user_value and last_message.content == llm_conversation.content)

    def build_user_message(self, llm_conversation: LLMConversationPacket) -> dict[str, Any] | None:
        """Build the current user message.

        Args:
            llm_conversation (LLMConversationPacket): Conversation packet to read.

        Returns:
            dict[str, Any] | None: User message when needed.
        """
        if not self.should_append_prompt_message(llm_conversation):
            return None
        return build_chat_message(LLMChatKeys.user_value, llm_conversation.content)

    def build_current_turn_messages(
        self, llm_conversation: LLMConversationPacket, container: DataContainer | None = None
    ) -> list[dict[str, Any]]:
        """Build the current-turn messages for a packet.

        Args:
            llm_conversation (LLMConversationPacket): Conversation packet to read.
            container (DataContainer | None): Optional container holding shared context.

        Returns:
            list[dict[str, Any]]: Messages representing the current turn.
        """
        _ = container
        user_message = self.build_user_message(llm_conversation)
        if user_message is None:
            return []
        return [user_message]

    def build_non_system_messages(
        self, llm_conversation: LLMConversationPacket, container: DataContainer | None = None
    ) -> list[dict[str, Any]]:
        """Build all non-system messages for a backend request.

        Args:
            llm_conversation (LLMConversationPacket): Conversation packet to convert.
            container (DataContainer | None): Optional container holding shared context.

        Returns:
            list[dict[str, Any]]: Non-system messages for the backend request.
        """
        messages = self.build_history_messages(llm_conversation)
        messages.extend(self.build_tool_messages(llm_conversation))
        messages.extend(self.build_current_turn_messages(llm_conversation, container))
        return messages

    def build_messages(
        self, llm_conversation: LLMConversationPacket, container: DataContainer | None = None
    ) -> list[dict[str, Any]]:
        """Build the backend message list.

        Args:
            llm_conversation (LLMConversationPacket): Conversation packet to convert.
            container (DataContainer | None): Optional container holding shared context.

        Returns:
            list[dict[str, Any]]: Backend message list.
        """
        messages: list[dict[str, Any]] = []
        system_message = self.build_system_message(llm_conversation)
        if system_message:
            messages.append(system_message)
        messages.extend(self.build_non_system_messages(llm_conversation, container))
        return messages

    def split_reasoning_response(self, response_text: str | None) -> tuple[str | None, str | None]:
        """Split reasoning content and final response from raw text.

        Args:
            response_text (str | None): Raw model response text.

        Returns:
            tuple[str | None, str | None]: Extracted reasoning and final response.
        """
        if not response_text:
            return None, response_text

        start_tag = self.attributes.reasoning_start_tag
        end_tag = self.attributes.reasoning_end_tag
        if not start_tag or not end_tag:
            return None, response_text

        start_idx = response_text.find(start_tag)
        if start_idx < 0:
            return None, response_text

        content_start = start_idx + len(start_tag)
        end_idx = response_text.find(end_tag, content_start)
        if end_idx < 0:
            return None, response_text

        reasoning = response_text[content_start:end_idx].strip() or None
        response = response_text[end_idx + len(end_tag) :].strip() or None
        return reasoning, response

    def extract_reasoning(self, llm_conversation: LLMConversationPacket) -> None:
        """Extract reasoning and the final response from tagged output.

        Args:
            llm_conversation (LLMConversationPacket): Conversation packet to update.
        """
        if llm_conversation.reasoning is not None or not llm_conversation.response:
            return

        reasoning, response = self.split_reasoning_response(llm_conversation.response)
        if reasoning is None:
            return

        llm_conversation.reasoning = reasoning
        llm_conversation.response = response

    def cleanup_response_text(self, response_text: str | None) -> str | None:
        """Clean the final assistant response text.

        Args:
            response_text (str | None): Response text to clean.

        Returns:
            str | None: Cleaned response text.
        """
        if not response_text or not self.attributes.cleanup_response:
            return response_text

        cleaned_text = response_text
        start_tag = self.attributes.reasoning_start_tag
        end_tag = self.attributes.reasoning_end_tag
        if start_tag and end_tag:
            reasoning_pattern = re.compile(rf"{re.escape(start_tag)}.*?{re.escape(end_tag)}", flags=re.DOTALL)
            cleaned_text = reasoning_pattern.sub("", cleaned_text)

        if start_tag:
            cleaned_text = cleaned_text.replace(start_tag, "")
        if end_tag:
            cleaned_text = cleaned_text.replace(end_tag, "")

        return postprocess_text(cleaned_text) or None

    def update_structured_output(self, llm_conversation: LLMConversationPacket) -> None:
        """Parse and store structured output when configured.

        Args:
            llm_conversation (LLMConversationPacket): Conversation packet to update.
        """
        if llm_conversation.structured_output is not None:
            return

        structured_output = self.parse_structured_output(llm_conversation.response)
        if structured_output is not None:
            llm_conversation.structured_output = structured_output

    def postprocess_llm_conversation(self, llm_conversation: LLMConversationPacket) -> None:
        """Finalize packet output fields after backend execution.

        Args:
            llm_conversation (LLMConversationPacket): Conversation packet to update.
        """
        self.extract_reasoning(llm_conversation)
        llm_conversation.response = self.cleanup_response_text(llm_conversation.response)
        self.update_structured_output(llm_conversation)

    def parse_structured_output(self, response_text: str | None) -> dict[str, Any] | list[Any] | None:
        """Parse structured output from response text.

        Args:
            response_text (str | None): Response text to parse.

        Returns:
            dict[str, Any] | list[Any] | None: Parsed structured output, if valid.
        """
        if not self.attributes.completion_args.response_format.is_structured() or not response_text:
            return None

        try:
            parsed = json.loads(response_text)
            if isinstance(parsed, (dict, list)):
                return parsed
        except (json.JSONDecodeError, TypeError):
            self.logger.warning(f"Failed to parse structured output as JSON: {response_text[:200]}")
        return None

    def process_llm_packet(
        self, llm_conversation: LLMConversationPacket, container: DataContainer | None = None
    ) -> None:
        """Process a conversation packet through the configured backend.

        Args:
            llm_conversation (LLMConversationPacket): Conversation packet to process.
            container (DataContainer | None): Optional container holding shared context.
        """
        if llm_conversation.termination is not None and llm_conversation.termination.finish_reason == "cache_hit":
            self.logger.debug(
                "Skipping backend invocation because the packet was already resolved from semantic cache."
            )
            return

        payload = self.build_backend_payload(llm_conversation, container=container)
        response = self.invoke_backend(payload=payload, llm_conversation=llm_conversation)
        self.update_packet_from_response(llm_conversation=llm_conversation, response=response)
        self.postprocess_llm_conversation(llm_conversation)

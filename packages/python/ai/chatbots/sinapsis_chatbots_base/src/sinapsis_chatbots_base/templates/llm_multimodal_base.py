from __future__ import annotations

from abc import abstractmethod
from typing import Any

from sinapsis.data_transport import DataContainer, LLMConversationPacket

from sinapsis_chatbots_base.helpers.llm_conversation import build_chat_message
from sinapsis_chatbots_base.helpers.llm_keys import LLMChatKeys
from sinapsis_chatbots_base.templates.llm_template_base import LLMTemplateBase


class LLMMultimodalTemplateBase(LLMTemplateBase):
    """Thin base for LLM templates that enrich the current user turn with multimodal content."""

    @abstractmethod
    def extract_additional_content(self, container: DataContainer) -> list[dict[str, Any]]:
        """Extract additional multimodal content from a container.

        Args:
            container (DataContainer): Container holding shared multimodal packets.

        Returns:
            list[dict[str, Any]]: Provider-compatible content blocks.
        """

    @staticmethod
    @abstractmethod
    def build_text_content_part(text: str) -> dict[str, Any]:
        """Build the provider-specific text block for multimodal user content.

        Args:
            text (str): Prompt text to append to the multimodal content.

        Returns:
            dict[str, Any]: Provider-compatible text content block.
        """

    def build_current_turn_messages(
        self, llm_conversation: LLMConversationPacket, container: DataContainer | None = None
    ) -> list[dict[str, Any]]:
        """Build the multimodal current turn for a conversation packet.

        Args:
            llm_conversation (LLMConversationPacket): Conversation packet to convert.
            container (DataContainer | None): Optional container holding shared multimodal packets.

        Returns:
            list[dict[str, Any]]: Provider-compatible current-turn messages.
        """
        if container is None:
            return super().build_current_turn_messages(llm_conversation, container)

        user_content = self.extract_additional_content(container)
        if llm_conversation.content is not None and self.should_append_prompt_message(llm_conversation):
            user_content.append(self.build_text_content_part(str(llm_conversation.content)))

        if not user_content:
            return []

        return [build_chat_message(LLMChatKeys.user_value, user_content)]

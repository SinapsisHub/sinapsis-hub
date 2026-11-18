from pathlib import Path
from typing import Literal

from sinapsis.data_transport import DataContainer, LLMConversationPacket, LLMIdentity

from sinapsis_chatbots_base.templates.llm_conversation_input import LLMConversationInput, LLMConversationInputAttributes


class TextToLLMConversationAttributes(LLMConversationInputAttributes):
    """Attributes for the `TextPacketsToLLMConversation` template.

    Attributes:
        mode (Literal["single", "per_text_packet"]):
            Conversion strategy. Use ``single`` to merge all text packets into
            one conversation prompt or ``per_text_packet`` to create one
            conversation per text packet.
        separator (str):
            String used to join text packet contents when ``mode="single"``.
        prompt_prefix (str):
            Optional text prepended to the generated prompt.
        prompt_suffix (str):
            Optional text appended to the generated prompt.
    """

    mode: Literal["single", "per_text_packet"] = "single"
    separator: str = "\n\n--- PAGE ---\n\n"
    prompt: str | Path = ""
    prompt_prefix: str = ""
    prompt_suffix: str = ""


class TextToLLMConversation(LLMConversationInput):
    """Convert TextPackets into LLMConversationPackets.

    This template is useful when upstream templates generate TextPackets and
    downstream LLM templates expect LLMConversationPackets.

    Depending on the configured mode, the template can either merge all text
    packets into a single conversation prompt or create one conversation
    packet per text packet.

    Usage example:

    agent:
      name: my_test_agent
    templates
    - template_name: InputTemplate
      class_name: InputTemplate
      attributes: {}
    - template_name: TextToLLMConversation
      class_name: TextToLLMConversation
      template_input: InputTemplate
      attributes:
        mode: single
        prompt_prefix: 'text prepended to the generated prompt'
        prompt_suffix: 'text appended to the generated prompt'
    """

    AttributesBaseModel = TextToLLMConversationAttributes
    attributes: TextToLLMConversationAttributes

    def _make_identity(self) -> LLMIdentity | None:
        """Create an identity object from configured attributes.

        Returns:
            LLMIdentity | None:
                Identity metadata if any identity-related attributes were
                provided. Otherwise, returns None.
        """
        if not any(
            (self.attributes.user_id, self.attributes.session_id, self.attributes.run_id, self.attributes.agent_id)
        ):
            return None

        return LLMIdentity(
            user_id=self.attributes.user_id,
            session_id=self.attributes.session_id,
            run_id=self.attributes.run_id,
            agent_id=self.attributes.agent_id,
        )

    @staticmethod
    def _get_texts(container: DataContainer) -> list[str]:
        """Extract non-empty text contents from a data container.

        Args:
            container (DataContainer):
                Container containing TextPackets.

        Returns:
            list[str]:
                List of stripped text contents from all non-empty TextPackets.
        """
        return [str(text_packet.content).strip() for text_packet in container.texts if str(text_packet.content).strip()]

    def _build_prompt(self, text: str) -> str:
        """Build the final prompt content.

        The generated prompt consists of the configured prefix, the provided
        text content, and the configured suffix.

        Args:
            text (str):
                Base text content.

        Returns:
            str:
                Final prompt text.
        """
        return f"{self.attributes.prompt_prefix}{text}{self.attributes.prompt_suffix}"

    def _make_conversation(
        self, text: str, system_prompt: str | None, identity: LLMIdentity | None
    ) -> LLMConversationPacket:
        """Create an LLM conversation packet.

        Args:
            text (str):
                Text content to include in the conversation prompt.
            system_prompt (str | None):
                System prompt to attach to the conversation.
            identity (LLMIdentity | None):
                Identity metadata associated with the conversation.

        Returns:
            LLMConversationPacket:
                Generated conversation packet.
        """
        return LLMConversationPacket(content=self._build_prompt(text), system_prompt=system_prompt, identity=identity)

    def _append_single_conversation(
        self, container: DataContainer, texts: list[str], system_prompt: str | None, identity: LLMIdentity | None
    ) -> None:
        """Append a single conversation containing all text packets.

        Args:
            container (DataContainer):
                Container to update.
            texts (list[str]):
                Text contents to merge into a single prompt.
            system_prompt (str | None):
                System prompt associated with the conversation.
            identity (LLMIdentity | None):
                Identity metadata associated with the conversation.
        """
        merged_text = self.attributes.separator.join(texts)
        conversation = self._make_conversation(merged_text, system_prompt, identity)
        container.llm_conversations.append(conversation)

    def _append_conversation_per_text(
        self, container: DataContainer, texts: list[str], system_prompt: str | None, identity: LLMIdentity | None
    ) -> None:
        """Append one conversation per text entry.

        Args:
            container (DataContainer):
                Container to update.
            texts (list[str]):
                Text contents used to create conversation packets.
            system_prompt (str | None):
                System prompt associated with each conversation.
            identity (LLMIdentity | None):
                Identity metadata associated with each conversation.
        """
        for text in texts:
            conversation = self._make_conversation(text, system_prompt, identity)
            container.llm_conversations.append(conversation)

    def execute(self, container: DataContainer) -> DataContainer:
        """Convert TextPackets into LLMConversationPackets.

        Depending on the configured mode, either a single conversation packet
        is created from all text packets or one conversation packet is created
        for each text packet.

        Args:
            container (DataContainer):
                Container containing TextPackets.

        Returns:
            DataContainer:
                Updated container with generated LLMConversationPackets.
        """
        texts = self._get_texts(container)

        if not texts:
            self.logger.warning("No non-empty TextPackets found.")
            return container

        system_prompt = self._resolve_prompt_value(self.attributes.system_prompt)
        identity = self._make_identity()

        if self.attributes.mode == "per_text_packet":
            self._append_conversation_per_text(container, texts, system_prompt, identity)
        else:
            self._append_single_conversation(container, texts, system_prompt, identity)

        return container

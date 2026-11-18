import abc
from typing import Any

from sinapsis.data_transport import DataContainer, LLMContextItem, LLMConversationPacket
from sinapsis.template import OutputTypes, Template, TemplateAttributes, UIPropertiesMetadata

from sinapsis_chatbots_base.helpers.tags import Tags


class QueryContextualize(Template, abc.ABC):
    """Base class for keyword-driven contextualization on conversation packets."""

    class AttributesBaseModel(TemplateAttributes):
        """Attributes for contextualization.

        Attributes:
            keywords (list[str]): A list of keywords to be used for retrieving context.
        """

        keywords: list[str]

    UIProperties = UIPropertiesMetadata(
        category="Chatbots",
        output_type=OutputTypes.TEXT,
        tags=[Tags.CHATBOTS, Tags.CONTEXT, Tags.QUERY, Tags.QUERY_CONTEXTUALIZATION],
    )
    attributes: AttributesBaseModel

    @abc.abstractmethod
    def retrieve_context_items(self, keyword: str, context_data: dict | Any) -> list[LLMContextItem]:
        """Return context items related to one keyword.

        Subclasses are responsible for translating provider- or source-specific
        context data into normalized `LLMContextItem` objects.

        Args:
            keyword (str): Keyword that triggered contextualization.
            context_data (dict | Any): Source-specific context storage.

        Returns:
            list[LLMContextItem]: Normalized context items for the matched keyword.
        """

    @staticmethod
    def should_contextualize(keyword: str, prompt_text: str) -> bool:
        """Return whether a keyword should contextualize the current prompt.

        Args:
            keyword (str): Keyword to search for.
            prompt_text (str): Prompt text to inspect.

        Returns:
            bool: `True` when the keyword is present in the prompt.
        """
        return keyword.lower() in prompt_text.lower()

    @staticmethod
    def _context_signature(context_item: LLMContextItem) -> tuple[str, str, str | None]:
        """Build a stable signature for one context item.

        Args:
            context_item (LLMContextItem): Context item to normalize.

        Returns:
            tuple[str, str, str | None]: Comparable context signature.
        """
        return context_item.category, context_item.content, context_item.source

    def append_contexts(self, llm_conversation: LLMConversationPacket, context_items: list[LLMContextItem]) -> None:
        """Append new context items while avoiding duplicates.

        Args:
            llm_conversation (LLMConversationPacket): Conversation packet to update.
            context_items (list[LLMContextItem]): Context items to append.
        """
        existing_signatures = {self._context_signature(context_item) for context_item in llm_conversation.contexts}
        for context_item in context_items:
            signature = self._context_signature(context_item)
            if signature in existing_signatures:
                continue
            llm_conversation.contexts.append(context_item)
            existing_signatures.add(signature)

    def load_context(self, container: DataContainer) -> None:
        """Load contextual document items into conversation packets.

        Args:
            container (DataContainer): Container holding conversation packets and context data.
        """
        for llm_conversation in container.llm_conversations:
            if llm_conversation.content is None:
                continue

            prompt_text = str(llm_conversation.content)
            for keyword in self.attributes.keywords:
                if not self.should_contextualize(keyword, prompt_text):
                    continue
                context_items = self.retrieve_context_items(keyword, container.generic_data)
                self.append_contexts(llm_conversation, context_items)

    def execute(self, container: DataContainer) -> DataContainer:
        """Execute contextualization on conversation packets.

        Args:
            container (DataContainer): Container holding conversation packets.

        Returns:
            DataContainer: Updated container with appended packet contexts.
        """
        if not container.llm_conversations:
            self.logger.info("No llm conversations to process.")
            return container
        self.load_context(container)

        return container

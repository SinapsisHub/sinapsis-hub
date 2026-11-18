from typing import Any

from sinapsis.data_transport import LLMContextItem

from sinapsis_chatbots_base.templates.query_contextualize import QueryContextualize


class QueryContextualizeFromFile(QueryContextualize):
    """Contextualize conversation packets from file-derived data in `generic_data`.

    This template reads file-derived entries from `container.generic_data`, matches
    them against configured keywords, and appends normalized `LLMContextItem`
    objects to `LLMConversationPacket.contexts` using the `document` category.

    Usage example:

    agent:
      name: my_test_agent
    templates:
      - template_name: InputTemplate
        class_name: InputTemplate
        attributes: {}
      - template_name: QueryContextualizeFromFile
        class_name: QueryContextualizeFromFile
        template_input: InputTemplate
        attributes:
          keywords:
            - "pricing"
            - "refund"
          generic_keys:
            - "refund_policy_pdf"
            - "pricing_guide_pdf"
    """

    class AttributesBaseModel(QueryContextualize.AttributesBaseModel):
        """Attributes for file-backed contextualization.

        Attributes:
            keywords (list[str]): Keywords used to trigger contextualization.
            generic_keys (list[str]): Keys searched in `container.generic_data`.
        """

        generic_keys: list[str]

    attributes: AttributesBaseModel

    @staticmethod
    def _extract_text_content(entry: Any) -> str | None:
        """Extract text content from one generic-data entry.

        Args:
            entry (Any): Generic-data entry to inspect.

        Returns:
            str | None: Extracted text content, when available.
        """
        if isinstance(entry, str):
            return entry or None

        if isinstance(entry, dict):
            for key in ("page_content", "content", "text"):
                value = entry.get(key)
                if isinstance(value, str) and value:
                    return value
            return None

        for attr_name in ("page_content", "content", "text"):
            value = getattr(entry, attr_name, None)
            if isinstance(value, str) and value:
                return value

        return None

    def _build_context_items(self, keyword: str, generic_key: str, generic_value: Any) -> list[LLMContextItem]:
        """Build normalized packet contexts from one generic-data value.

        Args:
            keyword (str): Keyword that triggered contextualization.
            generic_key (str): Matched generic-data key.
            generic_value (Any): Value stored under the matched key.

        Returns:
            list[LLMContextItem]: Normalized `document` context items.
        """
        raw_entries = generic_value if isinstance(generic_value, list) else [generic_value]
        context_items: list[LLMContextItem] = []
        for index, entry in enumerate(raw_entries):
            content = self._extract_text_content(entry)
            if not content:
                continue

            metadata: dict[str, Any] = {"keyword": keyword, "generic_key": generic_key}
            if len(raw_entries) > 1:
                metadata["entry_index"] = index

            context_items.append(
                LLMContextItem(category="document", content=content, source=generic_key, metadata=metadata)
            )

        return context_items

    def retrieve_context_items(self, keyword: str, context_data: dict | Any) -> list[LLMContextItem]:
        """Retrieve normalized context items for one keyword.

        Args:
            keyword (str): Keyword that triggered contextualization.
            context_data (dict | Any): Generic-data dictionary holding file-derived content.

        Returns:
            list[LLMContextItem]: Packet context items for the keyword.
        """
        matching_key = next((key for key in self.attributes.generic_keys if keyword.lower() in key.lower()), None)
        if matching_key is None or matching_key not in context_data:
            return []

        return self._build_context_items(keyword, matching_key, context_data[matching_key])

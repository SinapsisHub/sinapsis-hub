from pathlib import Path

from sinapsis.data_transport import DataContainer, LLMConversationPacket, LLMIdentity
from sinapsis.template import OutputTypes, Template, TemplateAttributes, UIPropertiesMetadata

from sinapsis_chatbots_base.helpers.tags import Tags


class LLMConversationInputAttributes(TemplateAttributes):
    """Attributes for the `LLMConversationInput` template.

    Attributes:
        prompt (str | Path): The main prompt text or a path to a `.txt` file containing it.
        system_prompt (str | Path | None): Optional system prompt text or a path to a `.txt` file containing it.
    """

    prompt: str | Path
    system_prompt: str | Path | None = None
    user_id: str | None = None
    session_id: str | None = None
    run_id: str | None = None
    agent_id: str | None = None


class LLMConversationInput(Template):
    """A template for adding an LLM conversation packet to a data container.

    This class uses the provided attributes to create an `LLMConversationPacket`
    and appends it to `container.llm_conversations`.

    Usage example:

    agent:
      name: my_test_agent
    templates:
    - template_name: InputTemplate
      class_name: InputTemplate
      attributes: {}
    - template_name: LLMConversationInput
      class_name: LLMConversationInput
      template_input: InputTemplate
      attributes:
        prompt: 'prompt to be added to the LLMConversationPacket'
        system_prompt: 'system prompt to be added to the LLMConversationPacket'

    """

    AttributesBaseModel = LLMConversationInputAttributes
    UIProperties = UIPropertiesMetadata(tags=[Tags.TEXT, Tags.TEXT_COMPLETION], output_type=OutputTypes.TEXT)
    attributes: AttributesBaseModel

    @staticmethod
    def _resolve_prompt_value(value: str | Path | None) -> str | None:
        """Return prompt text directly or load it from a `.txt` file when appropriate.

        Existing `.txt` files are treated as file paths. Literal strings that do not resolve
        to files are returned unchanged.

        Args:
            value (str | Path | None): Prompt text or file path.

        Returns:
            str | None: Resolved prompt text.

        Raises:
            ValueError: If the provided file path is invalid or not a `.txt` file.
        """
        if value is None:
            return None

        if isinstance(value, str) and not value.endswith((".txt", ".TXT")):
            return value

        candidate = value.expanduser() if isinstance(value, Path) else Path(value).expanduser()

        if not candidate.exists():
            return str(value)

        resolved_path = candidate.resolve()
        if not resolved_path.is_file():
            raise ValueError(f"Prompt path `{resolved_path}` must point to a file.")

        if resolved_path.suffix.lower() != ".txt":
            raise ValueError(f"Prompt path `{resolved_path}` must be a `.txt` file.")

        return resolved_path.read_text(encoding="utf-8")

    def execute(self, container: DataContainer) -> DataContainer:
        """Append an LLM conversation packet to the provided data container.

        Args:
            container (DataContainer): The container to which the conversation packet will be added.

        Returns:
            DataContainer: The updated container with the new conversation packet appended.
        """
        prompt = self._resolve_prompt_value(self.attributes.prompt)
        system_prompt = self._resolve_prompt_value(self.attributes.system_prompt)
        identity = None
        if any((self.attributes.user_id, self.attributes.session_id, self.attributes.run_id, self.attributes.agent_id)):
            identity = LLMIdentity(
                user_id=self.attributes.user_id,
                session_id=self.attributes.session_id,
                run_id=self.attributes.run_id,
                agent_id=self.attributes.agent_id,
            )

        container.llm_conversations.append(
            LLMConversationPacket(content=prompt, system_prompt=system_prompt, identity=identity)
        )
        return container

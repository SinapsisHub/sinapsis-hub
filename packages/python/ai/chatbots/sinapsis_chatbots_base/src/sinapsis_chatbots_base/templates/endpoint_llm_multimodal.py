from typing import Any

from sinapsis.data_transport import DataContainer
from sinapsis.template import OutputTypes, UIPropertiesMetadata
from typing_extensions import override

from sinapsis_chatbots_base.helpers.llm_conversation import image_array_to_data_uri
from sinapsis_chatbots_base.helpers.tags import Tags
from sinapsis_chatbots_base.templates.endpoint_llm_completion import EndpointLLMCompletion
from sinapsis_chatbots_base.templates.llm_multimodal_base import LLMMultimodalTemplateBase


class EndpointLLMMultiModal(LLMMultimodalTemplateBase, EndpointLLMCompletion):
    """Template for image + text completion using OpenAI-compatible endpoints.

    Usage example:

    agent:
      name: my_test_agent
    templates:
      - template_name: InputTemplate
        class_name: InputTemplate
        attributes: {}
      - template_name: EndpointLLMMultiModal
        class_name: EndpointLLMMultiModal
        template_input: LLMConversationInput
        attributes:
          init_args:
            base_url: "http://127.0.0.1:8000/v1"
            llm_model_name: "Qwen/Qwen2.5-VL-3B-Instruct"
          completion_args:
            max_tokens: 1024
    """

    UIProperties = UIPropertiesMetadata(
        category="Chatbots",
        output_type=OutputTypes.TEXT,
        tags=[Tags.CHATBOTS, Tags.LLM, Tags.TEXT_COMPLETION, Tags.TEXT, Tags.MULTIMODAL, Tags.IMAGE_TO_TEXT],
    )

    AttributesBaseModel = EndpointLLMCompletion.AttributesBaseModel
    attributes: AttributesBaseModel

    @override
    def extract_additional_content(self, container: DataContainer) -> list[dict[str, Any]]:
        """Extract image packets as OpenAI-compatible image blocks.

        Args:
            container (DataContainer): Container holding image packets.

        Returns:
            list[dict[str, Any]]: Encoded image content blocks.
        """
        return [
            {"type": "image_url", "image_url": {"url": image_array_to_data_uri(image_packet.content)}}
            for image_packet in container.images
        ]

    @staticmethod
    def build_text_content_part(text: str) -> dict[str, str]:
        """Build an OpenAI-compatible text block.

        Args:
            text (str): Text content.

        Returns:
            dict[str, str]: Text content block.
        """
        return {"type": "text", "text": text}

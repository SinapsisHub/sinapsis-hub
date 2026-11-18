from typing import Any

from openai import AsyncOpenAI, OpenAI
from pydantic import Field
from sinapsis.data_transport import DataContainer, LLMConversationPacket, LLMProviderInfo, LLMTermination, LLMUsage
from sinapsis.template import OutputTypes, UIPropertiesMetadata

from sinapsis_chatbots_base.helpers.env_vars import LLM_API_KEY
from sinapsis_chatbots_base.helpers.performance import build_client_side_performance, measure_call_latency
from sinapsis_chatbots_base.helpers.schemas import (
    JSON_OBJECT_RESPONSE_FORMAT,
    JSON_SCHEMA_RESPONSE_FORMAT,
    LLMCompletionArgs,
    LLMInitArgs,
)
from sinapsis_chatbots_base.helpers.tags import Tags
from sinapsis_chatbots_base.templates.llm_template_base import LLMTemplateBase, LLMTemplateBaseAttributes


class EndpointLLMInitArgs(LLMInitArgs):
    """Initialization arguments for a generic endpoint-backed LLM.

    Attributes:
        llm_model_name (str | None): Explicit model name. When `None`, the endpoint default is used.
        base_url (str): Base URL for the OpenAI-compatible endpoint.
        timeout (float): Request timeout in seconds.
        default_headers (dict[str, str]): Additional headers to include in requests.
        api_key (str | None): Optional API key override. Falls back to `LLM_API_KEY`.
    """

    llm_model_name: str | None = None
    base_url: str
    timeout: float = 120.0
    default_headers: dict[str, str] = Field(default_factory=dict)
    api_key: str | None = None


class EndpointLLMCompletionArgs(LLMCompletionArgs):
    """Completion arguments for generic endpoint-backed LLM calls.

    Attributes:
        max_tokens (int): Maximum number of output tokens.
        stop (str | list[str] | None): Stop sequences.
        seed (int | None): Optional seed for reproducibility.
        presence_penalty (float | None): Presence penalty.
        frequency_penalty (float | None): Frequency penalty.
        additional_args (dict[str, Any]): Extra provider-specific request arguments.
    """

    max_tokens: int = 4096
    stop: str | list[str] | None = None
    seed: int | None = None
    presence_penalty: float | None = None
    frequency_penalty: float | None = None
    additional_args: dict[str, Any] = Field(default_factory=dict)


class EndpointLLMCompletionAttributes(LLMTemplateBaseAttributes):
    """Attributes for `EndpointLLMCompletion`.

    Attributes:
        init_args (EndpointLLMInitArgs): Endpoint connection configuration.
        completion_args (EndpointLLMCompletionArgs): Generation and structured-output arguments.
    """

    init_args: EndpointLLMInitArgs
    completion_args: EndpointLLMCompletionArgs = Field(default_factory=EndpointLLMCompletionArgs)


class EndpointLLMCompletion(LLMTemplateBase):
    """Template for OpenAI-compatible chat completion endpoints.

    Usage example:

    agent:
      name: my_test_agent
    templates:
      - template_name: InputTemplate
        class_name: InputTemplate
        attributes: {}
      - template_name: EndpointLLMCompletion
        class_name: EndpointLLMCompletion
        template_input: InputTemplate
        attributes:
          init_args:
            base_url: "https://api.openai.com/v1"
            llm_model_name: "gpt-4o-mini"
          completion_args:
            max_tokens: 2048
    """

    UIProperties = UIPropertiesMetadata(
        category="Chatbots",
        output_type=OutputTypes.TEXT,
        tags=[Tags.CHATBOTS, Tags.CONTEXT, Tags.LLM, Tags.TEXT_COMPLETION, Tags.TEXT],
    )

    AttributesBaseModel = EndpointLLMCompletionAttributes
    attributes: AttributesBaseModel

    def _get_api_key(self) -> str:
        """Return the configured API key.

        Returns:
            str: API key to use for the client.
        """
        return self.attributes.init_args.api_key or LLM_API_KEY

    def init_llm_model(self) -> OpenAI | AsyncOpenAI:
        """Initialize the OpenAI-compatible client.

        Returns:
            OpenAI: Configured client instance.
        """
        init_args = self.attributes.init_args.model_dump(exclude={"llm_model_name", "api_key"})
        return OpenAI(api_key=self._get_api_key(), **init_args)

    def build_backend_payload(
        self, llm_conversation: LLMConversationPacket, container: DataContainer | None = None
    ) -> dict[str, Any]:
        """Build the request payload for the endpoint.

        Args:
            llm_conversation (LLMConversationPacket): Conversation packet to convert.
            container (DataContainer | None): Optional container holding shared context.

        Returns:
            dict[str, Any]: Chat completion payload.
        """
        messages = self.build_messages(llm_conversation, container=container)
        completion_args = self.attributes.completion_args.model_dump(
            exclude_none=True, exclude={"response_format", "additional_args"}
        )
        completion_args.update(self.attributes.completion_args.additional_args)

        response_format = self._build_response_format_payload()
        if response_format is not None:
            completion_args["response_format"] = response_format

        payload: dict[str, Any] = {"messages": messages, **completion_args}

        model_name = self.attributes.init_args.llm_model_name
        if model_name:
            payload["model"] = model_name

        return payload

    def _build_response_format_payload(self) -> dict[str, Any] | None:
        """Build the endpoint response_format payload.

        Returns:
            dict[str, Any] | None: Endpoint-compatible response format, if any.
        """
        response_format = self.attributes.completion_args.response_format
        if not response_format.is_structured():
            return None

        if response_format.has_schema():
            return {
                "type": JSON_SCHEMA_RESPONSE_FORMAT,
                "json_schema": {"name": "structured_output", "schema": response_format.to_json_schema()},
            }

        return {"type": JSON_OBJECT_RESPONSE_FORMAT}

    def invoke_backend(self, payload: Any, llm_conversation: LLMConversationPacket) -> Any:
        """Execute the endpoint request.

        Args:
            payload (Any): Client payload for the request.
            llm_conversation (LLMConversationPacket): Conversation packet being processed.

        Returns:
            Any: Raw OpenAI client response object.
        """
        self.logger.debug(f"Endpoint request payload: {payload}")
        if self.llm is None:
            raise ValueError("LLM client has not been initialized.")
        response, latency_seconds = measure_call_latency(self.llm.chat.completions.create, **payload)
        llm_conversation.performance = build_client_side_performance(
            llm_conversation.performance, latency_seconds=latency_seconds
        )
        return response

    def update_packet_from_response(self, llm_conversation: LLMConversationPacket, response: Any) -> None:
        """Update the packet from the endpoint response.

        Args:
            llm_conversation (LLMConversationPacket): Conversation packet to update.
            response (Any): Raw OpenAI client response object.
        """
        if not response.choices:
            return

        choice = response.choices[0]
        message = choice.message
        content = message.content
        reasoning = getattr(message, "reasoning", None)
        completion_token_details = (
            getattr(response.usage, "completion_tokens_details", None) if response.usage else None
        )
        output_tokens = getattr(response.usage, "completion_tokens", None) if response.usage else None
        reasoning_tokens = getattr(response.usage, "reasoning_tokens", None) if response.usage else None
        if reasoning_tokens is None and completion_token_details is not None:
            reasoning_tokens = getattr(completion_token_details, "reasoning_tokens", None)

        llm_conversation.response = content or None
        llm_conversation.reasoning = reasoning
        llm_conversation.provider_info = LLMProviderInfo(
            provider="openai_compatible_endpoint", model_name=response.model or self.attributes.init_args.llm_model_name
        )
        llm_conversation.termination = LLMTermination(
            finish_reason=choice.finish_reason, stop_reason=getattr(choice, "stop_reason", None)
        )

        if response.usage is not None:
            llm_conversation.usage = LLMUsage(
                input_tokens=getattr(response.usage, "prompt_tokens", None),
                output_tokens=output_tokens,
                reasoning_tokens=reasoning_tokens,
                total_tokens=getattr(response.usage, "total_tokens", None),
            )

        llm_conversation.performance = build_client_side_performance(
            llm_conversation.performance, output_tokens=output_tokens
        )

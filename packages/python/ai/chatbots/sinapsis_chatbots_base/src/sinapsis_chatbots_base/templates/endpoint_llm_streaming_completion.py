from collections.abc import AsyncGenerator
from time import perf_counter
from typing import Any

from openai import AsyncOpenAI
from sinapsis.data_transport import DataContainer, LLMConversationPacket, LLMProviderInfo, LLMTermination, LLMUsage
from sinapsis.template import OutputTypes, UIPropertiesMetadata
from typing_extensions import override

from sinapsis_chatbots_base.helpers.performance import build_client_side_performance
from sinapsis_chatbots_base.helpers.tags import Tags
from sinapsis_chatbots_base.templates.endpoint_llm_completion import EndpointLLMCompletion
from sinapsis_chatbots_base.templates.llm_streaming_base import LLMStreamingTemplateBase

_STREAM_START_TIME_KEY = "_endpoint_stream_started_at"


class EndpointLLMStreamingCompletion(LLMStreamingTemplateBase, EndpointLLMCompletion):
    """Streaming template for OpenAI-compatible chat completion endpoints.

    Usage example:

    agent:
      name: my_test_agent
    templates:
      - template_name: InputTemplate
        class_name: InputTemplate
        attributes: {}
      - template_name: EndpointLLMStreamingCompletion
        class_name: EndpointLLMStreamingCompletion
        template_input: InputTemplate
        attributes:
          init_args:
            base_url: "http://127.0.0.1:8000/v1"
            llm_model_name: "Qwen/Qwen3-4B"
          completion_args:
            max_tokens: 1024
            temperature: 0.7
    """

    UIProperties = UIPropertiesMetadata(
        category="Chatbots",
        output_type=OutputTypes.TEXT,
        tags=[Tags.CHATBOTS, Tags.CONTEXT, Tags.LLM, Tags.TEXT_COMPLETION, Tags.TEXT, Tags.STREAMING],
    )

    AttributesBaseModel = EndpointLLMCompletion.AttributesBaseModel
    attributes: AttributesBaseModel
    IS_STREAMING = True

    def init_llm_model(self) -> AsyncOpenAI:
        """Initialize the async OpenAI-compatible client.

        Returns:
            AsyncOpenAI: Configured async client instance.
        """
        init_args = self.attributes.init_args.model_dump(exclude={"llm_model_name", "api_key"})
        return AsyncOpenAI(api_key=self._get_api_key(), **init_args)

    @override
    def invoke_backend(self, payload: Any, llm_conversation: LLMConversationPacket) -> Any:
        """Streaming templates do not use the synchronous backend path.

        Args:
            payload (Any): Unused synchronous payload.
            llm_conversation (LLMConversationPacket): Unused conversation packet.

        Returns:
            Any: This method does not return a value.

        Raises:
            NotImplementedError: Always raised for the sync path.
        """
        _ = payload
        _ = llm_conversation
        raise NotImplementedError("Use `async_execute` for EndpointLLMStreamingCompletion.")

    def build_backend_payload(
        self, llm_conversation: LLMConversationPacket, container: DataContainer | None = None
    ) -> dict[str, Any]:
        """Build the request payload for the streaming endpoint.

        Args:
            llm_conversation (LLMConversationPacket): Conversation packet to convert.
            container (DataContainer | None): Optional container holding shared context.

        Returns:
            dict[str, Any]: Streaming chat completion payload.
        """
        payload = super().build_backend_payload(llm_conversation, container)
        payload["stream"] = True
        stream_options = payload.get("stream_options")
        if stream_options is None:
            payload["stream_options"] = {"include_usage": True}
        elif isinstance(stream_options, dict) and "include_usage" not in stream_options:
            payload["stream_options"] = {**stream_options, "include_usage": True}
        return payload

    async def stream_backend(self, payload: Any, llm_conversation: LLMConversationPacket) -> AsyncGenerator[Any, None]:
        """Yield raw stream events from the async OpenAI-compatible client.

        Args:
            payload (Any): Client payload for the request.
            llm_conversation (LLMConversationPacket): Conversation packet being processed.

        Yields:
            Any: Raw OpenAI-compatible stream events.
        """
        if self.llm is None:
            raise ValueError("LLM client has not been initialized.")
        request_payload = dict(payload)
        request_payload["stream"] = True
        llm_conversation.generic_data[_STREAM_START_TIME_KEY] = perf_counter()
        stream = await self.llm.chat.completions.create(**request_payload)
        async for event in stream:
            yield event

    @staticmethod
    def _extract_first_choice(event: Any) -> Any | None:
        """Return the first streamed choice when present.

        Args:
            event (Any): Raw streamed event.

        Returns:
            Any | None: First streamed choice when available.
        """
        choices = getattr(event, "choices", None) or []
        return choices[0] if choices else None

    @staticmethod
    def _extract_text_from_delta(delta: Any) -> str | None:
        """Extract text content from a streamed delta block.

        Args:
            delta (Any): Provider delta object.

        Returns:
            str | None: Text content extracted from the delta.
        """
        if delta is None:
            return None

        content = getattr(delta, "content", None)
        if content is None:
            return None

        if isinstance(content, str):
            return content or None

        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                text = getattr(item, "text", None)
                if text:
                    parts.append(str(text))
                elif isinstance(item, dict) and item.get("text"):
                    parts.append(str(item["text"]))
            return "".join(parts) or None

        return str(content)

    @staticmethod
    def _extract_reasoning_from_delta(delta: Any) -> str | None:
        """Extract provider reasoning text from a streamed delta block.

        Args:
            delta (Any): Provider delta object.

        Returns:
            str | None: Reasoning content extracted from the delta.
        """
        if delta is None:
            return None

        for attr_name in ("reasoning", "reasoning_content"):
            reasoning = getattr(delta, attr_name, None)
            if reasoning is None:
                continue

            if isinstance(reasoning, str):
                return reasoning or None

            if isinstance(reasoning, list):
                parts: list[str] = []
                for item in reasoning:
                    text = getattr(item, "text", None)
                    if text:
                        parts.append(str(text))
                    elif isinstance(item, dict) and item.get("text"):
                        parts.append(str(item["text"]))
                return "".join(parts) or None

            return str(reasoning)

        return None

    def aggregate_stream_event(self, aggregated_event: dict[str, Any] | None, event: Any) -> dict[str, Any]:
        """Aggregate stream events into one final packet state.

        Args:
            aggregated_event (dict[str, Any] | None): Aggregated stream state so far.
            event (Any): Current stream event.

        Returns:
            dict[str, Any]: Updated aggregated stream state.
        """
        if aggregated_event is None:
            aggregated_event = {
                "response_text": "",
                "reasoning_text": "",
                "usage": None,
                "finish_reason": None,
                "model_name": getattr(event, "model", None),
            }

        choice = self._extract_first_choice(event)
        delta = getattr(choice, "delta", None) if choice is not None else None
        delta_text = self._extract_text_from_delta(delta)
        delta_reasoning = self._extract_reasoning_from_delta(delta)

        if delta_text:
            aggregated_event["response_text"] = f"{aggregated_event['response_text']}{delta_text}"
        if delta_reasoning:
            aggregated_event["reasoning_text"] = f"{aggregated_event['reasoning_text']}{delta_reasoning}"

        finish_reason = getattr(choice, "finish_reason", None) if choice is not None else None
        if finish_reason is not None:
            aggregated_event["finish_reason"] = finish_reason

        usage = getattr(event, "usage", None)
        if usage is not None:
            aggregated_event["usage"] = usage

        model_name = getattr(event, "model", None)
        if model_name:
            aggregated_event["model_name"] = model_name

        return aggregated_event

    def extract_stream_delta(self, event: Any) -> str | None:
        """Extract the assistant text delta from one streamed event.

        Args:
            event (Any): Current stream event.

        Returns:
            str | None: Assistant text delta, if available.
        """
        choice = self._extract_first_choice(event)
        delta = getattr(choice, "delta", None) if choice is not None else None
        return self._extract_text_from_delta(delta)

    def update_partial_packet_from_stream(
        self, partial_packet: LLMConversationPacket, event: Any, delta_text: str
    ) -> None:
        """Update a partial packet from one streamed event.

        Args:
            partial_packet (LLMConversationPacket): Packet clone to mutate.
            event (Any): Current stream event.
            delta_text (str): Text delta extracted from the event.
        """
        choice = self._extract_first_choice(event)
        delta = getattr(choice, "delta", None) if choice is not None else None

        partial_packet.response = delta_text
        partial_packet.reasoning = self._extract_reasoning_from_delta(delta)
        partial_packet.provider_info = LLMProviderInfo(
            provider="openai_compatible_endpoint",
            model_name=getattr(event, "model", None) or self.attributes.init_args.llm_model_name,
        )
        partial_packet.termination = LLMTermination(
            finish_reason=getattr(choice, "finish_reason", None) if choice is not None else None,
            is_partial=getattr(choice, "finish_reason", None) is None if choice is not None else True,
        )

    def finalize_stream_packet(self, llm_conversation: LLMConversationPacket, aggregated_event: dict[str, Any]) -> None:
        """Finalize one packet after the stream completes.

        Args:
            llm_conversation (LLMConversationPacket): Conversation packet to update.
            aggregated_event (dict[str, Any]): Aggregated stream state.
        """
        usage = aggregated_event.get("usage")
        output_tokens = getattr(usage, "completion_tokens", None) if usage is not None else None
        reasoning_tokens = getattr(usage, "reasoning_tokens", None) if usage is not None else None
        completion_token_details = getattr(usage, "completion_tokens_details", None) if usage is not None else None
        if reasoning_tokens is None and completion_token_details is not None:
            reasoning_tokens = getattr(completion_token_details, "reasoning_tokens", None)

        llm_conversation.response = aggregated_event["response_text"] or None
        llm_conversation.reasoning = aggregated_event["reasoning_text"] or None
        llm_conversation.provider_info = LLMProviderInfo(
            provider="openai_compatible_endpoint",
            model_name=aggregated_event["model_name"] or self.attributes.init_args.llm_model_name,
        )
        llm_conversation.termination = LLMTermination(finish_reason=aggregated_event["finish_reason"], is_partial=False)

        if usage is not None:
            llm_conversation.usage = LLMUsage(
                input_tokens=getattr(usage, "prompt_tokens", None),
                output_tokens=output_tokens,
                reasoning_tokens=reasoning_tokens,
                total_tokens=getattr(usage, "total_tokens", None),
            )

        start_time = llm_conversation.generic_data.pop(_STREAM_START_TIME_KEY, None)
        latency_seconds = perf_counter() - start_time if isinstance(start_time, (int, float)) else None
        llm_conversation.performance = build_client_side_performance(
            llm_conversation.performance, latency_seconds=latency_seconds, output_tokens=output_tokens
        )

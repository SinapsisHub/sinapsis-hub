import json
from typing import Any

from sinapsis.data_transport import (
    DataContainer,
    LLMConversationPacket,
    LLMProviderInfo,
    LLMTermination,
    LLMToolCall,
    LLMUsage,
)
from sinapsis.logging import sinapsis_logger
from sinapsis.template import OutputTypes, UIPropertiesMetadata

from sinapsis_chatbots_base.helpers.endpoint_mcp_helpers import (
    EndpointMCPConstants,
    build_tool_description,
    extract_text_content,
    extract_tool_calls_from_content,
    format_json_content,
    make_tools_endpoint_compatible,
    strip_tool_call_blocks,
)
from sinapsis_chatbots_base.helpers.llm_conversation import (
    build_chat_message,
    build_packet_message,
    combine_assistant_responses,
    is_partial_llm_turn,
)
from sinapsis_chatbots_base.helpers.llm_keys import LLMChatKeys, MCPKeys
from sinapsis_chatbots_base.helpers.mcp_retry_helpers import (
    cleanup_conversation_state,
    get_tool_failure_count,
    stop_packet_after_max_retries,
    update_tool_failure_count,
)
from sinapsis_chatbots_base.helpers.performance import build_client_side_performance
from sinapsis_chatbots_base.helpers.tags import Tags
from sinapsis_chatbots_base.templates.endpoint_llm_completion import (
    EndpointLLMCompletion,
    EndpointLLMCompletionAttributes,
)


class EndpointLLMCompletionWithMCPAttributes(EndpointLLMCompletionAttributes):
    """Attributes for endpoint-backed MCP templates.

    Attributes:
        max_tool_retries (int): Maximum number of consecutive failed tool rounds before stopping.
        add_tool_to_prompt (bool): Whether tool descriptions should be appended to the system prompt.
        send_tools_in_payload (bool): Whether tool definitions should be sent through the endpoint payload.
        tool_choice (str | dict[str, Any] | None): Tool-choice directive for the endpoint request.
    """

    max_tool_retries: int = 3
    add_tool_to_prompt: bool = True
    send_tools_in_payload: bool = True
    tool_choice: str | dict[str, Any] | None = "auto"


class EndpointLLMCompletionWithMCP(EndpointLLMCompletion):
    """Template for OpenAI-compatible endpoint chat completion with MCP tool support.

    Usage example:

    agent:
      name: time_mcp_client
    templates:
      - template_name: InputTemplate
        class_name: InputTemplate
        attributes: {}
      - template_name: EndpointLLMCompletionWithMCP
        class_name: EndpointLLMCompletionWithMCP
        template_input: InputTemplate
        attributes:
          init_args:
            base_url: "http://localhost:8000/v1"
            llm_model_name: "Qwen/Qwen3-8B"
          completion_args:
            max_tokens: 2048
            temperature: 0.2
    """

    UIProperties = UIPropertiesMetadata(
        category="Chatbots",
        output_type=OutputTypes.TEXT,
        tags=[Tags.CHATBOTS, Tags.CONTEXT, Tags.LLM, Tags.TEXT_COMPLETION, Tags.TEXT, Tags.MCP],
    )

    AttributesBaseModel = EndpointLLMCompletionWithMCPAttributes
    attributes: AttributesBaseModel

    def __init__(self, attributes: Any) -> None:
        """Initialize MCP loop state for the endpoint template.

        Args:
            attributes (Any): Template attributes validated by `AttributesBaseModel`.
        """
        super().__init__(attributes)
        self.has_pending_tool_calls = False

    def _build_tool_guidance(self, llm_conversation: LLMConversationPacket) -> str:
        """Build the tool-guidance section appended to the system prompt.

        Args:
            llm_conversation (LLMConversationPacket): Conversation packet whose tools should be described.

        Returns:
            str: Prompt fragment describing available tools and fallback usage rules.
        """
        tools_section = "\n\n# Available Tools\n"
        for tool in self.build_available_tools(llm_conversation):
            tools_section += build_tool_description(tool)
        return f"{tools_section}{EndpointMCPConstants.TOOL_USAGE_GUIDELINES}"

    def build_system_message(self, llm_conversation: LLMConversationPacket) -> dict[str, Any] | None:
        """Build the system message, optionally appending tool guidance.

        Args:
            llm_conversation (LLMConversationPacket): Conversation packet being processed.

        Returns:
            dict[str, Any] | None: System message payload, or `None` when no system message is needed.
        """
        system_message = super().build_system_message(llm_conversation)
        if not self.attributes.add_tool_to_prompt or not llm_conversation.tools:
            return system_message

        tool_guidance = self._build_tool_guidance(llm_conversation)
        if system_message is None:
            return build_chat_message(
                LLMChatKeys.system_value, f"{EndpointMCPConstants.DEFAULT_SYSTEM_PROMPT}{tool_guidance}"
            )

        system_message[LLMChatKeys.content] = f"{system_message[LLMChatKeys.content]}{tool_guidance}"
        return system_message

    @staticmethod
    def build_available_tools(llm_conversation: LLMConversationPacket) -> list[dict[str, Any]]:
        """Build OpenAI-compatible tools for the current request.

        Args:
            llm_conversation (LLMConversationPacket): Conversation packet containing tool definitions.

        Returns:
            list[dict[str, Any]]: Endpoint-compatible function tool payloads.
        """
        return make_tools_endpoint_compatible(llm_conversation.tools)

    def build_history_messages(self, llm_conversation: LLMConversationPacket) -> list[dict[str, Any]]:
        """Build history messages while preserving tool-call metadata.

        Args:
            llm_conversation (LLMConversationPacket): Conversation packet containing persisted history.

        Returns:
            list[dict[str, Any]]: Endpoint-compatible history messages.
        """
        messages: list[dict[str, Any]] = []
        for message in llm_conversation.messages:
            chat_message = self.build_message_dict(message)
            if message.metadata:
                tool_calls = message.metadata.get(MCPKeys.tool_calls)
                tool_call_id = message.metadata.get(MCPKeys.tool_call_id)
                if tool_calls:
                    chat_message[MCPKeys.tool_calls] = tool_calls
                if tool_call_id:
                    chat_message[MCPKeys.tool_call_id] = tool_call_id
            messages.append(chat_message)
        return messages

    @staticmethod
    def build_tool_messages(llm_conversation: LLMConversationPacket) -> list[dict[str, Any]]:
        """Build native tool-result messages for the current turn.

        Args:
            llm_conversation (LLMConversationPacket): Conversation packet containing tool results.

        Returns:
            list[dict[str, Any]]: Endpoint-compatible tool-result messages.
        """
        messages: list[dict[str, Any]] = []
        for tool_result in llm_conversation.tool_results:
            text_content = format_json_content(extract_text_content(tool_result.content))
            if tool_result.is_error:
                text_content = f"{EndpointMCPConstants.TOOL_CALL_FAILED_PREFIX}{text_content}"

            message = build_chat_message(LLMChatKeys.tool_value, text_content)
            if tool_result.tool_call_id:
                message[MCPKeys.tool_call_id] = tool_result.tool_call_id
            elif tool_result.name:
                message[LLMChatKeys.name] = tool_result.name
            messages.append(message)
        return messages

    def build_current_turn_messages(
        self, llm_conversation: LLMConversationPacket, container: DataContainer | None = None
    ) -> list[dict[str, Any]]:
        """Build the current turn, suppressing the user prompt on resumed tool turns.

        Args:
            llm_conversation (LLMConversationPacket): Conversation packet for the current turn.
            container (DataContainer | None): Optional shared container.

        Returns:
            list[dict[str, Any]]: Current-turn messages to send to the endpoint.
        """
        if is_partial_llm_turn(llm_conversation):
            return []
        return super().build_current_turn_messages(llm_conversation, container)

    def build_backend_payload(
        self, llm_conversation: LLMConversationPacket, container: DataContainer | None = None
    ) -> dict[str, Any]:
        """Build the endpoint payload, including tools when enabled.

        Args:
            llm_conversation (LLMConversationPacket): Conversation packet to serialize.
            container (DataContainer | None): Optional shared container.

        Returns:
            dict[str, Any]: Chat completion payload for the endpoint.
        """
        payload = super().build_backend_payload(llm_conversation, container=container)
        tools = self.build_available_tools(llm_conversation)
        if tools and self.attributes.send_tools_in_payload:
            payload[MCPKeys.tools] = tools
            if self.attributes.tool_choice is not None:
                payload["tool_choice"] = self.attributes.tool_choice
        return payload

    @staticmethod
    def _get_value(obj: Any, field_name: str, default: Any = None) -> Any:
        """Read a value from an object or dictionary.

        Args:
            obj (Any): Source object or dictionary.
            field_name (str): Field or key name to read.
            default (Any): Fallback value when the field is missing.

        Returns:
            Any: Resolved value or the provided default.
        """
        if obj is None:
            return default
        if isinstance(obj, dict):
            return obj.get(field_name, default)
        return getattr(obj, field_name, default)

    def _extract_choice(self, response: Any) -> Any | None:
        """Extract the first response choice when present.

        Args:
            response (Any): Raw endpoint response object.

        Returns:
            Any | None: First choice object, or `None` when no choices are available.
        """
        choices = self._get_value(response, LLMChatKeys.choices, [])
        if not choices:
            return None
        return choices[0]

    @classmethod
    def _extract_message_text(cls, message: Any) -> str | None:
        """Extract assistant text from a response message.

        Args:
            message (Any): Endpoint message object or dictionary.

        Returns:
            str | None: Extracted assistant text, or `None` when absent.
        """
        content = cls._get_value(message, LLMChatKeys.content)
        if content is None:
            return None
        if isinstance(content, str):
            return content or None

        extracted = extract_text_content(content)
        return extracted or None

    @staticmethod
    def _parse_native_tool_arguments(arguments: Any) -> dict[str, Any]:
        """Parse native tool-call arguments safely.

        Args:
            arguments (Any): Raw native tool-call arguments.

        Returns:
            dict[str, Any]: Parsed argument dictionary, or an empty dict on failure.
        """
        if isinstance(arguments, dict):
            return arguments

        if isinstance(arguments, str):
            if not arguments.strip() or arguments.strip() in {"{}", "null", "None"}:
                return {}
            try:
                parsed_arguments = json.loads(arguments)
            except json.JSONDecodeError as exc:
                sinapsis_logger.warning(f"Failed to parse native tool arguments: {arguments}. Error: {exc}")
                return {}
            if isinstance(parsed_arguments, dict):
                return parsed_arguments

        return {}

    @classmethod
    def _serialize_native_tool_calls(cls, raw_tool_calls: Any) -> list[dict[str, Any]]:
        """Serialize provider-native tool calls into persistable dictionaries.

        Args:
            raw_tool_calls (Any): Raw tool-call payload returned by the endpoint.

        Returns:
            list[dict[str, Any]]: Serialized tool calls suitable for packet history storage.
        """
        if not isinstance(raw_tool_calls, list):
            return []

        serialized_tool_calls: list[dict[str, Any]] = []
        for raw_tool_call in raw_tool_calls:
            function = cls._get_value(raw_tool_call, MCPKeys.function, {})
            tool_name = cls._get_value(function, MCPKeys.name)
            if not isinstance(tool_name, str) or not tool_name:
                continue

            serialized_tool_calls.append(
                {
                    MCPKeys.tool_id: cls._get_value(raw_tool_call, MCPKeys.tool_id),
                    MCPKeys.tool_type: cls._get_value(raw_tool_call, MCPKeys.tool_type, MCPKeys.function),
                    MCPKeys.function: {
                        MCPKeys.name: tool_name,
                        MCPKeys.arguments: cls._get_value(function, MCPKeys.arguments, "{}"),
                    },
                }
            )

        return serialized_tool_calls

    @classmethod
    def _extract_native_tool_calls(cls, native_tool_calls: list[dict[str, Any]]) -> list[LLMToolCall]:
        """Extract normalized tool calls from native endpoint tool-call payloads.

        Args:
            native_tool_calls (list[dict[str, Any]]): Serialized native tool-call payloads.

        Returns:
            list[LLMToolCall]: Normalized tool calls for MCP execution.
        """
        parsed_tool_calls: list[LLMToolCall] = []
        for tool_call in native_tool_calls:
            function = cls._get_value(tool_call, MCPKeys.function, {})
            tool_name = cls._get_value(function, MCPKeys.name)
            if not isinstance(tool_name, str) or not tool_name:
                continue

            parsed_tool_calls.append(
                LLMToolCall(
                    name=tool_name,
                    arguments=cls._parse_native_tool_arguments(cls._get_value(function, MCPKeys.arguments, {})),
                    id=cls._get_value(tool_call, MCPKeys.tool_id),
                )
            )
        return parsed_tool_calls

    @staticmethod
    def _extract_text_tool_calls(response_text: str | None) -> list[LLMToolCall]:
        """Extract tool calls from assistant text using the fallback parser.

        Args:
            response_text (str | None): Assistant response text.

        Returns:
            list[LLMToolCall]: Parsed fallback tool calls extracted from text.
        """
        if not response_text:
            return []

        extracted = extract_tool_calls_from_content(response_text) or []
        return [
            LLMToolCall(
                name=tool_call[MCPKeys.tool_name],
                arguments=tool_call[MCPKeys.args],
                id=tool_call.get(MCPKeys.tool_use_id),
            )
            for tool_call in extracted
        ]

    @staticmethod
    def _build_assistant_message_metadata(
        tool_calls: list[LLMToolCall], native_tool_calls: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Build assistant metadata used to reconstruct tool-calling history.

        Args:
            tool_calls (list[LLMToolCall]): Normalized tool calls extracted for the current turn.
            native_tool_calls (list[dict[str, Any]]): Raw serialized native tool calls.

        Returns:
            dict[str, Any]: Metadata payload stored on the assistant history message.
        """
        if native_tool_calls:
            return {MCPKeys.tool_calls: native_tool_calls}
        if tool_calls:
            return {
                MCPKeys.tool_calls: [
                    {
                        MCPKeys.tool_id: tool_call.id,
                        MCPKeys.tool_type: MCPKeys.function,
                        MCPKeys.function: {
                            MCPKeys.name: tool_call.name,
                            MCPKeys.arguments: json.dumps(tool_call.arguments, ensure_ascii=True),
                        },
                    }
                    for tool_call in tool_calls
                ]
            }
        return {}

    def append_packet_history(
        self,
        llm_conversation: LLMConversationPacket,
        response_text: str | None,
        tool_calls: list[LLMToolCall],
        native_tool_calls: list[dict[str, Any]],
        was_partial: bool,
    ) -> None:
        """Persist the current MCP step directly on packet history.

        Args:
            llm_conversation (LLMConversationPacket): Conversation packet being updated.
            response_text (str | None): Assistant response text for the current step.
            tool_calls (list[LLMToolCall]): Parsed tool calls emitted in the current step.
            native_tool_calls (list[dict[str, Any]]): Serialized native tool calls for history.
            was_partial (bool): Whether this step resumed after previous tool calls.
        """
        if was_partial:
            for message in self.build_tool_messages(llm_conversation):
                packet_message = build_packet_message(
                    message[LLMChatKeys.role],
                    message[LLMChatKeys.content],
                    name=message.get(LLMChatKeys.name),
                    metadata={MCPKeys.tool_call_id: message.get(MCPKeys.tool_call_id)},
                )
                if packet_message is not None:
                    llm_conversation.messages.append(packet_message)
        else:
            user_message = self.build_user_message(llm_conversation)
            if user_message is not None:
                packet_message = build_packet_message(
                    user_message[LLMChatKeys.role],
                    user_message[LLMChatKeys.content],
                    name=user_message.get(LLMChatKeys.name),
                )
                if packet_message is not None:
                    llm_conversation.messages.append(packet_message)

        assistant_message = build_packet_message(
            LLMChatKeys.assistant_value,
            response_text or "",
            metadata=self._build_assistant_message_metadata(tool_calls, native_tool_calls),
        )
        if assistant_message is not None:
            llm_conversation.messages.append(assistant_message)

    def update_packet_metadata(
        self, llm_conversation: LLMConversationPacket, response: Any, *, is_partial: bool = False
    ) -> None:
        """Update provider metadata fields from an endpoint response.

        Args:
            llm_conversation (LLMConversationPacket): Conversation packet to update.
            response (Any): Raw endpoint response object.
            is_partial (bool): Whether the current turn is incomplete due to pending tool calls.
        """
        choice = self._extract_choice(response)
        if choice is None:
            return

        usage = self._get_value(response, "usage")
        completion_token_details = self._get_value(usage, "completion_tokens_details")
        output_tokens = self._get_value(usage, "completion_tokens")
        reasoning_tokens = self._get_value(usage, "reasoning_tokens")
        if reasoning_tokens is None:
            reasoning_tokens = self._get_value(completion_token_details, "reasoning_tokens")

        llm_conversation.provider_info = LLMProviderInfo(
            provider="openai_compatible_endpoint",
            model_name=self._get_value(response, "model") or self.attributes.init_args.llm_model_name,
        )
        previous_tool_failures = (
            llm_conversation.termination.consecutive_tool_failures if llm_conversation.termination is not None else 0
        )

        llm_conversation.termination = LLMTermination(
            finish_reason=self._get_value(choice, MCPKeys.finish_reason),
            stop_reason=self._get_value(choice, "stop_reason"),
            is_partial=is_partial,
            consecutive_tool_failures=previous_tool_failures,
        )

        if usage is not None:
            llm_conversation.usage = LLMUsage(
                input_tokens=self._get_value(usage, "prompt_tokens"),
                output_tokens=output_tokens,
                reasoning_tokens=reasoning_tokens,
                total_tokens=self._get_value(usage, "total_tokens"),
            )

        llm_conversation.performance = build_client_side_performance(
            llm_conversation.performance, output_tokens=output_tokens
        )

    def update_packet_from_response(self, llm_conversation: LLMConversationPacket, response: Any) -> None:
        """Update a packet from an endpoint MCP response.

        Args:
            llm_conversation (LLMConversationPacket): Conversation packet to update.
            response (Any): Raw endpoint response object.
        """
        self.logger.debug(f"Endpoint response: {response}")
        choice = self._extract_choice(response)
        if choice is None:
            return

        was_partial = is_partial_llm_turn(llm_conversation)
        message = self._get_value(choice, LLMChatKeys.message, {})
        response_text = self._extract_message_text(message)

        native_tool_calls = self._serialize_native_tool_calls(self._get_value(message, MCPKeys.tool_calls, []))
        tool_calls = self._extract_native_tool_calls(native_tool_calls)

        response_text_for_packet = response_text
        if not tool_calls:
            tool_calls = self._extract_text_tool_calls(response_text)
            if tool_calls:
                response_text_for_packet = strip_tool_call_blocks(response_text)

        reasoning = self._get_value(message, "reasoning")
        if reasoning is not None and not isinstance(reasoning, str):
            reasoning = json.dumps(reasoning, ensure_ascii=True, default=str)

        combined_response = combine_assistant_responses(llm_conversation.response, response_text_for_packet)
        _, history_response_text = self.split_reasoning_response(response_text_for_packet)
        cleaned_history_response = self.cleanup_response_text(history_response_text)
        self.append_packet_history(
            llm_conversation, cleaned_history_response, tool_calls, native_tool_calls, was_partial
        )

        llm_conversation.response = combined_response
        llm_conversation.reasoning = reasoning
        self.update_packet_metadata(llm_conversation, response, is_partial=bool(tool_calls))

        if tool_calls:
            llm_conversation.tool_calls = tool_calls
            llm_conversation.tool_results = []
            return

        cleanup_conversation_state(llm_conversation)

    def execute(self, container: DataContainer) -> DataContainer:
        """Process all conversation packets with MCP support.

        Args:
            container (DataContainer): Container holding conversation packets to process.

        Returns:
            DataContainer: Updated container after endpoint execution and MCP bookkeeping.
        """
        self.has_pending_tool_calls = False
        if not container.llm_conversations:
            self.logger.debug("Container has no llm conversations to process. Returning.")
            return container

        for llm_conversation in container.llm_conversations:
            if llm_conversation.tool_results:
                update_tool_failure_count(llm_conversation)
                if get_tool_failure_count(llm_conversation) >= self.attributes.max_tool_retries:
                    stop_packet_after_max_retries(llm_conversation)
                    continue
            self.process_llm_packet(llm_conversation=llm_conversation, container=container)
            self.has_pending_tool_calls = self.has_pending_tool_calls or bool(llm_conversation.tool_calls)
        return container

    def num_elements(self) -> int:
        """Determine whether the MCP loop should continue.

        Returns:
            int: `1` when tool calls are still pending, otherwise `-1`.
        """
        return 1 if self.has_pending_tool_calls else -1

import base64
from dataclasses import asdict, is_dataclass
from io import BytesIO
from typing import Any, Literal

from PIL import Image
from sinapsis.data_transport import LLMConversationPacket, LLMMessage

from sinapsis_chatbots_base.helpers.llm_keys import LLMChatKeys, MCPKeys


def extract_packet_identity(llm_conversation: LLMConversationPacket, exclude: set[str] | None = None) -> dict[str, Any]:
    """Extract identity values from a conversation packet.

    Args:
        llm_conversation (LLMConversationPacket): Conversation packet.
        exclude (set[str] | None): Identity keys to exclude.

    Returns:
        dict[str, Any]: Packet identity values excluding `None` entries.
    """
    if llm_conversation.identity is None:
        return {}

    excluded = exclude or set()

    return {
        key: value
        for key, value in asdict(llm_conversation.identity).items()
        if key not in excluded and value is not None
    }


def build_chat_message(role: str, msg_content: Any) -> dict[str, Any]:
    """Build a provider-compatible chat message payload.

    Args:
        role (str): Message role.
        msg_content (Any): Message content.

    Returns:
        dict[str, Any]: Normalized chat message dictionary.
    """
    return {LLMChatKeys.role: role, LLMChatKeys.content: msg_content}


def build_current_turn_messages(llm_conversation: LLMConversationPacket) -> list[dict[str, Any]]:
    """Build the current user and assistant turn from a packet.

    Args:
        llm_conversation (LLMConversationPacket): Conversation packet.

    Returns:
        list[dict[str, Any]]: Available user and assistant messages.
    """
    messages: list[dict[str, Any]] = []
    if llm_conversation.content is not None:
        messages.append(build_chat_message(role=LLMChatKeys.user_value, msg_content=llm_conversation.content))
    if llm_conversation.response is not None:
        messages.append(build_chat_message(role=LLMChatKeys.assistant_value, msg_content=llm_conversation.response))
    return messages


def normalize_tool_definition(tool: Any) -> dict[str, Any]:
    """Normalize one tool definition into a dictionary.

    Args:
        tool (Any): Tool definition as a dict, dataclass instance, or object with tool attributes.

    Returns:
        dict[str, Any]: Normalized tool definition dictionary.
    """
    if isinstance(tool, dict):
        return tool

    if not isinstance(tool, type) and is_dataclass(tool):
        return asdict(tool)

    return {
        MCPKeys.name: getattr(tool, MCPKeys.name),
        MCPKeys.description: getattr(tool, MCPKeys.description, ""),
        MCPKeys.input_schema: getattr(tool, MCPKeys.input_schema, {}),
    }


def build_packet_message(
    role: Literal["system", "user", "assistant", "tool", "developer"],
    content: Any,
    name: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> LLMMessage | None:
    """Build an `LLMMessage` suitable for packet history persistence.

    Args:
        role (str): Message role.
        content (Any): Message content.
        name (str | None): Optional speaker name.
        metadata (dict[str, Any] | None): Optional auxiliary metadata.

    Returns:
        LLMMessage | None: Persistable packet message when content is present.
    """
    if content is None:
        return None

    return LLMMessage(role=role, content=content, name=name, metadata=metadata or {})


def is_partial_llm_turn(llm_conversation: LLMConversationPacket) -> bool:
    """Return whether a packet represents an in-progress assistant turn.

    Args:
        llm_conversation (LLMConversationPacket): Conversation packet to inspect.

    Returns:
        bool: `True` when the packet termination state is marked partial.
    """
    return bool(llm_conversation.termination and llm_conversation.termination.is_partial)


def combine_assistant_responses(previous_response: str | None, current_response: str | None) -> str | None:
    """Combine partial and current assistant text into one response string.

    Args:
        previous_response (str | None): Previously accumulated assistant text.
        current_response (str | None): Current assistant text.

    Returns:
        str | None: Combined assistant text.
    """
    if previous_response and current_response:
        return f"{previous_response}\n{current_response}"
    if previous_response:
        return previous_response
    return current_response


def image_array_to_base64(image_array: Any, fmt: str = "JPEG") -> str:
    """Convert an image array into a base64 string.

    Args:
        image_array (Any): Image packet content, typically a numpy array.
        fmt (str): Output image format for encoding.

    Returns:
        str: Base64-encoded image bytes.
    """
    image = Image.fromarray(image_array)
    if fmt.upper() == "JPEG" and image.mode not in {"RGB", "L"}:
        image = image.convert("RGB")

    buffer = BytesIO()
    image.save(buffer, format=fmt)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def image_array_to_data_uri(image_array: Any, fmt: str = "JPEG") -> str:
    """Convert an image array into a base64 data URI.

    Args:
        image_array (Any): Image packet content, typically a numpy array.
        fmt (str): Output image format for encoding.

    Returns:
        str: Base64 data URI.
    """
    mime = f"image/{fmt.lower()}"
    encoded = image_array_to_base64(image_array, fmt=fmt)
    return f"data:{mime};base64,{encoded}"

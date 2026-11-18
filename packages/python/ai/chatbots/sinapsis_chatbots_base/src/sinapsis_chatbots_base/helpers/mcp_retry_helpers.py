from sinapsis.data_transport import LLMConversationPacket, LLMTermination
from sinapsis.logging import sinapsis_logger

_FALLBACK_RESPONSE = "I was unable to complete the request due to repeated tool failures."


def get_tool_failure_count(llm_conversation: LLMConversationPacket) -> int:
    """Return the consecutive tool-failure count for one packet.

    Args:
        llm_conversation (LLMConversationPacket): Conversation packet to inspect.

    Returns:
        int: Number of consecutive tool rounds that ended with at least one error.
    """
    if llm_conversation.termination is None:
        return 0
    return llm_conversation.termination.consecutive_tool_failures


def update_tool_failure_count(llm_conversation: LLMConversationPacket) -> None:
    """Update consecutive tool-failure count from the current tool results.

    Args:
        llm_conversation (LLMConversationPacket): Conversation packet whose tool results were updated.
    """
    if not llm_conversation.tool_results:
        return

    if llm_conversation.termination is None:
        llm_conversation.termination = LLMTermination()

    if any(result.is_error for result in llm_conversation.tool_results):
        llm_conversation.termination.consecutive_tool_failures += 1
    else:
        llm_conversation.termination.consecutive_tool_failures = 0


def cleanup_conversation_state(llm_conversation: LLMConversationPacket) -> None:
    """Clear transient MCP state from a completed conversation packet.

    Args:
        llm_conversation (LLMConversationPacket): Conversation packet to clean up.
    """
    llm_conversation.tool_calls = []
    llm_conversation.tool_results = []
    if llm_conversation.termination is not None:
        llm_conversation.termination.consecutive_tool_failures = 0


def stop_packet_after_max_retries(llm_conversation: LLMConversationPacket, instance_name: str | None = None) -> None:
    """Stop an MCP loop after too many consecutive tool failures.

    Args:
        llm_conversation (LLMConversationPacket): Conversation packet to mark as stopped.
        instance_name (str | None): Template instance name for logging context.
    """
    failure_count = get_tool_failure_count(llm_conversation)
    sinapsis_logger.warning(
        f"[{instance_name}] Stopping MCP loop for packet {llm_conversation.id} after "
        f"{failure_count} consecutive tool failures."
    )

    if llm_conversation.response is None:
        llm_conversation.response = _FALLBACK_RESPONSE

    if llm_conversation.termination is None:
        llm_conversation.termination = LLMTermination()

    llm_conversation.termination.is_partial = False
    llm_conversation.termination.stop_reason = "max_tool_retries"
    llm_conversation.termination.consecutive_tool_failures = failure_count

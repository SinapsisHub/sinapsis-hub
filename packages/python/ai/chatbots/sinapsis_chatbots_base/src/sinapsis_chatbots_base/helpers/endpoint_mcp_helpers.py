import json
import re
from typing import Any

from sinapsis.logging import sinapsis_logger

from sinapsis_chatbots_base.helpers.llm_conversation import normalize_tool_definition
from sinapsis_chatbots_base.helpers.llm_keys import LLMChatKeys, MCPKeys


class EndpointMCPConstants:
    """Constants used by endpoint-backed MCP integration.

    Attributes:
        TOOL_CALL_START (str): Marker that starts a plain-text fallback tool call block.
        TOOL_CALL_END (str): Marker that ends a plain-text fallback tool call block.
        TOOL_CALL_FAILED_PREFIX (str): Prefix added to tool-result text when a tool call failed.
        DEFAULT_SYSTEM_PROMPT (str): Default system prompt used when injecting tool guidance.
        TOOL_USAGE_GUIDELINES (str): Prompt snippet that explains fallback tool-call formatting.
    """

    TOOL_CALL_START = "TOOL_CALL"
    TOOL_CALL_END = "END_TOOL_CALL"

    TOOL_CALL_FAILED_PREFIX = "TOOL CALL FAILED: "

    DEFAULT_SYSTEM_PROMPT = (
        "You are a helpful AI assistant with access to tools. "
        "Use tools whenever you need current or external information."
    )

    TOOL_USAGE_GUIDELINES = """

# Tool Usage Guidelines

If native tool calling is available, use it.
Otherwise emit tool calls exactly with this plain-text format and no markdown fences:

TOOL_CALL
tool_name: exact_tool_name_here
args: {"param": "value"}
END_TOOL_CALL

Use the exact tool name and valid JSON arguments.
"""


def _normalize_parameters_schema(input_schema: dict[str, Any] | None) -> dict[str, Any]:
    """Normalize an MCP input schema into an endpoint-compatible parameters schema.

    Args:
        input_schema (dict[str, Any] | None): Original MCP input schema.

    Returns:
        dict[str, Any]: Normalized object schema compatible with OpenAI-style tools.
    """
    if not isinstance(input_schema, dict) or not input_schema:
        return {MCPKeys.tool_type: "object", MCPKeys.properties: {}}

    normalized_schema = dict(input_schema)
    normalized_schema.setdefault(MCPKeys.tool_type, "object")
    normalized_schema.setdefault(MCPKeys.properties, {})
    return normalized_schema


def make_tools_endpoint_compatible(tools: list[Any]) -> list[dict[str, Any]]:
    """Convert packet tools into OpenAI-compatible function tool definitions.

    Args:
        tools (list[Any]): Tool definitions stored on the conversation packet.

    Returns:
        list[dict[str, Any]]: Endpoint-compatible function tool payloads.
    """
    endpoint_tools: list[dict[str, Any]] = []
    for tool in tools:
        normalized_tool = normalize_tool_definition(tool)
        endpoint_tools.append(
            {
                MCPKeys.tool_type: MCPKeys.function,
                MCPKeys.function: {
                    MCPKeys.name: normalized_tool[MCPKeys.name],
                    MCPKeys.description: normalized_tool.get(MCPKeys.description, "") or "",
                    MCPKeys.parameters: _normalize_parameters_schema(normalized_tool.get(MCPKeys.input_schema)),
                },
            }
        )
    return endpoint_tools


def extract_tool_calls_from_content(content: str) -> list[dict[str, Any]] | None:
    """Extract fallback tool calls from assistant text.

    Args:
        content (str): Assistant text that may contain fallback tool-call blocks.

    Returns:
        list[dict[str, Any]] | None: Parsed fallback tool calls, or `None` when none were found.
    """
    tool_calls = _extract_explicit_tool_call_blocks(content)
    tool_calls.extend(_extract_xml_tool_call_blocks(content))

    return tool_calls if tool_calls else None


def _extract_explicit_tool_call_blocks(content: str) -> list[dict[str, Any]]:
    """Extract `TOOL_CALL ... END_TOOL_CALL` fallback blocks.

    Args:
        content (str): Assistant text that may contain explicit fallback blocks.

    Returns:
        list[dict[str, Any]]: Parsed tool-call payloads extracted from explicit blocks.
    """
    pattern = (
        rf"{re.escape(EndpointMCPConstants.TOOL_CALL_START)}\s*\n"
        rf"(.*?)(?:\n{re.escape(EndpointMCPConstants.TOOL_CALL_END)}|$)"
    )
    blocks = re.findall(pattern, content, re.DOTALL)
    tool_calls = []
    for block in blocks:
        parsed = _parse_tool_block(block)
        if parsed is not None:
            tool_calls.append(parsed)
    return tool_calls


def _extract_xml_tool_call_blocks(content: str) -> list[dict[str, Any]]:
    """Extract XML-like `<tool_call>` fallback blocks.

    Args:
        content (str): Assistant text that may contain XML-like tool-call blocks.

    Returns:
        list[dict[str, Any]]: Parsed tool-call payloads extracted from XML-like blocks.
    """
    pattern = re.compile(r"<tool_call>\s*(.*?)\s*</tool_call>", re.DOTALL)
    blocks = pattern.findall(content)
    tool_calls = []
    for block in blocks:
        parsed = _parse_xml_tool_call_block(block)
        if parsed is not None:
            tool_calls.append(parsed)
    return tool_calls


def _parse_tool_block(block: str) -> dict[str, Any] | None:
    """Parse one plain-text fallback tool-call block.

    Args:
        block (str): Tool-call block body without the wrapper markers.

    Returns:
        dict[str, Any] | None: Normalized tool-call payload, or `None` when parsing fails.
    """
    lines = [line.strip() for line in block.strip().split("\n") if line.strip()]
    if not lines:
        return None

    tool_name = _extract_tool_name(lines)
    args_dict = _extract_tool_args(lines)
    if not tool_name:
        return None

    return {
        MCPKeys.tool_name: tool_name,
        MCPKeys.args: args_dict,
        MCPKeys.tool_use_id: f"{tool_name}_{hash(block) % 1000}",
    }


def _extract_tool_name(lines: list[str]) -> str | None:
    """Extract the tool name from fallback tool-call lines.

    Args:
        lines (list[str]): Normalized non-empty lines from one fallback tool-call block.

    Returns:
        str | None: Extracted tool name, or `None` when no name could be inferred.
    """
    tool_name_from_keyword = None
    tool_name_from_standalone = None

    for line in lines:
        if line.startswith(f"{MCPKeys.tool_name}:"):
            tool_name_from_keyword = line.split(":", 1)[1].strip()
        elif ":" in line and not line.startswith(("args:", f"{MCPKeys.args}:")):
            key_part = line.split(":", 1)[0].strip()
            value_part = line.split(":", 1)[1].strip()
            if value_part.startswith(("{", "[")):
                return key_part
        elif (
            not line.startswith(("args:", f"{MCPKeys.args}:", f"{MCPKeys.tool_name}:"))
            and not line.startswith(("{", "["))
            and tool_name_from_standalone is None
        ):
            tool_name_from_standalone = line

    return tool_name_from_keyword or tool_name_from_standalone


def _extract_tool_args(lines: list[str]) -> dict[str, Any]:
    """Extract JSON arguments from fallback tool-call lines.

    Args:
        lines (list[str]): Normalized non-empty lines from one fallback tool-call block.

    Returns:
        dict[str, Any]: Parsed JSON arguments, or an empty dict on failure.
    """
    for line in lines:
        args_str = None

        if line.startswith(("args:", f"{MCPKeys.args}:")):
            args_str = line.split(":", 1)[1].strip()
        elif ":" in line and not line.startswith(f"{MCPKeys.tool_name}:"):
            value_part = line.split(":", 1)[1].strip()
            if value_part.startswith(("{", "[")):
                args_str = value_part

        if args_str is None:
            continue

        if args_str in {"{}", "", "null", "None"}:
            return {}

        try:
            parsed = json.loads(args_str)
        except json.JSONDecodeError as exc:
            sinapsis_logger.warning(f"Failed to parse MCP fallback tool args: {args_str}. Error: {exc}")
            return {}

        return parsed if isinstance(parsed, dict) else {}

    return {}


def _parse_xml_tool_call_block(block: str) -> dict[str, Any] | None:
    """Parse one XML-like tool-call block.

    Args:
        block (str): XML-like tool-call block body without the outer tags.

    Returns:
        dict[str, Any] | None: Normalized tool-call payload, or `None` when parsing fails.
    """
    function_match = re.search(r"<function=([^>]+)>", block)
    if function_match is None:
        return None

    tool_name = function_match.group(1).strip()
    if not tool_name:
        return None

    arguments: dict[str, Any] = {}
    for parameter_name, parameter_value in re.findall(r"<parameter=([^>]+)>\s*(.*?)\s*</parameter>", block, re.DOTALL):
        normalized_name = parameter_name.strip()
        normalized_value = parameter_value.strip()
        if not normalized_name:
            continue
        arguments[normalized_name] = normalized_value

    return {
        MCPKeys.tool_name: tool_name,
        MCPKeys.args: arguments,
        MCPKeys.tool_use_id: f"{tool_name}_{hash(block) % 1000}",
    }


def strip_tool_call_blocks(content: str | None) -> str | None:
    """Remove fallback tool-call blocks from assistant text.

    Args:
        content (str | None): Assistant text that may contain fallback tool-call blocks.

    Returns:
        str | None: Assistant text with fallback tool-call blocks removed.
    """
    if not content:
        return content

    explicit_pattern = re.compile(
        rf"{re.escape(EndpointMCPConstants.TOOL_CALL_START)}\s*\n"
        rf".*?(?:\n{re.escape(EndpointMCPConstants.TOOL_CALL_END)}|$)",
        flags=re.DOTALL,
    )
    xml_pattern = re.compile(r"<tool_call>\s*.*?\s*</tool_call>", flags=re.DOTALL)
    stripped = explicit_pattern.sub("", content)
    stripped = xml_pattern.sub("", stripped)
    stripped = re.sub(r"\n{3,}", "\n\n", stripped).strip()
    return stripped or None


def format_json_content(raw_text: str) -> str:
    """Pretty-print JSON content when it looks like a JSON object.

    Args:
        raw_text (str): Raw text returned by a tool or extracted from a payload.

    Returns:
        str: Pretty-printed JSON text when parsing succeeds, otherwise the original text.
    """
    text = raw_text.strip()
    if not (text.startswith("{") and text.endswith("}")):
        return raw_text

    try:
        parsed_data = json.loads(raw_text)
    except json.JSONDecodeError:
        return raw_text

    return json.dumps(parsed_data, indent=2)


def build_tool_description(tool: dict[str, Any]) -> str:
    """Build a readable tool description block for prompt injection.

    Args:
        tool (dict[str, Any]): Endpoint-compatible tool definition.

    Returns:
        str: Human-readable prompt fragment describing the tool and its parameters.
    """
    if not (tool.get(MCPKeys.tool_type) == MCPKeys.function and MCPKeys.function in tool):
        return ""

    function = tool[MCPKeys.function]
    description = f"\n## {function[MCPKeys.name]}\n"
    description += f"Description: {function.get(MCPKeys.description, '')}\n"

    parameters = function.get(MCPKeys.parameters, {})
    if parameters.get(MCPKeys.properties):
        description += "Parameters:\n"
        required_params = parameters.get(MCPKeys.required, [])

        for param_name, param_info in parameters[MCPKeys.properties].items():
            param_type = param_info.get(MCPKeys.tool_type, "string")
            param_desc = param_info.get(MCPKeys.description, "")
            req_text = " (required)" if param_name in required_params else " (optional)"
            description += f"  - {param_name} ({param_type}){req_text}: {param_desc}\n"

    return description + "\n"


def _extract_text_content_item(content_item: Any) -> str | None:
    """Extract one text fragment from a tool-result content item.

    Args:
        content_item (Any): Tool-result content item in string, dict, or object form.

    Returns:
        str | None: Extracted text fragment, or `None` when no text could be derived.
    """
    if content_item is None:
        return None

    if isinstance(content_item, str):
        return content_item

    if isinstance(content_item, dict):
        text_value = content_item.get(MCPKeys.text)
        if isinstance(text_value, str):
            return text_value

        content_value = content_item.get(LLMChatKeys.content)
        if isinstance(content_value, str):
            return content_value

        return json.dumps(content_item, ensure_ascii=True, default=str)

    if hasattr(content_item, MCPKeys.text):
        text_value = getattr(content_item, MCPKeys.text)
        if isinstance(text_value, str):
            return text_value

    if hasattr(content_item, LLMChatKeys.content):
        content_value = getattr(content_item, LLMChatKeys.content)
        if isinstance(content_value, str):
            return content_value

    return json.dumps(content_item, ensure_ascii=True, default=str)


def extract_text_content(content: Any) -> str:
    """Extract text content from a normalized tool-result payload.

    Args:
        content (Any): Tool-result content payload in string, list, dict, or object form.

    Returns:
        str: Joined text extracted from the payload.
    """
    if content is None:
        return ""

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = [text for item in content if (text := _extract_text_content_item(item))]
        return "\n".join(parts)

    extracted_text = _extract_text_content_item(content)
    return extracted_text or ""

import importlib
from collections.abc import Callable

_root_lib_path = "sinapsis_chatbots_base.templates"

_template_lookup = {
    "EndpointLLMCompletion": f"{_root_lib_path}.endpoint_llm_completion",
    "EndpointLLMCompletionWithMCP": f"{_root_lib_path}.endpoint_llm_completion_mcp",
    "EndpointLLMMultiModal": f"{_root_lib_path}.endpoint_llm_multimodal",
    "EndpointLLMStreamingCompletion": f"{_root_lib_path}.endpoint_llm_streaming_completion",
    "LLMConversationInput": f"{_root_lib_path}.llm_conversation_input",
    "QueryContextualizeFromFile": f"{_root_lib_path}.query_contextualize_from_file",
    "TextToLLMConversation": f"{_root_lib_path}.text_to_llm_conversation",
}


def __getattr__(name: str) -> Callable:
    if name in _template_lookup:
        module = importlib.import_module(_template_lookup[name])
        return getattr(module, name)
    raise AttributeError(f"template `{name}` not found in {_root_lib_path}")


__all__ = list(_template_lookup.keys())

import importlib
from collections.abc import Callable

_root_lib_path = "sinapsis_unsloth.templates"

_template_lookup = {
    "UnslothConversationTrainer": f"{_root_lib_path}.training.unsloth_conversation_trainer",
    "UnslothExportGGUF": f"{_root_lib_path}.export.unsloth_export_gguf",
    "UnslothExportMerged": f"{_root_lib_path}.export.unsloth_export_merged",
    "UnslothInferenceCompletion": f"{_root_lib_path}.inference.unsloth_inference_completion",
    "UnslothInferenceConversational": f"{_root_lib_path}.inference.unsloth_inference_conversational",
    "UnslothInferenceInstruct": f"{_root_lib_path}.inference.unsloth_inference_instruct",
    "UnslothInferenceReasoning": f"{_root_lib_path}.inference.unsloth_inference_reasoning",
    "UnslothInstructTrainer": f"{_root_lib_path}.training.unsloth_instruct_trainer",
    "UnslothPretrainer": f"{_root_lib_path}.training.unsloth_pretrainer",
}


def __getattr__(name: str) -> Callable:
    if name in _template_lookup:
        module = importlib.import_module(_template_lookup[name])
        return getattr(module, name)

    raise AttributeError(f"template `{name}` not found in {_root_lib_path}")


__all__ = list(_template_lookup.keys())

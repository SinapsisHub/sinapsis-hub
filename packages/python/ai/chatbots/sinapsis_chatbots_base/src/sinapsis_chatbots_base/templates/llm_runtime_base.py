import gc

import torch

from sinapsis_chatbots_base.templates.llm_template_base import LLMTemplateBase


class LLMRuntimeBase(LLMTemplateBase):
    """Base template for local or self-hosted LLM runtimes."""

    @staticmethod
    def clear_memory() -> None:
        """Run garbage collection and release GPU memory when available."""
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()

    def clear_model(self) -> None:
        """Release the loaded runtime backend, if any."""
        self.llm = None

    def reset_state(self, template_name: str | None = None) -> None:
        """Reset the runtime backend.

        Args:
            template_name (str | None): Optional template name passed by the agent.
        """
        _ = template_name
        self.clear_model()
        self.clear_memory()
        self.initialize()
        self.logger.info(f"Reset template instance `{self.instance_name}`")

    def cancel_execution(self) -> None:
        """Run best-effort runtime cancellation."""
        self.clear_model()
        self.clear_memory()

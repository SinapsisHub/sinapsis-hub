from sinapsis_unsloth.helpers.schemas.export import UnslothExportMergedArgs
from sinapsis_unsloth.templates.export.unsloth_export_base import UnslothExportBase, UnslothExportBaseAttributes


class UnslothExportMerged(UnslothExportBase):
    """Template for exporting merged models with Unsloth.

    Provides functionality to export Unsloth-optimized models either locally or to the Hugging Face Hub.

    Usage example:

    agent:
      name: my_test_agent
    templates:
    - template_name: InputTemplate
      class_name: InputTemplate
      attributes: {}
    - template_name: UnslothExportMerged
      class_name: UnslothExportMerged
      template_input: InputTemplate
      attributes:
        model_args:
          model_name: unsloth/DeepSeek-R1-Distill-Qwen-1.5B
          max_seq_length: 2048
          dtype: auto
          load_in_4bit: true
          load_in_8bit: false
          load_in_16bit: false
          full_finetuning: false
          device_map: sequential
          use_gradient_checkpointing: unsloth
          fast_inference: false
          gpu_memory_utilization: 0.5
          random_state: 3407
          max_lora_rank: 64
        export_args:
          save_path: artifacts/DeepSeek-R1-Distill-Qwen-1.5B-16-bit
          max_shard_size: 5GB
          maximum_memory_usage: 0.75
          save_method: merged_16bit
        push_to_hub: false

    """

    class AttributesBaseModel(UnslothExportBaseAttributes):
        """Configuration parameters for merged model export operations.

        Attributes:
            export_args (UnslothExportMergedArgs): Configuration arguments for exporting the merged model.
        """

        export_args: UnslothExportMergedArgs

    def set_export_method(self) -> str:
        """Sets the export method for the model.

        Returns:
            str: The export method to be used to export the model.
        """
        if self.attributes.push_to_hub:
            return "push_to_hub_merged"
        return "save_pretrained_merged"

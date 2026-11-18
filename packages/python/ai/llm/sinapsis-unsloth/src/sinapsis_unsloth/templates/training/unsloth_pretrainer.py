from unsloth import UnslothTrainer, UnslothTrainingArguments

from sinapsis_unsloth.helpers.schemas.fine_tuning import UnslothTrainingArgs
from sinapsis_unsloth.templates.training.unsloth_fine_tuning_base import (
    UnslothFineTuningBase,
    UnslothFineTuningBaseAttributes,
)

from typing import Any

from pydantic import Field
from torch.utils.data import Dataset
from transformers import Trainer, TrainingArguments


class UnslothPretrainingArgs(UnslothTrainingArgs):
    """Extended training arguments for Continued Pretraining (CPT).

    Attributes:
        embedding_learning_rate (float): A specific learning rate for the embedding
            layers and lm_head. Usually lower than the main learning rate to prevent
            catastrophic forgetting during CPT. Defaults to 5e-5.
    """

    embedding_learning_rate: float = 5e-5


class UnslothPretrainer(UnslothFineTuningBase):
    """Template for continued pretraining of language models using Unsloth.

    Specializes in efficient pretraining on raw text datasets using Unsloth's optimized
    training components. Extends the base fine-tuning template with pretraining-specific
    dataset handling and Unsloth's custom trainer configuration.

    Usage example:

    agent:
      name: my_test_agent
    templates:
    - template_name: InputTemplate
      class_name: InputTemplate
      attributes: {}
    - template_name: UnslothPretrainer
      class_name: UnslothPretrainer
      template_input: InputTemplate
      attributes:
        model_args:
          model_name: 'unsloth/DeepSeek-R1-Distill-Qwen-7B'
          max_seq_length: 2048
          dtype: auto
          load_in_4bit: true
          use_gradient_checkpointing: unsloth
          gpu_memory_utilization: 0.5
          random_state: 3407
          max_lora_rank: 64
        lora_args:
          r: 16
          target_modules:
          - q_proj
          - k_proj
          - v_proj
          - o_proj
          - gate_proj
          - up_proj
          - down_proj
          - "embed_tokens"
          - "lm_head"
          lora_alpha: 16
          lora_dropout: 0.0
          bias: none
          use_gradient_checkpointing: unsloth
          random_state: 3407
          use_rslora: false
          modules_to_save: null
        trainer_args:
          dataset_text_field: text
          dataset_num_proc: null
          max_length: 1024
          packing: false
        training_args:
          per_device_train_batch_size: 4
          gradient_accumulation_steps: 8
          warmup_ratio: 0.1
          num_train_epochs: 2
          learning_rate: 0.00005
          embedding_learning_rate: 0.00001
          fp16: false
          bf16: true
          logging_steps: 1
          optim: adamw_8bit
          weight_decay: 0.01
          lr_scheduler_type: linear
          seed: 3407
          output_dir: outputs
          save_strategy: "epoch"
          report_to: none
        train_dataset:
          loader_args:
            path: 'json'
            data_files: 'path/to/dataset.jsonl'
            split: train
          map_args:
            batched: false
            batch_size: 1000
            num_proc: 0
            keep_in_memory: false
            load_from_cache_file: true
          shuffle:
            enabled: true
            args:
              seed: 3407
          pre_tokenize:
            enabled: false
        resume_from_checkpoint: false
        save_path: 'path/to/fine-tuned-lora/`'

    """

    class AttributesBaseModel(UnslothFineTuningBaseAttributes):
        """Configuration attributes for Unsloth Pretraining.

        Overrides training_args to include embedding_learning_rate.

        Attributes:
            training_args (UnslothTrainingArgs): Hugging Face training arguments (batch size, learning rate).
        """

        training_args: UnslothPretrainingArgs = Field(default_factory=UnslothPretrainingArgs)

    def _prepare_dataset(self, dataset: Dataset) -> Dataset:
        """Formats raw text data for continued pretraining.

        Args:
            dataset (Dataset): Raw dataset loaded from HuggingFace datasets or locally,
                   expected to contain the configured text field.

        Returns:
            Dataset: Processed dataset with formatted text examples ready for training.
        """
        eos_token = self.tokenizer.eos_token
        text_column: str = self.attributes.trainer_args.dataset_text_field

        def _format_examples(examples: dict[str, Any]) -> dict[str, list[str]]:
            """Adds EOS tokens to raw text examples.

            Args:
                examples (dict[str, Any]): Batch of raw text examples from the dataset.

            Returns:
                dict[str, list[str]]: Dictionary with formatted text under the configured text field key.
            """
            return {text_column: [example + eos_token for example in examples[text_column]]}

        return dataset.map(_format_examples, **self.attributes.train_dataset.map_args.model_dump(exclude_none=True))

    @staticmethod
    def _get_trainer_classes() -> tuple[type[Trainer], type[TrainingArguments]]:
        """Provides Unsloth-specific trainer components for pretraining.

        Returns:
            tuple: (TrainerClass, TrainingArgumentsClass) pair to be used for training.
        """
        return UnslothTrainer, UnslothTrainingArguments

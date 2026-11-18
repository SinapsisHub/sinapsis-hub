from unsloth import standardize_sharegpt, to_sharegpt
from unsloth.chat_templates import get_chat_template, train_on_responses_only

from sinapsis_unsloth.helpers.chat_templates import DEEPSEEK_R1_CHAT_TEMPLATE
from sinapsis_unsloth.helpers.schemas.fine_tuning import (
    ConversationalDatasetConfig,
    DataCollatorArgs,
    TrainingChatTemplateConfig,
)
from sinapsis_unsloth.templates.training.unsloth_fine_tuning_base import (
    UnslothFineTuningBase,
    UnslothFineTuningBaseAttributes,
)

from typing import Any

from pydantic import Field
from sinapsis.template import TemplateAttributeType
from torch.utils.data import Dataset
from transformers import DataCollatorForSeq2Seq, Trainer, TrainingArguments
from trl import SFTTrainer


class UnslothConversationTrainerAttributes(UnslothFineTuningBaseAttributes):
    """Attributes configuration for Unsloth Conversation fine-tuning template.

    This class defines the configuration parameters needed for fine-tuning a language model
    using the Unsloth framework.

    Attributes:
        input_dataset_format (Literal["alpaca", "sharegpt"]): Format of the input dataset ('alpaca' or 'sharegpt').
            If alpaca, then it's automatically converted into single/multi-turn conversations format.
        alpaca_to_sharegpt_kwargs (dict[str, Any] | None): Arguments for to_sharegpt function to allow customization
            when loading alpaca dataset.
        target_dataset_format (str): Target chat template format for the processed dataset.
        mapping (dict[str, Any]): Dictionary mapping conversation fields with default structure:
                {
                    "role": "role",
                    "content": "content",
                    "user": "user",
                    "assistant": "assistant"
                }
        map_eos_token (bool): Whether to map EOS token during template application. Defaults to True.
        system_message (str): Optional system message to prepend to conversations.
        train_responses_only (bool): Whether to only compute loss on assistant responses
        data_collator_kwargs (dict[str, Any]): Custom arguments for conversation data collation
    """

    train_dataset: ConversationalDatasetConfig
    chat_template: TrainingChatTemplateConfig
    train_responses_only: bool = True
    data_collator_args: DataCollatorArgs = Field(default_factory=DataCollatorArgs)


class UnslothConversationTrainer(UnslothFineTuningBase):
    """Template for conversation-based-fine-tuning on language models using Unsloth framework.

    Handles the complete training pipeline including dataset preparation, template application,
    and model training with SFTTrainer.

    Usage example:

    agent:
      name: my_test_agent
    templates:
    - template_name: InputTemplate
      class_name: InputTemplate
      attributes: {}
    - template_name: UnslothConversationTrainer
      class_name: UnslothConversationTrainer
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
          input_format: 'alpaca'
          to_sharegpt_args:
            merged_prompt: '{instruction}[[{input}]]'
            merged_column_name: instruction
            output_column_name: output
            remove_unused_columns: true
            conversation_extension: 1
            random_state: 3407
        resume_from_checkpoint: false
        save_path: 'path/to/fine-tuned-lora/'
        chat_template:
          mapping:
            role: role
            content: content
            user: user
            assistant: assistant
          map_eos_token: true
          system_message: "You're a useful assistant"
          target_format: 'deepseek-r1'
        train_responses_only: true

    """

    AttributesBaseModel = UnslothConversationTrainerAttributes

    def __init__(self, attributes: TemplateAttributeType) -> None:
        super().__init__(attributes)
        if self.attributes.train_responses_only:
            self._modify_trainer_for_responses()

    def _prepare_dataset(self, dataset: Dataset) -> Dataset:
        """Prepare and format the dataset for instruction fine-tuning.

        Args:
            dataset (Dataset): Raw dataset loaded from HuggingFace datasets.

        Returns:
            Dataset: Processed dataset with formatted text examples ready for training.
        """
        if self.attributes.train_dataset.input_format == "alpaca":
            dataset = to_sharegpt(dataset, **self.attributes.train_dataset.to_sharegpt_args.model_dump())
        dataset = standardize_sharegpt(dataset)
        if self.attributes.chat_template.target_format in ["deepseek_r1", "deepseek-r1"]:
            chat_template = (
                (self.tokenizer.chat_template, self.tokenizer.eos_token)
                if hasattr(self.tokenizer, "chat_template")
                else (DEEPSEEK_R1_CHAT_TEMPLATE)
            )
        else:
            chat_template = self.attributes.chat_template.target_format
        self.tokenizer = get_chat_template(
            tokenizer=self.tokenizer,
            mapping=self.attributes.chat_template.mapping.model_dump(),
            chat_template=chat_template,
            map_eos_token=self.attributes.chat_template.map_eos_token,
            system_message=self.attributes.chat_template.system_message,
        )
        tokenizer = self.tokenizer
        text_column: str = self.attributes.trainer_args.dataset_text_field

        def format_examples(examples: dict[str, Any]) -> dict[str, list[str]]:
            """Formats examples for model training.

            Args:
                examples (dict[str, Any]): Batch of examples to format.

            Returns:
                dict[str, list[str]]: Formatted examples with prompts.
            """
            convos = examples["conversations"]
            texts = [
                tokenizer.apply_chat_template(convo, tokenize=False, add_generation_prompt=False) for convo in convos
            ]
            return {text_column: texts}

        return dataset.map(format_examples, **self.attributes.train_dataset.map_args.model_dump(exclude_none=True))

    def _set_data_collator(self) -> DataCollatorForSeq2Seq | None:
        """Returns the data collator for the trainer.

        Returns:
            DataCollatorForSeq2Seq: The data collator to be used.
        """
        if not self.attributes.train_responses_only:
            return None
        return DataCollatorForSeq2Seq(
            tokenizer=self.tokenizer, **self.attributes.data_collator_args.model_dump(exclude_none=True)
        )

    @staticmethod
    def _get_trainer_classes() -> tuple[type[Trainer], type[TrainingArguments]]:
        """Provides Unsloth-specific trainer components for pretraining.

        Returns:
            tuple: (TrainerClass, TrainingArgumentsClass) pair to be used for training.
            Must be implemented by subclasses.
        """
        return SFTTrainer, TrainingArguments

    def _modify_trainer_for_responses(self) -> None:
        """Modifies the trainer to focus training on response segments only."""
        normalized_name = self.normalize_template_name(self.attributes.chat_template.target_format)
        pattern = getattr(self.PATTERNS, normalized_name)
        self.trainer = train_on_responses_only(self.trainer, pattern.instruction, pattern.response)

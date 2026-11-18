from sinapsis_unsloth.helpers.schemas.fine_tuning import AlpacaConfig
from sinapsis_unsloth.templates.training.unsloth_fine_tuning_base import (
    UnslothFineTuningBase,
    UnslothFineTuningBaseAttributes,
)

from typing import Any, cast

from pydantic import Field
from torch.utils.data import Dataset
from transformers import Trainer, TrainingArguments
from trl import SFTTrainer


class UnslothInstructTrainerAttributes(UnslothFineTuningBaseAttributes):
    """Attribute configuration for the Unsloth Instruct fine-tuning template.

    Defines configuration parameters required for instruction-based fine-tuning
    of language models using the Unsloth framework.

    Attributes:
        alpaca_config (AlpacaConfig): Attributes used to prepend information or identify the fields for the
            dataset.
    """

    alpaca_config: AlpacaConfig = Field(default_factory=AlpacaConfig)


class UnslothInstructTrainer(UnslothFineTuningBase):
    """Fine-tuning template for instruction-based LLM training using the Unsloth framework.

    Handles the complete training pipeline including dataset preparation, template application,
    and model training with SFTTrainer.

    Usage example:

    agent:
      name: my_test_agent
    templates:
    - template_name: InputTemplate
      class_name: InputTemplate
      attributes: {}
    - template_name: UnslothInstructTrainer
      class_name: UnslothInstructTrainer
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
            enabled: false
            args:
              seed: null
              keep_in_memory: false
              load_from_cache_file: true
          pre_tokenize:
            enabled: false
            args:
              add_special_tokens: true
              padding: do_not_pad
              truncation: do_not_truncate
              max_length: null
              stride: 0
              is_split_into_words: false
              padding_side: null
              verbose: true
            map_args:
              desc: null
              batched: false
              batch_size: 1000
              num_proc: 0
              keep_in_memory: false
              load_from_cache_file: true
        resume_from_checkpoint: false
        save_path: 'path/to/fine-tuned-lora/'
        alpaca_config:
          task_preamble: "Write a response that appropriately"
          instruction_key: instruction
          input_key: input
          output_key: output

    """

    AttributesBaseModel = UnslothInstructTrainerAttributes

    def _get_template_prompt(self) -> tuple[str, str]:
        """Generate the template prompts for the Alpaca dataset..

        Returns:
            tuple[str, str]: A tuple containing two strings:
                - The first string is the prompt with input.
                - The second string is the prompt without input.
        """
        prompt_with_input = (
            self.PATTERNS.alpaca.instruction
            + "{}\n\n"
            + cast(str, self.PATTERNS.alpaca.system)
            + "{}\n\n"
            + self.PATTERNS.alpaca.response
            + "{}"
        )
        prompt_no_input = self.PATTERNS.alpaca.instruction + "{}\n\n" + self.PATTERNS.alpaca.response + "{}"

        return prompt_with_input, prompt_no_input

    def _prepare_dataset(self, dataset: Dataset) -> Dataset:
        """Prepares and formats the dataset for instruction fine-tuning.

        Applies the defined instruction template to each example in the dataset,
        transforming it into a text prompt suitable for supervised fine-tuning.

        Args:
            dataset (Dataset): Raw dataset loaded from HuggingFace datasets.

        Returns:
            Dataset: Processed dataset with formatted text examples ready for training.
        """
        text_column = self.attributes.trainer_args.dataset_text_field
        eos_token = self.tokenizer.eos_token
        instruction_key = self.attributes.alpaca_config.instruction_key
        input_key = self.attributes.alpaca_config.input_key
        output_key = self.attributes.alpaca_config.output_key
        task_preamble = self.attributes.alpaca_config.task_preamble
        prompt_with_input, prompt_no_input = self._get_template_prompt()

        def format_examples(examples: dict[str, Any]) -> dict[str, list[str]]:
            """Formats examples for model training.

            Args:
                examples (dict[str, Any]): Batch of examples to format.

            Returns:
                dict[str, list[str]]: Formatted examples with prompts.
            """
            instructions = examples[instruction_key]
            inputs = examples[input_key]
            outputs = examples[output_key]
            texts = []

            for instruction, input_text, output in zip(instructions, inputs, outputs):
                if input_text and str(input_text).strip():
                    formatted = prompt_with_input.format(instruction, input_text, output)
                else:
                    formatted = prompt_no_input.format(instruction, output)

                texts.append(task_preamble + formatted + eos_token)

            return {text_column: texts}

        return dataset.map(format_examples, **self.attributes.train_dataset.map_args.model_dump(exclude_none=True))

    @staticmethod
    def _get_trainer_classes() -> tuple[type[Trainer], type[TrainingArguments]]:
        """Provides trainer components optimized for instruction fine-tuning.

        Returns:
            tuple: (TrainerClass, TrainingArgumentsClass) pair to be used for training.
            Must be implemented by subclasses.
        """
        return SFTTrainer, TrainingArguments

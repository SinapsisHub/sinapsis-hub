from unsloth import FastLanguageModel

from sinapsis_unsloth.helpers.env_var_keys import HF_TOKEN
from sinapsis_unsloth.helpers.schemas.fine_tuning import (
    DatasetConfig,
    UnslothLoraArgs,
    UnslothTrainerArgs,
    UnslothTrainingArgs,
)
from sinapsis_unsloth.templates.unsloth_base import UnslothBase, UnslothBaseAttributes

from abc import abstractmethod

from datasets import load_dataset
from pydantic import Field
from sinapsis.data_transport import DataContainer
from sinapsis.template import TemplateAttributeType
from torch.utils.data import Dataset
from transformers import DataCollator, Trainer, TrainingArguments


class UnslothFineTuningBaseAttributes(UnslothBaseAttributes):
    """Base configuration attributes for Unsloth fine-tuning templates.

    Extends the base Unsloth attributes with parameters specific to model fine-tuning.

    Attributes:
        lora_args (UnslothLoraArgs): Configuration for LoRA adapter initialization (rank, alpha, etc).
        trainer_args (UnslothTrainerArgs): Unsloth-specific trainer arguments (packing, text field).
        training_args (UnslothTrainingArgs): Hugging Face training arguments (batch size, learning rate).
        train_dataset (DatasetConfig): Consolidated configuration for the training dataset.
            Includes loader arguments, shuffling settings, pre-tokenization options, and mapping kwargs.
        resume_from_checkpoint (bool): Whether to resume training from the last checkpoint.
            Defaults to False.
        save_path (str): Path where the fine-tuned LoRA adapters will be saved.
    """

    lora_args: UnslothLoraArgs = Field(default_factory=UnslothLoraArgs)
    trainer_args: UnslothTrainerArgs = Field(default_factory=UnslothTrainerArgs)
    training_args: UnslothTrainingArgs = Field(default_factory=UnslothTrainingArgs)
    train_dataset: DatasetConfig
    resume_from_checkpoint: bool = False
    save_path: str


class UnslothFineTuningBase(UnslothBase):
    """Abstract base template for fine-tuning language models with Unsloth optimization.

    Provides core functionality for LoRA-based fine-tuning of language models using the
    Unsloth framework. Subclasses must implement dataset preparation and trainer
    configuration specifics.
    """

    AttributesBaseModel = UnslothFineTuningBaseAttributes

    def __init__(self, attributes: TemplateAttributeType) -> None:
        super().__init__(attributes)
        self.model = self._apply_lora()
        self.train_dataset = self._load_dataset()
        self.data_collator = self._set_data_collator()
        self.trainer = self._set_trainer()

    def _apply_lora(self) -> FastLanguageModel:
        """Configures the base model with LoRA adapters.

        Applies Low-Rank Adaptation (LoRA) to the model according to the configured
        lora_args.

        Returns:
            FastLanguageModel: The model configured with LoRA adapters.
        """
        model = FastLanguageModel.get_peft_model(self.model, **self.attributes.lora_args.model_dump(exclude_none=True))
        return model

    @abstractmethod
    def _prepare_dataset(self, dataset: Dataset) -> Dataset:
        """Prepares the dataset for training.

        Subclasses must implement this method to perform dataset-specific processing
        such as formatting, filtering, or additional transformations.

        Args:
            dataset (Dataset): Raw dataset loaded from HuggingFace datasets.

        Returns:
            Dataset: Processed dataset ready for training. Must be implemented by subclasses.
        """

    def _load_dataset(self) -> Dataset:
        """Loads and prepares the dataset for fine-tuning.

        Returns:
            Dataset: The processed dataset ready for training.
        """
        dataset = load_dataset(
            **self.attributes.train_dataset.loader_args.model_dump(exclude_none=True), token=HF_TOKEN
        )
        dataset = self._prepare_dataset(dataset)

        if self.attributes.train_dataset.shuffle.enabled:
            dataset = dataset.shuffle(**self.attributes.train_dataset.shuffle.args.model_dump(exclude_none=True))

        if self.attributes.train_dataset.pre_tokenize.enabled:
            tokenizer = self.tokenizer
            text_field = self.attributes.trainer_args.dataset_text_field
            tokenization_args = self.attributes.train_dataset.pre_tokenize.args.model_dump(exclude_none=True)
            dataset = dataset.map(
                lambda x: tokenizer(x[text_field], **tokenization_args),
                **self.attributes.train_dataset.pre_tokenize.map_args.model_dump(exclude_none=True),
            )
        return dataset

    def _set_data_collator(self) -> DataCollator | None:
        """Configures the data collator for training.

        Returns:
            DataCollator | None: The data collator or `None` if the default collator is to be used.
        """
        return None

    @staticmethod
    @abstractmethod
    def _get_trainer_classes() -> tuple[type[Trainer], type[TrainingArguments]]:
        """Specifies the trainer components to use.

        Subclasses must implement this to return the appropriate trainer and
        training arguments classes for their specific training approach.

        Returns:
            tuple: (TrainerClass, TrainingArgumentsClass) pair to be used for training.
            Must be implemented by subclasses.
        """

    def _set_trainer(self) -> Trainer:
        """Configures and instantiates the appropriate trainer.

        Returns:
            Trainer: Configured trainer ready for fine-tuning.
        """
        trainer_class, training_args_class = self._get_trainer_classes()
        return trainer_class(
            model=self.model,
            processing_class=self.tokenizer,
            train_dataset=self.train_dataset,
            data_collator=self.data_collator,
            args=training_args_class(**self.attributes.training_args.model_dump(exclude_none=True)),
            **self.attributes.trainer_args.model_dump(exclude_none=True),
        )

    def train(self) -> None:
        """Executes the model training process.

        Runs the complete training loop and logs training statistics. Handles
        checkpoint resuming if configured.
        """
        trainer_stats = self.trainer.train(resume_from_checkpoint=self.attributes.resume_from_checkpoint)
        self.logger.info(trainer_stats)

    def save_model(self) -> None:
        """Saves the trained model to disk.

        The model is saved as LoRA adapters only.
        """
        self.model.save_pretrained(self.attributes.save_path)
        self.tokenizer.save_pretrained(self.attributes.save_path)

    def execute(self, container: DataContainer) -> DataContainer:
        """Runs the complete fine-tuning pipeline.

        Args:
            container (DataContainer): Input data container.

        Returns:
            DataContainer: The updated data container with saved path.
        """
        self.train()
        self.save_model()
        self.logger.info(f"LoRA saved to {self.attributes.save_path}")
        self._set_generic_data(container, self.attributes.save_path)
        return container

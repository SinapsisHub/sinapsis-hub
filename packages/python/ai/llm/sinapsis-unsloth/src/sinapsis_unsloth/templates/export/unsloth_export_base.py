from sinapsis_unsloth.helpers.env_var_keys import HF_TOKEN
from sinapsis_unsloth.helpers.schemas.export import UnslothExportBaseArgs
from sinapsis_unsloth.templates.unsloth_base import UnslothBase, UnslothBaseAttributes

from abc import abstractmethod

from sinapsis.data_transport import DataContainer
from sinapsis.template import TemplateAttributeType


class UnslothExportBaseAttributes(UnslothBaseAttributes):
    """Base configuration parameters for model export operations.

    Extends the base Unsloth attributes with export-specific parameters.

    Attributes:
        export_args (UnslothExportBaseArgs): Arguments required for the export process.
        push_to_hub (bool, optional): If True, the model will be pushed to the HF Hub. Defaults to False.
    """

    export_args: UnslothExportBaseArgs
    push_to_hub: bool = False


class UnslothExportBase(UnslothBase):
    """Base template for exporting models with Unsloth.

    Provides base functionality to export Unsloth-optimized models either locally or to the Hugging Face Hub. Subclasses
    must override the `set_export_method` method with the adequate logic to define the export method to use.
    """

    AttributesBaseModel = UnslothExportBaseAttributes

    def __init__(self, attributes: TemplateAttributeType) -> None:
        super().__init__(attributes)
        self.export_method = self.set_export_method()

    @abstractmethod
    def set_export_method(self) -> str:
        """Sets the export method for the model.

        Returns:
            str: The export method to be used to export the model.
        """

    def export_model(self) -> None:
        """Executes the model export according to the configured method.

        Uses reflection to call the appropriate save method on the model instance.
        """
        save_method = getattr(self.model, self.export_method)
        save_method(
            self.attributes.export_args.save_path,
            self.tokenizer,
            **self.attributes.export_args.model_dump(exclude={"save_path"}),
            token=HF_TOKEN,
        )

    def execute(self, container: DataContainer) -> DataContainer:
        """Executes the model export pipeline.

        Performs the model export operation and updates the data container with
        the export path information.

        Args:
            container (DataContainer): Input data container.

        Returns:
            DataContainer: The updated data container with export path.
        """
        self.export_model()
        self.logger.info(f"Exported model saved to {self.attributes.export_args.save_path}")
        self._set_generic_data(container, self.attributes.export_args.save_path)
        return container

from unsloth import FastLanguageModel

from sinapsis_unsloth.helpers.env_var_keys import HF_TOKEN
from sinapsis_unsloth.helpers.schemas.base import ChatTemplatePatterns, UnslothModelArgs

from sinapsis.template import OutputTypes, Template, TemplateAttributes, TemplateAttributeType, UIPropertiesMetadata
from transformers import PreTrainedTokenizer


class UnslothBaseAttributes(TemplateAttributes):
    """Configuration attributes for Unsloth-based language model templates.

    Defines the core parameters needed to initialize and configure an Unsloth-optimized
    language model.

    Attributes:
        model_args (UnslothModelArgs): Configuration arguments for loading the Unsloth
            model, including model name, quantization settings (4-bit/8-bit), precision
            (dtype), and caching options.
    """

    model_args: UnslothModelArgs


class UnslothBase(Template):
    """Base template for Unsloth-optimized language model operations.

    Provides core functionality shared across both training and inference templates using
    Unsloth's optimized implementations. Handles model loading, configuration, and
    provides utilities for working with different chat template formats.
    """

    AttributesBaseModel = UnslothBaseAttributes
    PATTERNS = ChatTemplatePatterns()
    UIProperties = UIPropertiesMetadata(category="Unsloth", output_type=OutputTypes.TEXT)

    def __init__(self, attributes: TemplateAttributeType) -> None:
        super().__init__(attributes)
        self.model, self.tokenizer = self._load_model()

    def _load_model(self) -> tuple[FastLanguageModel, PreTrainedTokenizer]:
        """Loads and initializes the Unsloth model and tokenizer.

        Uses the configured attributes to load the specified model with the requested
        precision settings and any additional loading arguments.

        Returns:
            tuple[FastLanguageModel, PreTrainedTokenizer]: The initialized model and tokenizer.
        """
        return FastLanguageModel.from_pretrained(token=HF_TOKEN, **self.attributes.model_args.model_dump())

    @staticmethod
    def normalize_template_name(name: str) -> str:
        """Normalizes chat template names to valid Python attribute format.

        Converts the input string to lowercase and replaces special characters with
        underscores to create a consistent naming scheme for template references.

        Args:
            name (str): Chat template name to normalize

        Returns:
            str: Normalized name with special characters replaced
        """
        return name.lower().replace("-", "_").replace(".", "_").replace(" ", "_")

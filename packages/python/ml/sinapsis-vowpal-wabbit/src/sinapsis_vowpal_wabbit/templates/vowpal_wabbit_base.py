from abc import abstractmethod

from sinapsis.template import Template, TemplateAttributes, TemplateAttributeType
from vowpalwabbit import pyvw

from sinapsis_vowpal_wabbit.templates.base_models import DEFAULT_STOP_WORDS


class VowpalWabbitBaseAttributes(TemplateAttributes):
    """Attributes configuration class for Vowpal Wabbit template.

    This class extends TemplateAttributes and provides default configuration
    for text preprocessing in Vowpal Wabbit models.

    Attributes:
        stop_words (list): A list of stop words to be filtered during text processing.
            Defaults to DEFAULT_STOP_WORDS.
        clean_text_pattern (str): A regular expression pattern used to clean and normalize
            text by removing unwanted characters. Defaults to a pattern that removes all
            characters except lowercase letters, digits, and whitespace.
    """

    stop_words: list = DEFAULT_STOP_WORDS
    clean_text_pattern: str = r"[^a-z0-9\s]"
    random_seed: int | None = None


class VowpalWabbitBase(Template):
    """Base class for Vowpal Wabbit templates."""

    def __init__(self, attributes: TemplateAttributeType) -> None:
        super().__init__(attributes)
        self.initialize_vw_workspace()

    def initialize_vw_workspace(self) -> None:
        """Initialize the Vowpal Wabbit workspace with the built configuration.

        This method constructs the Vowpal Wabbit configuration and creates a new
        Workspace instance that will be used for model training and predictions.

        Raises:
            Exception: If the workspace initialization fails due to invalid configuration
                or Vowpal Wabbit runtime errors.
        """
        config = self._build_vw_config()
        self.vw = pyvw.Workspace(config)

    @abstractmethod
    def _build_vw_config(self) -> str:
        """Build the Vowpal Wabbit configuration string.

        This abstract method must be implemented by subclasses to construct
        the appropriate configuration parameters for Vowpal Wabbit.

        Returns:
            str: The Vowpal Wabbit configuration string.
        """

    @abstractmethod
    def get_vw_format(
        self,
        user_text: str,
        actions: list[str],
        chosen_action_idx: int | None = None,
        cost: float | None = None,
        prob: float | None = None,
    ) -> str:
        """Convert user text and action data into Vowpal Wabbit format.

        Args:
            user_text (str): The input text from the user.
            actions (list): A list of available actions to choose from.
            chosen_action_idx (int, optional): The index of the chosen action. Defaults to None.
            cost (float, optional): The cost associated with the chosen action. Defaults to None.
            prob (float, optional): The probability of selecting the chosen action. Defaults to None.

        Returns:
            str: A string formatted according to Vowpal Wabbit's input specification.
        """

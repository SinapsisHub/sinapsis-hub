import re
from typing import Literal, cast

from pydantic import Field, model_validator
from sinapsis.template import TemplateAttributeType

from sinapsis_vowpal_wabbit.templates.base_models import VWWorkspaceParams
from sinapsis_vowpal_wabbit.templates.vowpal_wabbit_base import VowpalWabbitBase, VowpalWabbitBaseAttributes


class CBExploreADFWorkspaceParams(VWWorkspaceParams):
    """Workspace parameters for Contextual Bandit exploration with Action Dependent Features (ADF).

    This class configures the exploration strategy and related settings for a Vowpal Wabbit
    contextual bandit model using the ADF approach.

    Attributes:
        exploration_method: The exploration strategy to use. Options are:
            - "first": Explores the first action
            - "epsilon": Epsilon-greedy exploration
            - "bag": Bagging/bootstrap exploration
            - "softmax": Softmax exploration with temperature parameter
            Defaults to "epsilon".
        exploration_value: The value parameter for the chosen exploration method.
            - For "first" and "bag": Must be an integer (e.g., number of actions to explore)
            - For "epsilon": Must be a float between 0.0 and 1.0 (exploration probability)
            - For "softmax": Must be a float (lambda/temperature parameter)
            Defaults to 0.2.
        adaptive: Whether to use adaptive exploration. Defaults to True.
        normalized: Whether to use normalized weights. Defaults to True.
        quiet: Whether to suppress output. Defaults to False.

    Raises:
        ValueError: If exploration_value is inconsistent with exploration_method:
            - If method is "first" or "bag" but value is not an integer
            - If method is "epsilon" but value is not a float or outside [0.0, 1.0]

    Properties:
        vw_exploration_string: Generates the corresponding Vowpal Wabbit command line
            arguments for the configured exploration method and value.
    """

    exploration_method: Literal["first", "epsilon", "bag", "softmax"] = "epsilon"
    exploration_value: int | float = 0.2
    adaptive: bool = True
    normalized: bool = True
    quiet: bool = False

    @model_validator(mode="after")
    def validate_exploration_consistency(self) -> "CBExploreADFBaseAttributes":
        """Validate that the exploration method and value are consistent."""
        method = self.exploration_method
        value = self.exploration_value

        match method:
            case "first" | "bag":
                if not isinstance(value, int):
                    raise ValueError(f"'{method}' requires an integer (e.g., 10)")

            case "epsilon":
                if not (0.0 <= value <= 1.0):
                    raise ValueError(f"Epsilon must be between 0 and 1, got {value}")

        return cast(CBExploreADFBaseAttributes, self)

    @property
    def vw_exploration_string(self) -> str:
        """Converts the internal attributes to VW command line arguments."""
        method = self.exploration_method
        value = self.exploration_value

        if method == "first":
            return f"--first {value}"

        if method == "epsilon":
            return f"--epsilon {value}"

        if method == "bag":
            return f"--bag {value}"

        if method == "softmax":
            return f"--softmax --lambda {value}"

        return ""


class CBExploreADFBaseAttributes(VowpalWabbitBaseAttributes):
    """A Pydantic model class for contextual bandit explore-adf base attributes.

    This class extends VowpalWabbitBaseAttributes and defines the configuration
    parameters for Vowpal Wabbit's contextual bandit exploration with action-dependent
    features (ADF) learning algorithm.

    Attributes:
        actions (list[str]): List of available actions for the contextual bandit.
        vw_workspace_params (CBExploreADFWorkspaceParams): Workspace parameters specific
            to the CB explore-adf algorithm. Defaults to an empty CBExploreADFWorkspaceParams
            instance if not provided or if an empty dict is passed.
        remove_stop_words (bool): Flag indicating whether to remove stop words from text.
            Defaults to False.
        remove_special_characters (bool): Flag indicating whether to remove special
            characters from text. Defaults to True.

    Methods:
        initialize_empty_params(): Post-initialization validator that converts an empty
            dictionary to a CBExploreADFWorkspaceParams instance for vw_workspace_params.
    """

    actions: list[str]
    vw_workspace_params: CBExploreADFWorkspaceParams = Field(default_factory=CBExploreADFWorkspaceParams)
    remove_stop_words: bool = False
    remove_special_characters: bool = True


class CBExploreADFBase(VowpalWabbitBase):
    """Base template for Vowpal Wabbit CB Explore ADF approach."""

    AttributesBaseModel = CBExploreADFBaseAttributes
    attributes: CBExploreADFBaseAttributes

    def __init__(self, attributes: TemplateAttributeType) -> None:
        super().__init__(attributes)

    def _build_vw_config(self) -> str:
        """Build a Vowpal Wabbit configuration string from workspace parameters.

        Constructs a command-line configuration string for Vowpal Wabbit by combining
        various parameters including exploration strategy, bit precision, regularization,
        feature interactions, and other training options.

        Returns:
            str: A space-separated string of Vowpal Wabbit command-line arguments
                 configured based on the instance's workspace parameters.
        """
        attr = self.attributes.vw_workspace_params
        config_parts = ["--cb_explore_adf", f"{attr.vw_exploration_string}", f"-b {attr.bit_precision}"]

        if attr.adaptive:
            config_parts.append("--adaptive")

        if attr.normalized:
            config_parts.append("--normalized")

        config_parts.extend(f"-q {q}" for q in attr.quadratic_interactions)
        config_parts.extend(f"--cubic {c}" for c in attr.cubic_interactions)

        config_parts.extend(f"--ngram {ns}{attr.ngram_size}" for ns in attr.ngram_namespaces)

        if attr.learning_rate is not None:
            config_parts.append(f"-l {attr.learning_rate}")

        if attr.l1 > 0:
            config_parts.append(f"--l1 {attr.l1}")
        if attr.l2 > 0:
            config_parts.append(f"--l2 {attr.l2}")

        if self.attributes.random_seed is not None:
            config_parts.append(f"--random_seed {self.attributes.random_seed}")

        if attr.quiet:
            config_parts.append("--quiet")

        return " ".join(config_parts)

    def get_vw_format(
        self,
        user_text: str,
        actions: list[str],
        chosen_action_idx: int | None = None,
        cost: float | None = None,
        prob: float | None = None,
    ) -> str:
        r"""Format user text and actions into Vowpal Wabbit contextual bandit explore-adf format.

        This method constructs a VW format string for contextual bandit learning with
        action-dependent features (adf). It includes a shared context feature and
        individual action features, with optional reward information for the chosen action.

        Args:
            user_text (str): The user input text to be used as shared context.
            actions (list): List of action strings to be formatted as features.
            chosen_action_idx (int, optional): Index of the chosen action in the actions list.
                If provided, this action will include cost and probability information.
                Defaults to None.
            cost (float, optional): The cost/reward associated with the chosen action.
                Only used if chosen_action_idx is provided. Defaults to None.
            prob (float, optional): The probability of selecting the chosen action.
                Only used if chosen_action_idx is provided. Defaults to None.

        Returns:
            str: A formatted Vowpal Wabbit example string with shared context and actions.
                Format: "shared |C <cleaned_text>\n" followed by action lines.
                The chosen action line includes cost and probability: "<idx>:<cost>:<prob> |A <action>"
                Other actions follow format: "|A <action>"
        """
        clean_text = user_text.replace("|", "").replace(":", "")
        clean_text = self.clean_text(clean_text)
        example_str = f"shared |C {clean_text}\n"

        for i, action in enumerate(actions):
            if i == chosen_action_idx:
                example_str += f"{i}:{cost}:{prob} |A {action}\n"
            else:
                example_str += f"|A {action}\n"
        return example_str.strip()

    def clean_text(self, text: str) -> str:
        """Clean and normalize text by removing special characters and/or stop words.

        This method processes input text based on the configured attributes. It can
        optionally remove special characters (converting to lowercase) and filter out
        common stop words.

        Args:
            text (str): The input text to be cleaned.

        Returns:
            str: The cleaned text with special characters and/or stop words removed
                 based on the configuration settings.

        """
        if self.attributes.remove_special_characters:
            text = re.sub(self.attributes.clean_text_pattern, " ", text.lower())

        if self.attributes.remove_stop_words:
            words = text.split()
            filtered = [w for w in words if w not in self.attributes.stop_words]
            return " ".join(filtered)
        return text

    def _shut_down(self) -> None:
        self.vw.finish()

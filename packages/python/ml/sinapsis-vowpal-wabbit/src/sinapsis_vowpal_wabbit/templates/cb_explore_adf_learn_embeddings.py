from pydantic import Field
from sentence_transformers import SentenceTransformer
from sinapsis.template import TemplateAttributeType

from sinapsis_vowpal_wabbit.templates.base_models import SentenceTransformerParams
from sinapsis_vowpal_wabbit.templates.cb_explore_adf_learn import CBExploreADFLearn, CBExploreADFLearnAttributes


class CBExploreADFLearnEmbeddingsAttributes(CBExploreADFLearnAttributes):
    """Attributes for Contextual Bandit exploration with Action Dependent Features (ADF) in learning mode.

    This class extends CBExploreADFLearnAttributes with additional configuration parameters
    required for training a Vowpal Wabbit model using the CB explore ADF algorithm.

    Attributes:
        epochs (int): Number of training epochs. Defaults to 5.
        instruction_column (str): Name of the column containing instructions or features.
        true_action_column (str): Name of the column containing the true/correct actions.
        split_dataset (bool): Whether to split the dataset into train and test sets. Defaults to True.
        train_test_split_params (TrainTestSplitParams): Parameters for train-test split configuration.
            Defaults to an empty dictionary via factory.
        root_dir (str): Root directory path for model storage.
        save_path (str): Relative path within root_dir where the model will be saved.
        full_save_path (str): Computed property that combines root_dir and save_path
            into a single absolute file system path.
        sentence_transformer_params (SentenceTransformerParams): Configuration parameters for the
            SentenceTransformer model used to generate embeddings from text. Defaults to an empty
            SentenceTransformerParams instance if not provided or if an empty dict is passed.
    """

    sentence_transformer_params: SentenceTransformerParams = Field(default_factory=SentenceTransformerParams)


class CBExploreADFLearnEmbeddings(CBExploreADFLearn):
    """Template to perform action learning using the Vowpal Wabbit CB_Explore_ADF approach.

    Uses text instructions and action labels, enhanced with sentence embeddings.

    Attributes:
        actions (list[str]): List of available actions for the contextual bandit.
        vw_workspace_params (CBExploreADFWorkspaceParams): Workspace parameters specific
            to the CB explore-adf algorithm. Defaults to an empty CBExploreADFWorkspaceParams
            instance if not provided or if an empty dict is passed.
        remove_stop_words (bool): Flag indicating whether to remove stop words from text.
            Defaults to False.
        remove_special_characters (bool): Flag indicating whether to remove special
            characters from text. Defaults to True.
        epochs (int): Number of training epochs. Defaults to 5.
        instruction_column (str): Name of the column containing instructions or features.
        true_action_column (str): Name of the column containing the true/correct actions.
        split_dataset (bool): Whether to split the dataset into train and test sets. Defaults to True.
        train_test_split_params (TrainTestSplitParams): Parameters for train-test split configuration.
            Defaults to an empty dictionary via factory.
        root_dir (str): Root directory path for model storage.
        save_path (str): Relative path within root_dir where the model will be saved.
        full_save_path (str): Computed property that combines root_dir and save_path
            into a single absolute file system path.
        sentence_transformer_params (SentenceTransformerParams): Configuration parameters for the
            SentenceTransformer model used to generate embeddings from text. Defaults to an empty
            SentenceTransformerParams instance if not provided or if an empty dict is passed.


    """

    AttributesBaseModel = CBExploreADFLearnEmbeddingsAttributes
    attributes: CBExploreADFLearnEmbeddingsAttributes

    def __init__(self, attributes: TemplateAttributeType) -> None:
        super().__init__(attributes)

        self.embedding_model: SentenceTransformer = SentenceTransformer(
            self.attributes.sentence_transformer_params.model_name,
            device=self.attributes.sentence_transformer_params.device,
        )

    def get_vw_format(
        self,
        user_text: str,
        actions: list[str],
        chosen_action_idx: int | None = None,
        cost: float | None = None,
        prob: float | None = None,
    ) -> str:
        """Converts user text and actions into the Vowpal Wabbit input format, including sentence embeddings.

        Arguments:
            user_text (str): The input text or instruction from the user.
            actions (list[str]): List of possible actions for the contextual bandit.
            chosen_action_idx (int | None): Index of the action that was chosen (if any). Defaults to None.
            cost (float | None): The cost associated with the chosen action (if any). Defaults to None.
            prob (float | None): The probability of the chosen action (if any). Defaults to None.

        Returns:
            str: A string formatted according to Vowpal Wabbit's expected input,
                including both raw text features and their corresponding sentence embeddings.
        """
        encode_attrs = self.attributes.sentence_transformer_params

        user_query_embedding = self.embedding_model.encode(
            user_text,
            batch_size=encode_attrs.batch_size,
            precision=encode_attrs.precision,
            normalize_embeddings=encode_attrs.normalize_embeddings,
        ).tolist()
        embed_features = " ".join([f"{i}:{val}" for i, val in enumerate(user_query_embedding)])
        raw_text_features = user_text.lower().replace("|", "").replace(":", "")
        example_str = f"shared |E {embed_features} |C {raw_text_features}\n"

        for i, action in enumerate(actions):
            if chosen_action_idx is not None and i == chosen_action_idx:
                label = f"{chosen_action_idx}:{cost}:{prob} "
            else:
                label = ""

            action_label = action.replace(" ", "_")
            example_str += f"{label}|A {action_label}\n"

        return example_str

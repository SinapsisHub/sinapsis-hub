from pydantic import Field
from sentence_transformers import SentenceTransformer
from sinapsis.template import TemplateAttributeType

from sinapsis_vowpal_wabbit.templates.base_models import SentenceTransformerParams
from sinapsis_vowpal_wabbit.templates.cb_explore_adf_predict import CBExploreADFPredict, CBExploreADFPredictAttributes


class CBExploreADFPredictEmbeddingsAttributes(CBExploreADFPredictAttributes):
    """Attributes for contextual bandit exploration with action-dependent features prediction.

    This class extends CBExploreADFPPredictAttributes to define specific configuration
    parameters for the prediction phase of a contextual bandit model using
    action-dependent features (ADF).

    Attributes:
        actions (list[str]): List of available action identifiers or labels that
            the model can predict or explore.
        vw_workspace_params (CBExploreADFWorkspaceParams): Workspace parameters specific
            to the CB explore-adf algorithm. Defaults to an empty CBExploreADFWorkspaceParams
            instance if not provided or if an empty dict is passed.
        remove_stop_words (bool): Flag indicating whether to remove stop words from text.
            Defaults to False.
        remove_special_characters (bool): Flag indicating whether to remove special
            characters from text. Defaults to True.
        model_path (str): File system path to the trained Vowpal Wabbit model
            that will be used for making predictions.
        inference_only (bool): Flag to determine the operation mode. When True,
            the model operates in inference-only mode without updates or learning.
            Defaults to True.
        threshold (float): Minimum confidence or score threshold for predictions.
            Predictions below this threshold may be filtered or handled differently.
            Defaults to 0.
        top_k (int): Number of top-ranked predictions or actions to return or consider
            in the output. Defaults to 3.
        sentence_transformer_params (SentenceTransformerParams): Configuration parameters for the
            SentenceTransformer model used to generate embeddings from text. Defaults to an empty
            SentenceTransformerParams instance if not provided or if an empty dict is passed.

    """

    sentence_transformer_params: SentenceTransformerParams = Field(default_factory=SentenceTransformerParams)


class CBExploreADFPredictEmbeddings(CBExploreADFPredict):
    """Template to perform action predictions using the Vowpal Wabbit CB_Explore_ADF approach.

    Uses text instructions, enhanced with sentence embeddings.

    Attributes:
        actions (list[str]): List of available action identifiers or labels that
            the model can predict or explore.
        model_path (str): File system path to the trained Vowpal Wabbit model
            that will be used for making predictions.
        inference_only (bool): Flag to determine the operation mode. When True,
            the model operates in inference-only mode without updates or learning.
            Defaults to True.
        threshold (float): Minimum confidence or score threshold for predictions.
            Predictions below this threshold may be filtered or handled differently.
            Defaults to 0.
        top_k (int): Number of top-ranked predictions or actions to return or consider
            in the output. Defaults to 3.
        sentence_transformer_params (SentenceTransformerParams): Configuration parameters for the
            SentenceTransformer model used to generate embeddings from text. Defaults to an empty
            SentenceTransformerParams instance if not provided or if an empty dict is passed.
    """

    AttributesBaseModel = CBExploreADFPredictEmbeddingsAttributes
    attributes: CBExploreADFPredictEmbeddingsAttributes

    def __init__(self, attributes: TemplateAttributeType) -> None:
        super().__init__(attributes)
        self.embedding_model: SentenceTransformer = SentenceTransformer(
            self.attributes.sentence_transformer_params.model_name
        )

    def get_vw_format(
        self,
        user_text: str,
        actions: list[str],
        chosen_action_idx: int | None = None,
        cost: float | None = None,
        prob: float | None = None,
    ) -> str:
        """Convert user text and actions into Vowpal Wabbit format with sentence embeddings."""
        encode_attrs = self.attributes.sentence_transformer_params

        user_query_embedding = self.embedding_model.encode(
            user_text,
            batch_size=encode_attrs.batch_size,
            precision=encode_attrs.precision,
            normalize_embeddings=encode_attrs.normalize_embeddings,
        ).tolist()
        embed_features = " ".join([f"{i}:{val}" for i, val in enumerate(user_query_embedding)])
        raw_text_features = user_text.lower().replace("|", "").replace(":", "").replace("\n", " ")
        raw_text_features = self.clean_text(raw_text_features).strip()
        raw_text_features = " ".join(raw_text_features.split())

        example_str = f"shared |E {embed_features} |C {raw_text_features}\n"

        for i, action in enumerate(actions):
            if chosen_action_idx is not None and i == chosen_action_idx:
                label = f"{chosen_action_idx}:{cost}:{prob} "
            else:
                label = ""

            action_label = action.replace(" ", "_")
            example_str += f"{label}|A {action_label}\n"

        return example_str

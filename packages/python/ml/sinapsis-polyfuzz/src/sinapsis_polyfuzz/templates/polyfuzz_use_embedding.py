import tensorflow_hub
from polyfuzz.models import USEEmbeddings
from pydantic import BaseModel
from sinapsis.template import TemplateAttributeType

from sinapsis_polyfuzz.templates.polyfuzz_base import PolyfuzzBase, PolyfuzzBaseAttributes


class USEEmbeddingsInit(BaseModel):
    """Configuration for initializing Universal Sentence Encoder (USE) embeddings.

    Attributes:
        embedding_model (str): The URL or local path to the Universal Sentence Encoder model. Defaults to
            "https://tfhub.dev/google/universal-sentence-encoder/4".
        min_similarity (float): The minimum similarity score threshold for filtering results. Defaults to 0.75.
        top_n (int): The number of most similar results to retrieve. Defaults to 1.
        cosine_method (str): The method used to calculate cosine similarity (e.g., "sparse"). Defaults to "sparse".
        model_id (str, optional): A unique identifier for the model instance. Defaults to None.
    """

    embedding_model: str = "https://tfhub.dev/google/universal-sentence-encoder/4"
    min_similarity: float = 0.75
    top_n: int = 1
    cosine_method: str = "sparse"
    model_id: str | None = None


class USEEmbeddingsWrapper(PolyfuzzBase):
    """Static template for Universal Sentence Encoder (USE) embeddings."""

    class AttributesBaseModel(PolyfuzzBaseAttributes):
        """Base model for Polyfuzz attributes focusing on embedding initialization.

        Attributes:
            useembeddings_init (USEEmbeddingsInit): The initialization configuration or
                instance for Universal Sentence Encoder (USE) embeddings.
        """

        useembeddings_init: USEEmbeddingsInit

    def __init__(self, attributes: TemplateAttributeType) -> None:
        super().__init__(attributes)
        embedding_model = tensorflow_hub.load(self.attributes.useembeddings_init.embedding_model)
        self.wrapped_callable = USEEmbeddings(
            embedding_model,
            **self.attributes.useembeddings_init.model_dump(exclude={"embedding_model"}),
        )

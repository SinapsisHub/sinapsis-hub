import gc
import io
import time
import uuid
from abc import abstractmethod
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from plotly import graph_objects as go
from pydantic import Field
from sentence_transformers import SentenceTransformer
from sinapsis.data_transport import DataContainer, ImagePacket
from sinapsis.env_vars import SINAPSIS_CACHE_DIR
from sinapsis.template import OutputTypes, Template, TemplateAttributes, UIPropertiesMetadata

from sinapsis_bertopic.helpers.tags import Tags
from sinapsis_bertopic.templates.base_models.base_attrs import ToImageParams


class BERTopicBaseAttributes(TemplateAttributes):
    """Base attributes configuration for BERTopic template.

    This class defines the core configuration parameters for BERTopic model initialization
    and behavior, including caching, visualization export, and sentence embedding settings.

    Attributes:
        root_dir (str): Root directory path for caching BERTopic-related files and models.
            Defaults to SINAPSIS_CACHE_DIR.
        export_visualization_to_image (bool): Flag to enable exporting topic visualizations
            to image files. Defaults to True.
        image_export_params (ToImageParams): Parameters for configuring image export behavior
            and formatting options. Defaults to a new ToImageParams instance.
        sentence_model_name (str): Name or path of the sentence transformer model to use
            for embedding generation. Defaults to "sentence-transformers/all-MiniLM-L6-v2".
    """

    root_dir: str = SINAPSIS_CACHE_DIR
    export_visualization_to_image: bool = True
    image_export_params: ToImageParams = Field(default_factory=ToImageParams)
    sentence_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"


class BERTopicBase(Template):
    """Base class for BERTopic templates, providing common functionality for topic modeling and visualization."""

    AttributesBaseModel = BERTopicBaseAttributes
    attributes: BERTopicBaseAttributes

    UIProperties = UIPropertiesMetadata(
        category="BERTopic",
        output_type=OutputTypes.MULTIMODAL,
        tags=[
            Tags.BERTOPIC.value,
            Tags.TOPIC_MODELING.value,
            Tags.VISUALIZATION.value,
            Tags.NLP.value,
            Tags.EMBEDDINGS.value,
            Tags.CLUSTERING.value,
        ],
    )

    def __init__(self, attributes: TemplateAttributes) -> None:
        super().__init__(attributes)
        self.topic_model = None
        self.sentence_transformer_model = None
        self.initialize_bertopic_model()
        self.initialize_sentence_transformer_model()

    @abstractmethod
    def initialize_bertopic_model(self) -> None:
        """Initializes and configures the BERTopic model."""

    def initialize_sentence_transformer_model(self) -> None:
        """Initializes the sentence transformer model for embedding inference."""
        self.sentence_transformer_model = SentenceTransformer(self.attributes.sentence_model_name)

    @staticmethod
    def clear_memory() -> None:
        """Clears memory to free up resources.

        This method performs garbage collection and clears GPU memory (if applicable) to prevent memory leaks
        and ensure efficient resource usage.
        """
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def reset_state(self, template_name: str | None = None) -> None:
        """Releases the pipeline and processor from memory and re-instantiates the template.

        Args:
            template_name (str | None, optional): The name of the template instance being reset. Defaults to None.
        """
        _ = template_name

        if hasattr(self, "topic_model") and self.topic_model is not None:
            del self.topic_model

        if hasattr(self, "sentence_transformer_model") and self.sentence_transformer_model is not None:
            del self.sentence_transformer_model

        self.clear_memory()
        self.initialize_bertopic_model()
        self.initialize_sentence_transformer_model()
        self.logger.info(f"Reset template instance `{self.instance_name}`")

    def infer_embeddings(self, docs: list[str]) -> np.ndarray:
        """Infers embeddings for a list of documents using the sentence transformer model.

        Args:
            docs (list[str]): A list of document strings for which to infer embeddings.

        Returns:
            np.ndarray: A numpy array containing the inferred embeddings for the input documents.
        """
        if self.sentence_transformer_model is None:
            raise AttributeError("Sentence transformer model not initialized")
        return self.sentence_transformer_model.encode(docs, show_progress_bar=True)

    def save_figure_to_html(self, fig: go.Figure, save_path: str) -> None:
        """Save visualization figure to an HTML file.

        Args:
            fig: (go.Figure) Plotly graph object Figure containing the topics visualization.
            save_path: (str) Path to save the HTML file.
        """
        if not Path(self.attributes.root_dir).exists():
            self.logger.info(f"Creating root directory at {self.attributes.root_dir} for saving visualizations.")
            Path(self.attributes.root_dir).mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Saving visualization figure to HTML file at {save_path}.")
        fig.write_html(save_path)

    def convert_figure_to_image_array(self, fig: go.Figure) -> np.ndarray:
        """Convert a Plotly figure to a numpy array image.

        This method takes a Plotly graph object figure and converts it to a numpy
        array representation by first exporting it as image bytes, then reading
        those bytes into a PIL Image and converting to a numpy array.

        Args:
            fig (graph_objects.Figure): A Plotly figure object to be converted.

        Returns:
            np.ndarray: A numpy array representing the image data of the figure.
        """
        image_bytes = fig.to_image(**self.attributes.image_export_params.model_dump(by_alias=True))
        return np.array(Image.open(io.BytesIO(image_bytes)))

    def append_img_array_to_container(self, img_arr: np.ndarray, container: DataContainer) -> None:
        """Append an image array to a data container as an ImagePacket.

        Args:
            img_arr (np.ndarray): The image array to be appended to the container.
            container (DataContainer): The data container where the image packet will be stored.

        Returns:
            None
        """
        source = f"{self.instance_name}_{int(time.time())!s}_{uuid.uuid4()!s}"

        container.images.append(ImagePacket(content=img_arr, source=source))

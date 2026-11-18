import pickle
from pathlib import Path
from typing import cast

import numpy as np
from bertopic import BERTopic
from bertopic._save_utils import (
    CONFIG_NAME,
    CTFIDF_CFG_NAME,
    CTFIDF_SAFE_WEIGHTS_NAME,
    CTFIDF_WEIGHTS_NAME,
    HF_SAFE_WEIGHTS_NAME,
    HF_WEIGHTS_NAME,
    TOPICS_NAME,
)
from bertopic.vectorizers import ClassTfidfTransformer
from hdbscan import HDBSCAN
from plotly import graph_objects
from pydantic import Field
from sentence_transformers import SentenceTransformer
from sinapsis.data_transport import DataContainer, FilePacket
from sinapsis.env_vars import SINAPSIS_CACHE_DIR
from sinapsis.template import TemplateAttributes
from umap import UMAP

from sinapsis_bertopic.helpers.bertopic_helpers import get_docs_from_text_packets
from sinapsis_bertopic.templates.base_models.base_attrs import (
    BERTopicModelParams,
    BERTopicSaveModelParams,
    CTFIDFModelParams,
    HDBSCANModelParams,
    ToImageParams,
    UMAPModelParams,
    VisualizeDocumentsParams,
)
from sinapsis_bertopic.templates.bertopic_base import BERTopicBase, BERTopicBaseAttributes


class BERTopicFitModelAttributes(BERTopicBaseAttributes):
    """Attributes configuration class for BERTopic model fitting operations.

    This class extends BERTopicBaseAttributes and defines all parameters required for
    fitting and saving a BERTopic model, including model persistence, visualization
    export, and training data management.

    Attributes:
        bertopic_model_params (BERTopicModelParams): Configuration parameters for the
            BERTopic model. Defaults to an empty dictionary which is converted to a
            BERTopicModelParams instance during validation.
        umap_model_params (UMAPModelParams): Configuration parameters for the UMAP
            dimensionality reduction model. Defaults to an empty dictionary which is
            converted to a UMAPModelParams instance during validation.
        hdbscan_model_params (HDBSCANModelParams): Configuration parameters for the
            HDBSCAN clustering model. Defaults to an empty dictionary which is
            converted to a HDBSCANModelParams instance during validation.
        bertopic_save_model_params (BERTopicSaveModelParams): Parameters for saving
            the BERTopic model. Defaults to BERTopicSaveModelParams().
        ctfidf_model_params (CTFIDFModelParams): Configuration parameters for the
            ClassTfidfTransformer model used in BERTopic. Defaults to CTFIDFModelParams().
        export_visualization_to_image (bool): Whether to export visualizations as
            image files. Defaults to True.
        image_export_params (ToImageParams): Parameters for image export configuration.
            Defaults to ToImageParams().
        root_dir (str): Root directory for storing model and visualization files.
            Defaults to SINAPSIS_CACHE_DIR.
        save_documents_visualization_path (str): Relative path for saving documents
            visualization HTML file. Defaults to "documents_visualization.html".
        save_model_path (str): Relative path for saving the BERTopic model.
        save_training_data (bool): Whether to save training data to disk.
            Defaults to False.
        save_training_data_path (str): Relative path for saving training data pickle
            file. Defaults to "training_data.pkl".
        sentence_model_name (str): Identifier for the sentence transformer model.
            Defaults to "sentence-transformers/all-MiniLM-L6-v2".
        visualize_documents_params (VisualizeDocumentsParams): Parameters for document
            visualization. Defaults to VisualizeDocumentsParams().

    Properties:
        full_visualization_path (str): Absolute path to the documents visualization file.
        full_training_data_path (str): Absolute path to the training data file.
        full_save_model_path (str): Absolute path to the saved model file.
    """

    bertopic_model_params: BERTopicModelParams = Field(default_factory=BERTopicModelParams)
    bertopic_save_model_params: BERTopicSaveModelParams = Field(default_factory=BERTopicSaveModelParams)
    ctfidf_model_params: CTFIDFModelParams = Field(default_factory=CTFIDFModelParams)
    export_visualization_to_image: bool = True
    hdbscan_model_params: HDBSCANModelParams = Field(default_factory=HDBSCANModelParams)
    image_export_params: ToImageParams = Field(default_factory=ToImageParams)

    root_dir: str = SINAPSIS_CACHE_DIR
    save_documents_visualization_path: str = "documents_visualization.html"
    save_model_path: str = "bertopic_model"
    save_training_data: bool = False
    save_training_data_path: str = "training_data.pkl"

    umap_model_params: UMAPModelParams = Field(default_factory=UMAPModelParams)

    visualize_documents_params: VisualizeDocumentsParams = Field(default_factory=VisualizeDocumentsParams)

    @property
    def full_visualization_path(self) -> str:
        """Combines root_dir and save_documents_visualization_path into a single absolute path string."""
        return str(Path(self.root_dir) / self.save_documents_visualization_path)

    @property
    def full_training_data_path(self) -> str:
        """Combines root_dir and save_training_data_path into a single absolute path string."""
        return str(Path(self.root_dir) / self.save_training_data_path)

    @property
    def full_save_model_path(self) -> str:
        """Combines root_dir and save_model_path into a single absolute path string."""
        if self.bertopic_save_model_params.serialization == "pickle":
            return str(Path(self.root_dir) / self.save_model_path / "topic_embeddings.pkl")
        return str(Path(self.root_dir) / self.save_model_path)


class BERTopicFitModel(BERTopicBase):
    """A class for fitting and managing a BERTopic model.

     This class provides methods for fitting a BERTopic model on input documents, generating visualizations, and saving
     both the model and visualizations to disk. It also supports exporting visualizations as images and saving training
     data used for fitting the model.

    Attributes:
        bertopic_model_params (BERTopicModelParams): Configuration parameters for the
            BERTopic model. Defaults to an empty dictionary which is converted to a
            BERTopicModelParams instance during validation.
        umap_model_params (UMAPModelParams): Configuration parameters for the UMAP
            dimensionality reduction model. Defaults to an empty dictionary which is
            converted to a UMAPModelParams instance during validation.
        hdbscan_model_params (HDBSCANModelParams): Configuration parameters for the
            HDBSCAN clustering model. Defaults to an empty dictionary which is
            converted to a HDBSCANModelParams instance during validation.
        bertopic_save_model_params (BERTopicSaveModelParams): Parameters for saving
            the BERTopic model. Defaults to BERTopicSaveModelParams().
        export_visualization_to_image (bool): Whether to export visualizations as
            image files. Defaults to True.
        image_export_params (ToImageParams): Parameters for image export configuration.
            Defaults to ToImageParams().
        root_dir (str): Root directory for storing model and visualization files.
            Defaults to SINAPSIS_CACHE_DIR.
        save_documents_visualization_path (str): Relative path for saving documents
            visualization HTML file. Defaults to "documents_visualization.html".
        save_model_path (str): Relative path for saving the BERTopic model.
        save_training_data (bool): Whether to save training data to disk.
            Defaults to False.
        save_training_data_path (str): Relative path for saving training data pickle
            file. Defaults to "training_data.pkl".
        sentence_model_name (str): Identifier for the sentence transformer model.
            Defaults to "sentence-transformers/all-MiniLM-L6-v2".
        visualize_documents_params (VisualizeDocumentsParams): Parameters for document
            visualization. Defaults to VisualizeDocumentsParams().

    """

    AttributesBaseModel = BERTopicFitModelAttributes
    attributes: BERTopicFitModelAttributes

    def __init__(self, attributes: TemplateAttributes) -> None:
        super().__init__(attributes)

    def initialize_bertopic_model(self) -> None:
        """Initialize and configure the BERTopic model with UMAP and HDBSCAN components.

        This method sets up three interconnected models:
        - UMAP: Dimensionality reduction model configured with parameters from self.attributes.umap_model_params
        - HDBSCAN: Clustering model configured with parameters from self.attributes.hdbscan_model_params,
          including any additional kwargs
        - SentenceTransformer: Embedding model initialized with the specified sentence_model_name
        - BERTopic: The main topic modeling instance that combines UMAP and HDBSCAN with additional
          parameters from self.attributes.bertopic_model_params

        The initialized BERTopic model is assigned to self.topic_model.
        """
        umap_model = UMAP(**self.attributes.umap_model_params.model_dump())

        hdbscan_model_params = self.attributes.hdbscan_model_params.model_dump(exclude={"kwargs"})
        extra_kwargs = self.attributes.hdbscan_model_params.kwargs or {}
        merged_hdbscan_model_params = {**hdbscan_model_params, **extra_kwargs}
        hdbscan_model = HDBSCAN(**merged_hdbscan_model_params)
        ctfidf_model = ClassTfidfTransformer(**self.attributes.ctfidf_model_params.model_dump())

        bertopic_params_dict = self.attributes.bertopic_model_params.model_dump()
        bertopic_params_dict["ctfidf_model"] = ctfidf_model
        bertopic_params_dict["umap_model"] = umap_model
        bertopic_params_dict["hdbscan_model"] = hdbscan_model
        bertopic_params_dict["embedding_model"] = SentenceTransformer(self.attributes.sentence_model_name)

        self.topic_model = BERTopic(**bertopic_params_dict)

    def save_model(self) -> str:
        """Save the fitted topic model to the specified path using the configured serialization format.

        Supports both safetensors/pytorch formats (with additional parameters) and default format.

        Returns:
            str: The full path where the model was saved.
        """
        save_path = self.attributes.full_save_model_path
        self.topic_model = cast(BERTopic, self.topic_model)

        if self.attributes.bertopic_save_model_params.serialization in ["safetensors", "pytorch"]:
            save_attrs = self.attributes.bertopic_save_model_params.model_dump()
            save_attrs["save_embedding_model"] = self.attributes.sentence_model_name
            save_attrs["path"] = save_path

            self.topic_model.save(**save_attrs)
        else:
            self.topic_model.save(save_path)
        self.logger.info(f"Bertopic model saved at {save_path}")
        return save_path

    def save_training_data(self, docs: list[str], embeddings: np.ndarray) -> None:
        """Saves the training data used for fitting the model to disk.

        Args:
            docs (list[str]): The list of documents used for training.
            embeddings (np.ndarray): The embeddings corresponding to the documents.

        """
        training_data = (docs, embeddings)
        save_path = self.attributes.full_training_data_path

        if not Path(self.attributes.root_dir).exists():
            self.logger.info(f"Root directory {self.attributes.root_dir} does not exist. Creating it.")
            Path(self.attributes.root_dir).mkdir(parents=True, exist_ok=True)

        if Path(save_path).exists():
            self.logger.warning(f"Training data file already exists at {save_path}. It will be overwritten.")
        else:
            self.logger.info(f"Saving training data at {save_path}.")

        with open(save_path, "wb") as f:
            pickle.dump(training_data, f)

    def fit_model(self, docs: list[str], embeddings: np.ndarray) -> None:
        """Fits the BERTopic model on the provided documents.

        This method encodes the input documents using a sentence transformer model,
        then fits the BERTopic model on the encoded document embeddings.

        Args:
            docs (list[str]): A list of document strings to be used for fitting the model.
            embeddings (np.ndarray): A numpy array containing the embeddings for the input documents.
        """
        self.topic_model = cast(BERTopic, self.topic_model)
        self.topic_model.fit(docs, embeddings)

    def produce_documents_visualizations(self, docs: list[str], embeddings: np.ndarray) -> graph_objects.Figure:
        """Generate visualizations of documents using BERTopic topic modeling.

        This method encodes the provided documents using a sentence transformer model,
        fits the topic model on the encoded documents, and produces an interactive
        visualization of the documents in a reduced dimensional space.

        Args:
            docs: A list of document strings to be encoded and visualized.
            embeddings: A numpy array of shape (n_documents, embedding_dim) containing the embeddings for the input
                documents.

        Returns:
            graph_objects.Figure: A Plotly figure object containing the interactive
                visualization of the documents with their topic assignments.
        """
        self.topic_model = cast(BERTopic, self.topic_model)
        visualize_docs_dict = self.attributes.visualize_documents_params.model_dump()
        visualize_docs_dict["embeddings"] = embeddings
        visualize_docs_dict["docs"] = docs

        return self.topic_model.visualize_documents(**visualize_docs_dict)

    def append_files_to_container(self, container: DataContainer) -> None:
        """Append file packets for the saved model, visualizations, and optionally training data.

        Modifies the provided data container in place.
        """
        if self.attributes.save_training_data:
            training_data_path = self.attributes.full_training_data_path
            container.files.append(FilePacket(content=training_data_path))

        visualization_path = self.attributes.full_visualization_path
        container.files.append(FilePacket(content=visualization_path))

        serialization = self.attributes.bertopic_save_model_params.serialization
        save_base_path = self.attributes.full_save_model_path
        save_ctfidf = self.attributes.bertopic_save_model_params.save_ctfidf

        config_path = f"{save_base_path}/{CONFIG_NAME}"
        topics_path = f"{save_base_path}/{TOPICS_NAME}"
        ctfidf_cfg_path = f"{save_base_path}/{CTFIDF_CFG_NAME}"

        if serialization == "safetensors":
            model_path = f"{save_base_path}/{HF_SAFE_WEIGHTS_NAME}"
            container.files.append(FilePacket(content=model_path))

            container.files.append(FilePacket(content=config_path))
            container.files.append(FilePacket(content=topics_path))

            if save_ctfidf:
                ctfidf_path = f"{save_base_path}/{CTFIDF_SAFE_WEIGHTS_NAME}"
                container.files.append(FilePacket(content=ctfidf_path))
                container.files.append(FilePacket(content=ctfidf_cfg_path))

        elif serialization == "pytorch":
            model_path = f"{save_base_path}/{HF_WEIGHTS_NAME}"
            container.files.append(FilePacket(content=model_path))

            container.files.append(FilePacket(content=config_path))
            container.files.append(FilePacket(content=topics_path))

            if save_ctfidf:
                ctfidf_path = f"{save_base_path}/{CTFIDF_WEIGHTS_NAME}"
                container.files.append(FilePacket(content=ctfidf_path))
                container.files.append(FilePacket(content=ctfidf_cfg_path))

        else:
            container.files.append(FilePacket(content=save_base_path))

    def get_docs_from_datacontainer(self, container: DataContainer) -> list[str]:
        """Extract documents from text packets in the provided data container.

        This method looks for text packets within the container and compiles a list
        of document strings to be used for model fitting.

        Args:
            container (DataContainer): The input data container containing text packets.

        Returns:
            list[str]: A list of documents extracted from the text packets in the container.
        """
        return get_docs_from_text_packets(container)

    def execute(self, container: DataContainer) -> DataContainer:
        """Execute the BERTopic model fitting and visualization pipeline.

        This method orchestrates the complete workflow for training a BERTopic model:
        1. Extracts documents from text packets in the container
        2. Generates embeddings for the documents
        3. Fits the BERTopic model with the documents and embeddings
        4. Produces document visualizations
        5. Saves the visualizations to disk
        6. Optionally saves training data if configured
        7. Optionally exports visualizations to image array and appends to container if configured
        8. Persists the trained model to disk

        Args:
            container (DataContainer): The input data container with text packets to process.

        Returns:
            DataContainer: The updated container, optionally containing image arrays if
                          export_visualization_to_image is enabled.
        """
        docs = self.get_docs_from_datacontainer(container)

        if not docs:
            self.logger.warning("No documents found in the received data container. Returning input container.")
            return container

        embeddings = self.infer_embeddings(docs)
        self.fit_model(docs, embeddings)

        fig = self.produce_documents_visualizations(docs, embeddings)

        self.save_figure_to_html(fig, self.attributes.full_visualization_path)

        if self.attributes.save_training_data:
            self.save_training_data(docs, embeddings)

        if self.attributes.export_visualization_to_image:
            img_arr = self.convert_figure_to_image_array(fig)
            self.append_img_array_to_container(img_arr, container)
        self.save_model()
        self.append_files_to_container(container)

        return container

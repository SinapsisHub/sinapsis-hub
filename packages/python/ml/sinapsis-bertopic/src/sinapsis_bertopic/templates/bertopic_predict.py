import pickle
from pathlib import Path
from typing import cast

import numpy as np
from bertopic import BERTopic
from plotly import graph_objects as go
from pydantic import BaseModel, ConfigDict, Field
from sinapsis.data_transport import DataContainer, FilePacket, TextAnnotations, TextPacket

from sinapsis_bertopic.helpers.bertopic_helpers import get_docs_from_text_packets
from sinapsis_bertopic.templates.base_models.base_attrs import VisualizeTopicsParams
from sinapsis_bertopic.templates.bertopic_base import BERTopicBase, BERTopicBaseAttributes
from sinapsis_bertopic.third_party._documents import visualize_documents


class BERTopicPredictions(BaseModel):
    """A Pydantic model representing BERTopic prediction results.

    This model encapsulates the output of a BERTopic model's prediction operation,
    containing topic assignments, their corresponding labels, and confidence probabilities.

    Attributes:
        topics (list[int]): A list of topic identifiers assigned to each document.
            Each integer represents the predicted topic for the corresponding input.
        labels (list[str]): A list of human-readable labels corresponding to each predicted topic.
            Provides interpretable names or descriptions for the assigned topics.
        probs (np.ndarray): A NumPy array containing the probability scores for each prediction.
            Typically contains confidence values indicating the model's certainty in its predictions.

    Config:
        model_config (ConfigDict): Pydantic model configuration that allows arbitrary types
            (specifically NumPy arrays) to be used as model fields.
    """

    topics: list[int]
    labels: list[str]
    probs: np.ndarray
    model_config = ConfigDict(arbitrary_types_allowed=True)


class BERTopicPredictAttributes(BERTopicBaseAttributes):
    """BERTopicPredictAttributes class for managing BERTopic prediction configuration.

    Attributes:
        model_path (str): Path to the trained BERTopic model file.
        visualize_predictions (bool): Whether to generate visualizations for predictions.
            Defaults to False.
        historical_data_path (str | None): Path to historical data required for
            visualization. Must be provided if visualize_predictions is True.
            Defaults to None.
        root_dir (str): Root directory for storing prediction outputs.
            Defaults to SINAPSIS_CACHE_DIR.
        prediction_viz_path (str): Relative path for the prediction visualization file.
            Defaults to "prediction_viz.html".

    Methods:
        validate_attributes() -> None: Validates that historical_data_path is provided
            when visualize_predictions is enabled. Raises ValueError if validation fails.
        full_prediction_viz_path (property): Computed field that combines root_dir
            and prediction_viz_path into an absolute file path.
    """

    model_path: str
    visualize_predictions: bool = False
    visualize_topics: bool = True
    historical_data_path: str | None = None
    prediction_viz_path: str = "prediction_viz.html"
    visualize_topics_params: VisualizeTopicsParams = Field(default_factory=VisualizeTopicsParams)
    save_topic_visualization_path: str = "topics_visualization.html"

    def validate_attributes(self) -> None:
        """Validate that historical_data_path is provided if visualize_predictions is True."""
        if self.visualize_predictions and not self.historical_data_path:
            raise ValueError("historical_data_path must be provided when visualize_predictions is True")

    @property
    def full_prediction_viz_path(self) -> str:
        """Combines root_dir and prediction_viz_path into a single absolute path string."""
        return str(Path(self.root_dir) / self.prediction_viz_path)

    @property
    def full_topic_visualization_path(self) -> str:
        """Combines root_dir and save_topic_visualization_path into a single absolute path string."""
        return str(Path(self.root_dir) / self.save_topic_visualization_path)


class BERTopicPredict(BERTopicBase):
    """BERTopicPredict template for topic prediction using BERTopic models.

    This class provides functionality to load a pre-trained BERTopic model and generate
    topic predictions for document collections. It handles model loading, prediction generation,
    and integration with the data container pipeline.

    Attributes:
        AttributesBaseModel: Configuration model for BERTopicPredict template.
            - model_path (str): Path to the saved BERTopic model file. It can point to a local saved model or a
                model stored in a huggingface hub repo.
            - visualize_predictions (bool): Whether to generate visualizations for predictions.
                Defaults to False.
            - historical_data_path (str | None): Path to historical data required for
                visualization. Must be provided if visualize_predictions is True.
                Defaults to None.
            - root_dir (str): Root directory for storing prediction outputs.
                Defaults to SINAPSIS_CACHE_DIR.
            - prediction_viz_path (str): Relative path for the prediction visualization file.
                Defaults to "prediction_viz.html".
            - save_topic_visualization_path (str): Relative path for the topic visualization file.
                Defaults to "topics_visualization.html".
    """

    AttributesBaseModel = BERTopicPredictAttributes
    attributes: BERTopicPredictAttributes

    def initialize_bertopic_model(self) -> None:
        """Load the BERTopic model from the specified path in attributes.

        Returns:
            str: The model path that was loaded.
        """
        self.topic_model = BERTopic.load(self.attributes.model_path)

    def produce_topics_visualizations(self) -> go.Figure:
        """Generate interactive visualizations of the discovered topics from the BERTopic model.

        This method produces a comprehensive visual representation of all topics identified
        by the topic model, displaying their relationships and characteristics through an
        interactive plotly figure.

        Returns:
        -------
        go.Figure
            An interactive plotly Figure object containing the topics visualization.
            The visualization includes topic embeddings, their spatial relationships,
            and other relevant topic metrics for exploratory data analysis.
        """
        self.topic_model = cast(BERTopic, self.topic_model)

        visualize_topics_params = self.attributes.visualize_topics_params.model_dump(by_alias=True)

        return self.topic_model.visualize_topics(**visualize_topics_params)

    def produce_prediction_visualization(self, docs: list[str], topics: list[int], embeddings: np.ndarray) -> go.Figure:
        """Visualize the predicted topics for the given documents.

        Args:
            docs (list[str]): List of documents for which topics were predicted.
            topics (list[int]): List of predicted topic indices corresponding to each document.
            embeddings (np.ndarray): Array of embeddings for each document.

        Returns:
            go.Figure: A Plotly figure visualizing the predicted topics and their probabilities.
        """
        self.topic_model = cast(BERTopic, self.topic_model)
        with open(cast(str, self.attributes.historical_data_path), "rb") as file_obj:
            train_docs, train_embeddings = pickle.load(file_obj)

        merged_docs = train_docs + docs
        merged_embeddings = np.vstack([train_embeddings, embeddings])

        self.topic_model.topics_ = list(getattr(self.topic_model, "topics_")) + list(topics)

        document_viz = visualize_documents(
            topic_model=self.topic_model, docs=merged_docs, embeddings=merged_embeddings, highligth_last_n=len(docs)
        )

        return document_viz

    def get_predictions(self, docs: list[str], embeddings: np.ndarray) -> BERTopicPredictions:
        """Generate topic predictions for the provided documents.

        Args:
            docs (list[str]): List of documents to predict topics for.
            embeddings (np.ndarray): Array of embeddings for each document.

        Returns:
            BERTopicPredictions: Object containing predicted topics, labels, and probabilities.
        """
        self.topic_model = cast(BERTopic, self.topic_model)

        topics, probs = self.topic_model.transform(docs, embeddings=embeddings)
        topic_labels = [self.topic_model.topic_labels_[t] for t in topics]

        return BERTopicPredictions(topics=topics, labels=topic_labels, probs=probs)

    def parse_text_annotations(self, text_packets: list[TextPacket], preds: BERTopicPredictions) -> None:
        """Parse text annotations from BERTopic predictions and assign them to text packets.

        Args:
            text_packets: List of TextPacket objects to annotate.
            preds: BERTopicPredictions containing topics, labels, and probabilities.

        Returns:
            None. Modifies text_packets in place by setting their annotations attribute.
        """
        for text_packet, topic, label, prob in zip(text_packets, preds.topics, preds.labels, preds.probs.tolist()):
            text_packet.annotations.append(TextAnnotations(label=topic, label_str=label, confidence_score=prob))

    def save_visualizations(
        self, container: DataContainer, docs: list[str], preds: BERTopicPredictions, embeddings: np.ndarray
    ) -> None:
        """Save visualization outputs for BERTopic predictions and topics.

        Generates and saves visualizations based on the configured attributes. Can produce
        HTML files and/or convert visualizations to image arrays that are appended to the
        data container.

        Args:
            container (DataContainer): The data container to append image arrays to if
                export_visualization_to_image is enabled.
            docs (list[str]): List of documents used for predictions.
            preds (BERTopicPredictions): Prediction results containing topic assignments.
            embeddings (np.ndarray): Document embeddings array.

        Returns:
            None
        """
        if self.attributes.visualize_predictions:
            fig_preds = self.produce_prediction_visualization(docs, preds.topics, embeddings)
            self.save_figure_to_html(fig_preds, self.attributes.full_prediction_viz_path)
            container.files.append(FilePacket(content=self.attributes.full_prediction_viz_path))

            if self.attributes.export_visualization_to_image:
                img_arr = self.convert_figure_to_image_array(fig_preds)
                self.append_img_array_to_container(img_arr, container)

        if self.attributes.visualize_topics:
            fig_topics = self.produce_topics_visualizations()
            self.save_figure_to_html(fig_topics, self.attributes.full_topic_visualization_path)
            container.files.append(FilePacket(content=self.attributes.full_topic_visualization_path))

            if self.attributes.export_visualization_to_image:
                img_arr = self.convert_figure_to_image_array(fig_topics)
                self.append_img_array_to_container(img_arr, container)

    def execute(self, container: DataContainer) -> DataContainer:
        """Execute the prediction pipeline on documents from the data container.

        Args:
            container (DataContainer): Input data container with documents to predict.

        Returns:
            DataContainer: Updated container with prediction results.
        """
        docs = get_docs_from_text_packets(container)

        if not docs:
            self.logger.warning("No documents found in the container for prediction.")
            return container

        embeddings = self.infer_embeddings(docs)

        preds = self.get_predictions(docs, embeddings)

        self.parse_text_annotations(container.texts, preds)

        self.save_visualizations(container, docs, preds, embeddings)
        return container

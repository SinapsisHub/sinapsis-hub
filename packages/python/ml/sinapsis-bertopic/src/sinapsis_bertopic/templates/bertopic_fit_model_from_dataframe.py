from sinapsis.data_transport import DataContainer

from sinapsis_bertopic.templates.bertopic_fit_model import BERTopicFitModel, BERTopicFitModelAttributes


class BERTopicFitModelFromDataFrameAttributes(BERTopicFitModelAttributes):
    """Attributes for configuring the BERTopicFitModelFromDataFrame class.

    Extends BERTopicFitModelAttributes with additional parameters specific to handling dataframe inputs.
    """

    columns_to_use: list[str]


class BERTopicFitModelFromDataFrame(BERTopicFitModel):
    """Fit and manage a BERTopic model using documents extracted from dataframe packets.

    This class extends the BERTopicFitModel class, adding functionality to handle dataframe inputs.

    This class provides methods for fitting a BERTopic model on input documents, generating
    visualizations, and saving both the model and visualizations to disk. It also supports
    exporting visualizations as images and saving training data used for fitting the model.

    Attributes:
        columns_to_use (list[str]): A list of column names to extract text from within the dataframe packets.
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

    AttributesBaseModel = BERTopicFitModelFromDataFrameAttributes
    attributes: BERTopicFitModelFromDataFrameAttributes

    def get_docs_from_dataframe_packets(self, container: DataContainer, columns: list[str]) -> list[str]:
        """Extract documents from specified columns in dataframe packets within the data container.

        Args:
            container (DataContainer): The input data container containing dataframe packets.
            columns (list[str]): A list of column names to extract text from within the dataframe packets.

        Returns:
            list[str]: A list of documents extracted from the specified columns in the dataframe packets.
        """
        docs = []
        for dataframe_packet in container.data_frames:
            for column in columns:
                if column in getattr(dataframe_packet, "columns"):
                    docs.extend(dataframe_packet.content[column].astype(str).tolist())
                else:
                    self.logger.warning(f"Column '{column}' not found in dataframe packet. Skipping this column.")
        return docs

    def get_docs_from_datacontainer(self, container: DataContainer) -> list[str]:
        """Extract documents from dataframe packets in the provided data container.

        This method serves as a wrapper around get_docs_from_dataframe_packets, utilizing
        the columns_to_use attribute from the class configuration.

        Args:
            container (DataContainer): The input data container containing dataframe packets.

        Returns:
            list[str]: A list of documents extracted from the specified columns in the dataframe packets.
        """
        return self.get_docs_from_dataframe_packets(container, self.attributes.columns_to_use)

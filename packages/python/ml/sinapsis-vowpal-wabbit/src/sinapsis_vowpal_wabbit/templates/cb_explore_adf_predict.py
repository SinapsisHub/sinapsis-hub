from sinapsis.data_transport import DataContainer, TextAnnotations

from sinapsis_vowpal_wabbit.templates.cb_explore_adf_base import CBExploreADFBase, CBExploreADFBaseAttributes


class CBExploreADFPredictAttributes(CBExploreADFBaseAttributes):
    """Attributes for contextual bandit exploration with action-dependent features prediction.

    This class extends CBExploreADFBaseAttributes to define specific configuration
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

    """

    model_path: str
    inference_only: bool = True
    threshold: float = 0
    top_k: int = 3


class CBExploreADFPredict(CBExploreADFBase):
    """Template to perform action predictions using the Vowpal Wabbit CB_Explore_ADF approach.

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

    """

    AttributesBaseModel = CBExploreADFPredictAttributes
    attributes: CBExploreADFPredictAttributes

    def _build_vw_config(self) -> str:
        """Build the Vowpal Wabbit configuration string for prediction mode."""
        config_parts = [super()._build_vw_config()]

        if self.attributes.inference_only:
            config_parts.append("-t")

        config_parts.append(f"-i {self.attributes.model_path}")

        config = " ".join(config_parts)

        return config

    def execute(self, container: DataContainer) -> DataContainer:
        """Run the prediction pipeline and annotate text packets with top-k actions."""
        for text_packet in container.texts:
            input_msg = text_packet.content

            vw_text = self.get_vw_format(input_msg, self.attributes.actions)

            prediction = self.vw.predict(vw_text)
            indexed_preds = list(enumerate(prediction))

            top_k_filtered = [
                (idx, prob)
                for idx, prob in sorted(indexed_preds, key=lambda x: x[1], reverse=True)
                if prob >= self.attributes.threshold
            ][: self.attributes.top_k]

            if not top_k_filtered:
                text_packet.annotations = [TextAnnotations(label_str="Unkown")]

            else:
                chosen_actions = [(idx, self.attributes.actions[idx], prob) for idx, prob in top_k_filtered]
                top_action = chosen_actions[0]

                extra_labels = {action[1]: action[2] for action in chosen_actions[1:]}

                text_packet.annotations = [
                    TextAnnotations(
                        label=top_action[0],
                        label_str=top_action[1],
                        confidence_score=top_action[2],
                        extra_labels=extra_labels,
                    )
                ]

        return container

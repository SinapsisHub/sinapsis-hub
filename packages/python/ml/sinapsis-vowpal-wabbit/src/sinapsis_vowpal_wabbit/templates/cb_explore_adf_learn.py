import random
from pathlib import Path

from pydantic import Field, computed_field
from sinapsis.data_transport import DataContainer, FilePacket
from sinapsis.env_vars import SINAPSIS_CACHE_DIR
from sinapsis.template import TemplateAttributeType
from sklearn.model_selection import train_test_split

from sinapsis_vowpal_wabbit.templates.base_models import TrainTestSplitParams
from sinapsis_vowpal_wabbit.templates.cb_explore_adf_base import CBExploreADFBase, CBExploreADFBaseAttributes


class CBExploreADFLearnAttributes(CBExploreADFBaseAttributes):
    """Attributes for Contextual Bandit exploration with Action Dependent Features (ADF) in learning mode.

    This class extends CBExploreADFBaseAttributes with additional configuration parameters
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
    """

    epochs: int = 5
    instruction_column: str
    true_action_column: str
    split_dataset: bool = True
    train_test_split_params: TrainTestSplitParams = Field(default_factory=TrainTestSplitParams)

    root_dir: str = SINAPSIS_CACHE_DIR
    save_path: str = "cb_explore_adf_model.vw"

    @computed_field
    @property
    def full_save_path(self) -> str:
        """Combines root_dir and save_path into a single absolute path string."""
        return str(Path(self.root_dir) / self.save_path)


class CBExploreADFLearn(CBExploreADFBase):
    """Template to perform action learning using the Vowpal Wabbit CB_Explore_ADF approach.

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


    """

    AttributesBaseModel = CBExploreADFLearnAttributes
    attributes: CBExploreADFLearnAttributes

    def __init__(self, attributes: TemplateAttributeType) -> None:
        super().__init__(attributes)

        if self.attributes.random_seed is not None:
            random.seed(self.attributes.random_seed)

    def _build_vw_config(self) -> str:
        """Build the Vowpal Wabbit configuration string for contextual bandit exploration.

        Extends parent configuration with action-dependent features (ADF) learning by adding
        a model file save path parameter.

        Returns:
            str: A space-separated string containing Vowpal Wabbit command-line arguments, including the parent
                 configuration and the full file path where the model will be saved using the '-f' flag.
        """
        config_parts = [super()._build_vw_config()]

        config_parts.append(f"-f {self.attributes.full_save_path}")

        return " ".join(config_parts)

    def execute(self, container: DataContainer) -> DataContainer:
        """Execute the contextual bandit exploration and learning pipeline.

        This method trains a Vowpal Wabbit model using contextual bandit exploration
        with ADF (Action Dependent Features) format. It splits the data into training
        and validation sets, then iterates through multiple epochs.

        During each epoch:
        - Training phase: Explores actions using epsilon-greedy strategy based on
            model predictions, records costs, and learns from the feedback.
        - Validation phase: Evaluates model performance by selecting the best predicted
            action and comparing against ground truth.

        Args:
                container: A data container object that holds input data frames.
                                     Expects container.data_frames[0].content to be a pandas DataFrame
                                     with columns specified in self.attributes (instruction_column,
                                     true_action_column).

        Returns:
                container: The same input container object (unchanged).

        """
        for data_frame_packet in container.data_frames:
            df = data_frame_packet.content
            split_attrs = self.attributes.train_test_split_params

            train_df, val_df = train_test_split(
                df,
                train_size=split_attrs.train_size,
                test_size=split_attrs.test_size,
                shuffle=split_attrs.shuffle,
                random_state=self.attributes.random_seed,
            )

            for epoch in range(self.attributes.epochs):
                # --- TRAINING PHASE ---
                cost_sum_train = 0
                train_shuffled = train_df.sample(frac=1)

                for _, row in train_shuffled.iterrows():
                    user_query = row[self.attributes.instruction_column]
                    true_intent = row[self.attributes.true_action_column]

                    vw_text = self.get_vw_format(user_query, self.attributes.actions)
                    prediction = self.vw.predict(vw_text)

                    chosen_idx = random.choices(range(len(prediction)), weights=prediction)[0]

                    prob = prediction[chosen_idx]

                    cost = 0.0 if self.attributes.actions[chosen_idx] == true_intent else 1.0

                    cost_sum_train += cost
                    learn_text = self.get_vw_format(user_query, self.attributes.actions, chosen_idx, cost, prob)
                    self.vw.learn(learn_text)

                # --- VALIDATION PHASE (After each epoch) ---
                correct_val = 0
                for _, row in val_df.iterrows():
                    user_query = row[self.attributes.instruction_column]
                    true_intent = row[self.attributes.true_action_column]

                    vw_text = self.get_vw_format(user_query, self.attributes.actions)
                    prediction = self.vw.predict(vw_text)

                    # For validation, we pick the BEST action (argmax)
                    best_idx = prediction.index(max(prediction))
                    if self.attributes.actions[best_idx] == true_intent:
                        correct_val += 1

                val_accuracy = correct_val / len(val_df)
                train_accuracy = (len(train_df) - cost_sum_train) / len(train_df)

                self.logger.info(f"Epoch {epoch + 1} | Train Acc: {train_accuracy:.4f} | Val Acc: {val_accuracy:.4f}")

        container.files.append(FilePacket(content=self.attributes.full_save_path))

        self.vw.save(self.attributes.full_save_path)

        return container

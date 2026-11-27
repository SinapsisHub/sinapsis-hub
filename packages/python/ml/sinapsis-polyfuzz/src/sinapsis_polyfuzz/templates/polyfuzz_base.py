from typing import Any

import pandas as pd
from sinapsis.data_transport import DataContainer, DataFramePacket
from sinapsis.template import OutputTypes, TemplateAttributes, UIPropertiesMetadata
from sinapsis.template import Template

from sinapsis_polyfuzz.helpers.tags import Tags


class PolyfuzzBaseAttributes(TemplateAttributes):
    """Attributes for Polyfuzz base configuration.

    Attributes:
        target_column (str): The name of the column to be used as the target for matching.
        to_list (list[str] | None): A list of strings to match against. Defaults to None.
        overwrite (bool): Whether to overwrite the original packet content with results.
            If False, creates new packets. Defaults to False.
    """

    target_column: str
    to_list: list[str] | None = None
    overwrite: bool = False


class PolyfuzzBase(Template):
    """Base class for Polyfuzz-based templates, providing shared processing logic."""

    UIProperties = UIPropertiesMetadata(
        category="Polyfuzz",
        output_type=OutputTypes.MULTIMODAL,
        tags=[Tags.POLYFUZZ, Tags.MATCHING, Tags.EMBEDDING, Tags.SENTENCE_ENCODER],
    )

    wrapped_callable: Any

    @staticmethod
    def _get_column_values_as_list(packet: DataFramePacket, column: str) -> list[str]:
        """Extracts column values from a DataFrame (pandas or polars) as a list of strings.

        Args:
            packet: The DataFramePacket containing the DataFrame.
            column: The name of the column to extract.

        Returns:
            list[str]: The column values as a list of strings.
        """
        input_df = packet.content
        series = input_df[column]

        if packet.dataframe_type == "polars":
            return series.cast(str).to_list()
        return series.astype(str).tolist()

    def match(self, packet: DataFramePacket) -> pd.DataFrame:
        """Processes the input packet by matching a target column against a reference list.

        Extracts the target column specified in the attributes from the input DataFrame,
        converts it to a list of strings, and passes it to the wrapped callable's
        match method along with an optional reference list.

        Args:
            packet (DataFramePacket): The input packet containing the DataFrame to be processed.

        Returns:
            pd.DataFrame: The result of the matching operation as a pandas DataFrame.

        Raises:
            ValueError: If the target column is not found in the DataFrame.
        """
        if self.attributes.target_column not in packet.content.columns:
            msg = (
                f"Target column '{self.attributes.target_column}' not found in DataFrame. "
                f"Available columns: {list(packet.content.columns)}"
            )
            raise ValueError(msg)
        from_list = self._get_column_values_as_list(packet, self.attributes.target_column)
        args = {"from_list": from_list}

        if self.attributes.to_list is not None:
            args["to_list"] = self.attributes.to_list

        return self.wrapped_callable.match(**args)

    def save_results(
        self, matches: pd.DataFrame, packet: DataFramePacket, new_packets: list[DataFramePacket]
    ) -> None:
        """Saves the match results either by overwriting the packet content or creating new packets.

        Args:
            matches (pd.DataFrame): The DataFrame containing the matching results.
            packet (DataFramePacket): The source data packet that was processed.
            new_packets (list[DataFramePacket]): A list to collect new packets when
                overwrite is False. These will be added to the container after iteration.
        """
        if self.attributes.overwrite:
            packet.content = matches
        else:
            result_packet = DataFramePacket(content=matches)
            new_packets.append(result_packet)

    def execute(self, container: DataContainer) -> DataContainer:
        """Executes the processing logic on all data frames within the provided container.

        Args:
            container: A DataContainer instance containing the data frames to be processed.

        Returns:
            The processed DataContainer instance.
        """
        new_packets: list[DataFramePacket] = []
        for packet in container.data_frames:
            matches = self.match(packet)
            self.save_results(matches=matches, packet=packet, new_packets=new_packets)
        container.data_frames.extend(new_packets)
        return container

# -*- coding: utf-8 -*-
import os

from sinapsis.data_transport import DataContainer, DataFramePacket, TimeSeriesPacket
from sinapsis.env_vars import SINAPSIS_CACHE_DIR
from sinapsis.template import Template, TemplateAttributes, TemplateAttributeType

from sinapsis_data_readers.helpers.csv_reader import read_file


class CSVDatasetReader(Template):
    class AttributesBaseModel(TemplateAttributes):
        root_dir: str | None = None
        path_to_csv: str
        store_as_time_series: bool = False

    attributes: AttributesBaseModel

    def __init__(self, attributes: TemplateAttributeType) -> None:
        super().__init__(attributes)
        self.root_dir = self.attributes.root_dir or SINAPSIS_CACHE_DIR
        self.csv_file = read_file(os.path.join(self.root_dir, self.attributes.path_to_csv))

    def execute(self, container: DataContainer) -> DataContainer:
        if self.attributes.store_as_time_series:
            packet = TimeSeriesPacket(content=self.csv_file)
            container.time_series.append(packet)
        else:
            packet = DataFramePacket(content=self.csv_file, source=f"{self.instance_name}_x_dataset")
            container.data_frames.append(packet)

        return container

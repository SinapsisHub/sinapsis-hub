import io
from collections.abc import Sequence
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from pydantic.dataclasses import is_pydantic_dataclass
from sinapsis.data_transport import (
    AudioPacket,
    BaseAnnotations,
    BinaryPacket,
    DataContainer,
    DataFramePacket,
    FilePacket,
    ImagePacket,
    Packet,
    TextPacket,
    TimeSeriesPacket,
)
from sinapsis.logging import sinapsis_logger
from sinapsis.template import TemplateMetadata
from sinapsis_deserialization.schemas.constant_variables import (
    BasePacketFieldNames,
    ContainerFieldNames,
    EncodedArrayFieldNames,
    PacketFieldNames,
    SupportedArrayTypeNames,
    SupportedContentArrays,
)
from sinapsis_deserialization.schemas.type_checkers import (
    is_array_content,
    is_builtin_type,
    is_iterable,
)

from sinapsis_serializer_core.schemas.exceptions import SerializationError
from sinapsis_serializer_core.serialization.staging_file_manager import (
    StagingAudioManager,
    StagingFileManager,
    StagingGenericArrayManager,
    StagingImageManager,
    StagingTimeSeriesManager,
)


class DataContainerEncoder:
    def __init__(self, replace_content_with_url: bool = False) -> None:
        """If set to true, we will save the data to disk and instead replace a packet's
        content with an id or url to retrieve the data on a need basis.
        """
        self.replace_content_with_url = replace_content_with_url

    def container_encoder(self, obj: DataContainer, agent_id: str) -> dict[str, Any]:
        """
        Serializes a DataContainer and its Data packets into a dictionary.
        It iterates through all packet collections within the container—including
        images, audio, text, dataframes, and time series—applying proper
        encoders to each. The resulting dictionary is structured for
        transport across the Sinapsis messaging protocol.

        Args:
            obj: The DataContainer instance to be serialized.
            agent_id: The unique identifier for the agent session, used by sub-encoders
                for contextual operations like URL generation or storage pathing.

        Returns:
            dict[str, Any]: A dictionary containing serialized representations of all
                packets and generic metadata stored in the container.
        """
        res = {
            ContainerFieldNames.container_id: obj.container_id,
            ContainerFieldNames.images: [self.image_packet_encoder(packet, agent_id) for packet in obj.images],
            ContainerFieldNames.audios: [self.audio_packet_encoder(packet, agent_id) for packet in obj.audios],
            ContainerFieldNames.texts: [self.text_packet_encoder(packet, agent_id) for packet in obj.texts],
            ContainerFieldNames.files: [self.file_packet_encoder(packet, agent_id) for packet in obj.files],
            ContainerFieldNames.data_frames: [
                self.data_frame_packet_encoder(packet, agent_id) for packet in obj.data_frames
            ],
            ContainerFieldNames.time_series: [
                self.time_series_packet_encoder(packet, agent_id) for packet in obj.time_series
            ],
            ContainerFieldNames.binary_data: [
                self.binary_packet_encoder(packet, agent_id) for packet in obj.binary_data
            ],
            ContainerFieldNames.generic_data: self.generic_data_encoder(obj.generic_data, agent_id),
        }
        return res

    def file_packet_encoder(self, packet: FilePacket, agent_id: str) -> dict:
        """Specific encoder for FilePacket objects"""
        if self.replace_content_with_url:
            array_dict_with_metadata = {
                EncodedArrayFieldNames.content: StagingFileManager.save_staging_data(packet, agent_id)
            }
        else:
            array_dict_with_metadata = self.generic_array_like_content_encoder(packet.content)

        file_packet_dict = {
            EncodedArrayFieldNames.content: array_dict_with_metadata,
            EncodedArrayFieldNames.type: SupportedContentArrays.file,
        } | self.base_packet_meta_encoder(packet, agent_id)
        return file_packet_dict

    def base_packet_meta_encoder(self, packet: Packet, agent_id: str) -> dict:
        """Base encoder for data packets. It contains the embedding , generic_data and source fields."""

        embedding_dict = [self.generic_array_like_content_encoder(embedding) for embedding in packet.embedding]
        generic_data_dict = self.generic_data_encoder(packet.generic_data, agent_id) if packet.generic_data else {}
        packet_source = packet.source

        if isinstance(packet_source, Path):
            packet_source = str(packet_source.resolve())
        return {
            BasePacketFieldNames.id: packet.id,
            BasePacketFieldNames.source: packet_source,
            BasePacketFieldNames.embedding: embedding_dict,
            BasePacketFieldNames.generic_data: generic_data_dict,
        }

    @staticmethod
    def generic_array_like_content_encoder(content: Any) -> dict | None:
        """Encoder for generic array objects. At the moment numpy, pandas, darts, iterables and
        dictionary objects are supported
        """
        if content is None:
            return None
        device = "cpu"
        module_name = type(content).__module__

        if module_name.startswith("numpy"):
            shape = tuple(content.shape)
            dtype = str(content.dtype)
            bytes_content = content.tobytes()
            array_type = SupportedArrayTypeNames.numpy
        elif isinstance(content, str):
            shape = len(content)
            dtype = "str"
            array_type = SupportedArrayTypeNames.bytes
            bytes_content = content.encode()
        elif module_name.startswith("torch"):
            shape = tuple(content.size())
            device = device
            dtype = str(content.dtype)
            array_type = SupportedArrayTypeNames.torch
            bytes_content = content.cpu().detach().numpy().tobytes()
        elif isinstance(content, bytes):
            array_type = SupportedArrayTypeNames.bytes
            bytes_content = content
            shape = -1
            dtype = "bytes"

        elif module_name.startswith("pandas"):
            import pandas as pd

            if isinstance(content, pd.DataFrame):
                # we can optimise frame and series objects further by splitting them
                # into columns or index names and data. Data is a numpy array which
                # can be converted to bytes. However, we aren't guaranteed to have only
                # one data type so it needs iterating.

                shape = content.values.shape
                array_type = SupportedArrayTypeNames.pd_dataframe
                original = content.copy()

                # pandas JSON edge cases
                original.index = original.index.astype(str)
                original.columns = original.columns.astype(str)

                # return original.to_json(orient="split")
                bytes_content = original.to_json(orient="split")
                dtype = {str(k): str(v) for k, v in original.dtypes.items()}

            elif isinstance(content, pd.Series):
                shape = content.shape
                buf = io.BytesIO()
                content.to_pickle(buf)
                bytes_content = buf.getvalue()
                # bytes_content = content.to_pickle(None)
                # safe_series = content.copy()
                # safe_series.index = safe_series.index.astype(str)
                # bytes_content = safe_series.to_json(orient="split")
                array_type = SupportedArrayTypeNames.pd_timeseries
                dtype = str(content.dtype)

        elif module_name.startswith("darts"):
            shape = content.shape
            bytes_content = content.to_json()
            dtype = content.to_dataframe().dtypes.apply(str).to_dict()
            array_type = SupportedArrayTypeNames.darts_timeseries

        else:
            # raise SerializationError("Unsupported content type: {}".format(type(content)))
            sinapsis_logger.debug(f"Unsupported content type: {type(content)}, will return empty dict")
            # shape = -1
            # bytes_content = str(content)
            # dtype = str(content.dtype)
            # array_type = "text"
            return {}

        encoded_dict = {
            EncodedArrayFieldNames.content: bytes_content,
            EncodedArrayFieldNames.shape: shape,
            EncodedArrayFieldNames.device: device,
            EncodedArrayFieldNames.dtype: dtype,
            EncodedArrayFieldNames.array_type: array_type,
        }
        return encoded_dict

    # TODO: we need to handle generic data too # noqa:  TD002 TD003 FIX002
    def audio_packet_encoder(self, packet: AudioPacket, agent_id: str) -> dict[str, Any]:
        """
        Encoder for audio packets.

        """
        if self.replace_content_with_url:
            array_dict_with_metadata = {
                EncodedArrayFieldNames.content: StagingAudioManager.save_staging_data(packet, agent_id)
            }
            ann_dict_with_metadata = (
                {
                    PacketFieldNames.annotations: self.annotations_encoder(packet.annotations)  # ty: ignore[invalid-argument-type]
                }
                if packet.annotations
                else []
            )

        else:
            array_dict_with_metadata = self.generic_array_like_content_encoder(packet.content)
            ann_dict_with_metadata = [self.pydantic_dataclass_as_dict(ann) for ann in packet.annotations]

        audio_packet_dict = {
            EncodedArrayFieldNames.content: array_dict_with_metadata,
            EncodedArrayFieldNames.type: SupportedContentArrays.audio,
            PacketFieldNames.annotations: ann_dict_with_metadata,
            PacketFieldNames.sample_rate: packet.sample_rate,
            PacketFieldNames.audio_duration: packet.audio_duration,
        } | self.base_packet_meta_encoder(packet, agent_id)
        return audio_packet_dict

    @staticmethod
    def annotations_encoder(annotations: Sequence[BaseAnnotations]) -> list[dict[str, str]]:
        """Encode annotation objects into a preview-safe, serializable format.

        Iterates over a collection of annotation objects and converts each one
        into a dictionary. Every field value is passed through
        `StagingGenericArrayManager.make_preview()` to ensure it is suitable
        for previewing (e.g. reduced size, serialized, or transformed).

        Args:
            annotations (BaseAnnotations):
                Iterable of annotation objects (e.g. dataclasses) whose attributes
                will be encoded.

        Returns:
            list[dict]:
                A list of dictionaries, one per annotation, containing the
                preview-encoded field values.
        """
        new_ann = []
        for ann in annotations:
            ann_dict = {}
            for key, val in ann.__dict__.items():
                ann_dict[key] = StagingGenericArrayManager.make_preview(val)
            new_ann.append(ann_dict)
        return new_ann

    def image_packet_encoder(self, packet: ImagePacket, agent_id: str) -> dict[str, Any]:
        """Encoder for image packet objects."""
        if self.replace_content_with_url:
            array_dict_with_metadata = {
                EncodedArrayFieldNames.content: StagingImageManager.save_staging_data(packet, agent_id)
            }
            ann_dict_with_metadata = {PacketFieldNames.annotations: self.annotations_encoder(packet.annotations)}
        else:
            array_dict_with_metadata = self.generic_array_like_content_encoder(packet.content)
            ann_dict_with_metadata = [self.pydantic_dataclass_as_dict(ann) for ann in packet.annotations]
        encoded_data = {
            EncodedArrayFieldNames.content: array_dict_with_metadata,
            EncodedArrayFieldNames.type: SupportedContentArrays.image,
            PacketFieldNames.annotations: ann_dict_with_metadata,
            PacketFieldNames.color_space: packet.color_space.value if packet.color_space else None,
            # shape is a computed field
            # PacketFieldNames.shape: packet.content.shape if isinstance(packet.content, np.ndarray) else None,
        } | self.base_packet_meta_encoder(packet, agent_id)

        return encoded_data

    def template_attributes_encoder(self, template_attributes: dict[str, Any]) -> dict[str, Any]:
        # TODO: not sure this belongs here # noqa:  TD002 TD003 FIX002
        """Encoder for the template attrbibutes of the Agent"""
        metadata = template_attributes.get("metadata")
        if isinstance(metadata, TemplateMetadata):
            template_attributes["metadata"] = self.pydantic_dataclass_as_dict(metadata)
        return template_attributes

    def text_packet_encoder(self, packet: TextPacket, agent_id: str) -> dict[str, Any]:
        """Encoder for Text packet objects."""
        if not isinstance(packet, TextPacket):
            raise SerializationError(f"Packet content is meant to be of type str but got: {type(packet)}")
        if self.replace_content_with_url:
            text_content_data = {
                EncodedArrayFieldNames.content: StagingGenericArrayManager.save_staging_data(packet.content, agent_id)
            }
            ann_dict_with_metadata = {PacketFieldNames.annotations: self.annotations_encoder(packet.annotations)}
        else:
            text_content_data = packet.content
            ann_dict_with_metadata = [self.pydantic_dataclass_as_dict(ann) for ann in packet.annotations]
        return {
            EncodedArrayFieldNames.type: "text",
            PacketFieldNames.content: text_content_data,
            PacketFieldNames.annotations: ann_dict_with_metadata,
        } | self.base_packet_meta_encoder(packet, agent_id)

    def data_frame_packet_encoder(self, packet: DataFramePacket, agent_id: str) -> dict[str, Any]:
        """Encoder for data frame packet objects."""
        if self.replace_content_with_url:
            data_frame_content_data = {
                EncodedArrayFieldNames.content: StagingGenericArrayManager.save_staging_data(packet.content, agent_id)
            }
        else:
            data_frame_content_data = self.generic_array_like_content_encoder(packet.content)
        return {
            EncodedArrayFieldNames.type: SupportedContentArrays.dataframe,
            PacketFieldNames.content: data_frame_content_data,
        } | self.base_packet_meta_encoder(packet, agent_id)

    def time_series_packet_encoder(self, packet: TimeSeriesPacket, agent_id: str) -> dict[str, Any]:
        """Encoder for time series packet objects."""
        if self.replace_content_with_url:
            time_series_content_data = {
                EncodedArrayFieldNames.content: StagingTimeSeriesManager.save_staging_data(packet, agent_id)
            }
        else:
            time_series_content_data = self.generic_array_like_content_encoder(packet.content)
        return {
            EncodedArrayFieldNames.type: SupportedContentArrays.timeseries,
            PacketFieldNames.content: time_series_content_data,
            # TODO: need save like content if replace with url set # noqa:  TD002 TD003 FIX002
            PacketFieldNames.predictions: self.generic_array_like_content_encoder(packet.predictions),
            PacketFieldNames.past_covariates: self.generic_array_like_content_encoder(packet.past_covariates),
            PacketFieldNames.future_covariates: self.generic_array_like_content_encoder(packet.future_covariates),
        } | self.base_packet_meta_encoder(packet, agent_id)

    def binary_packet_encoder(self, packet: BinaryPacket, agent_id: str) -> dict[str, Any]:
        """Encoder for byte packet objects."""
        if not isinstance(packet.content, bytes):
            raise TypeError("packet.content must be of type bytes")
        if self.replace_content_with_url:
            bytes_content_data = {
                EncodedArrayFieldNames.content: StagingGenericArrayManager.save_staging_data(packet.content, agent_id)
            }
        else:
            bytes_content_data = self.generic_array_like_content_encoder(packet.content)
        return {
            EncodedArrayFieldNames.type: SupportedContentArrays.binary,
            PacketFieldNames.content: bytes_content_data,
        } | self.base_packet_meta_encoder(packet, agent_id)

    def _encode_single_item(self, item: Any) -> Any:
        """Helper to determine the type of single item and encode it accordingly.

        Args:
            item (Any): Element to encode

        Returns:
            Any: Encoded element
        """
        if is_builtin_type(item):
            return item

        if is_array_content(item):
            return self.generic_array_like_content_encoder(item)

        if isinstance(item, dict):
            return {k: self._encode_single_item(v) for k, v in item.items()}

        if isinstance(item, BaseModel):
            return {k: self._encode_single_item(v) for k, v in item.model_dump().items()}

        if is_pydantic_dataclass(item):
            return self.pydantic_dataclass_as_dict(item)

        if is_dataclass(item):
            return {k: self._encode_single_item(v) for k, v in asdict(item).items()}

        if hasattr(item, "__dict__"):
            return self._encode_single_item(vars(item))

        if isinstance(item, datetime):
            return item.isoformat()

        if is_iterable(item) and not isinstance(item, (str, bytes, bytearray)):
            return [self._encode_single_item(x) for x in item]

        return str(item)

    def generic_data_encoder(self, generic_data: dict[str, Any], agent_id: str) -> dict[str, Any]:
        """Encodes a dictionary of generic data into a serializable format..

        Args:
            generic_data (dict[str, Any]): A dictionary containing data of arbitrary types.
            agent_id (str): Agent identifier

        Returns:
            dict[str, Any]: A dictionary where all values have been converted to serializable types.
        """
        encoded_dict = {}

        for key, value in generic_data.items():
            key = key or "generic"

            if self.replace_content_with_url:
                encoded_val = {
                    EncodedArrayFieldNames.content: StagingGenericArrayManager.save_staging_data(value, agent_id)
                }
            else:
                encoded_val = self._encode_single_item(value)
            encoded_dict[key] = encoded_val
        return encoded_dict

    def pydantic_dataclass_as_dict(self, obj: object) -> dict[str, Any]:
        """
        Serializes a Pydantic  dataclass into a dictionary of serializable objects.

        Args:
            obj: The Pydantic dataclass instance to be converted.

        Returns:
            dict[str, Any]: A dictionary where all field values have been processed
                by `_encode_single_item`.
        """
        output = {}

        for name, value in asdict(obj).items():  # ty: ignore[invalid-argument-type]
            value = self._encode_single_item(value)

            output[name] = value
        return output

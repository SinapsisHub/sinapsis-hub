import io
from typing import Any

from sinapsis.data_transport import (
    AudioAnnotations,
    AudioPacket,
    BinaryPacket,
    DataContainer,
    DataFramePacket,
    FilePacket,
    ImageAnnotations,
    ImageColor,
    ImagePacket,
    TextAnnotations,
    TextPacket,
    TimeSeriesPacket,
)
from sinapsis.logging import sinapsis_logger

from sinapsis_deserialization.schemas.constant_variables import (
    BasePacketFieldNames,
    ContainerFieldNames,
    EncodedArrayFieldNames,
    PacketFieldNames,
    SupportedArrayTypeNames,
)
from sinapsis_deserialization.schemas.type_checkers import (
    is_array_content,
    is_encoded_array_type,
    is_iterable,
)


class DataContainerDecoder:
    """Class to decode different types of data packets into corresponding objects."""

    def __call__(self, container_dict: dict[str, Any]) -> DataContainer | dict[str, Any]:
        return self.decode_container(container_dict)

    def decode_container(self, container_dict: dict[str, Any]) -> DataContainer | dict[str, Any]:
        """Decode a container dictionary into a DataContainer object."""
        if isinstance(container_dict, dict) and ContainerFieldNames.container_id in container_dict:
            container_id = container_dict[ContainerFieldNames.container_id]
            return DataContainer(
                container_id=container_id,
                images=[self.decode_image(packet) for packet in container_dict.get(ContainerFieldNames.images, [])],
                audios=[self.decode_audio(packet) for packet in container_dict.get(ContainerFieldNames.audios, [])],
                texts=[self.decode_text(packet) for packet in container_dict.get(ContainerFieldNames.texts, [])],
                files=[self.decode_file(packet) for packet in container_dict.get(ContainerFieldNames.files, [])],
                data_frames=[
                    self.decode_data_frame(packet) for packet in container_dict.get(ContainerFieldNames.data_frames, [])
                ],
                time_series=[
                    self.decode_time_series(packet)
                    for packet in container_dict.get(ContainerFieldNames.time_series, [])
                ],
                binary_data=[
                    self.decode_binary(packet) for packet in container_dict.get(ContainerFieldNames.binary_data, [])
                ],
                generic_data=self.decode_generic_dict(container_dict.get(ContainerFieldNames.generic_data, {})),
            )
        return container_dict

    def decode_arrays_in_dict(self, dataclass_dict: dict) -> dict:
        """Decode a Pydantic dataclass into a DataContainer object."""
        for key, value in dataclass_dict.items():
            if isinstance(value, dict):
                if is_encoded_array_type(value):
                    dataclass_dict[key] = self.array_type_decoder(value)
                else:
                    self.decode_arrays_in_dict(value)
        return dataclass_dict

    def decode_generic_dict(self, generic_dict: dict[str, Any]) -> dict:
        """Decode a dictionary into a DataContainer object. For each of the values in the dictionary,
        recursively checkthe type of object to apply the proper decoding method

        Args:
            generic_dict: dictionary to be decoded
        Returns:
            decoded dictionary
        """
        decoded = {}
        for key, value in generic_dict.items():
            if isinstance(value, dict):
                if is_encoded_array_type(value):
                    decoded[key] = self.array_type_decoder(value)
                else:
                    decoded[key] = self.decode_generic_dict(value)

            elif is_iterable(value):
                decoded[key] = self.decode_iterable(value)

            else:
                decoded[key] = value

        return decoded

    def decode_iterable(self, obj: Any) -> list:
        """Recursively traverses and decodes nested objects.

        This method iterates through a collection (list, tuple, etc.) and evaluates
        each element. It specifically handles nested dictionaries, iterables,
        and encoded array types to ensure the entire tree is reconstructed into
        its original Python or numerical types.


        Args:
            obj: The iterable collection containing potentially encoded elements.

        Returns:
            A new collection of the same type as the input (e.g., list or tuple)
            containing the fully decoded items.
        """
        decoded_items = []
        for item in obj:
            if isinstance(item, dict):
                if is_encoded_array_type(item):
                    decoded_items.append(self.array_type_decoder(item))
                else:
                    decoded_items.append(self.decode_generic_dict(item))

            elif is_iterable(item) and not isinstance(item, (str, bytes)):
                decoded_items.append(self.decode_iterable(item))

            elif is_array_content(item):
                decoded_items.append(self.array_type_decoder(item))

            else:
                decoded_items.append(item)

        return type(obj)(decoded_items)

    def base_packet_decoder(self, packet: dict[str, Any]) -> dict[str, Any]:
        """Decodes a DataPacket into a DataContainer object.

        This helper extracts and decodes the shared metadata and content required
        to instantiate specific packets. It specifically handles the
        deserialization of the 'content', 'embedding', and 'generic_data' fields.

        Args:
            packet: The raw dictionary containing base packet data.

        Returns:
            dict[str, Any]: A dictionary of decoded values suitable for
                unpacking into a packet constructor.
        """
        packet_content = packet[PacketFieldNames.content]
        content = self.array_type_decoder(packet_content) if isinstance(packet_content, dict) else packet_content
        base_dict = {
            PacketFieldNames.content: content,
            BasePacketFieldNames.id: packet[BasePacketFieldNames.id],
            BasePacketFieldNames.source: packet[BasePacketFieldNames.source],
            BasePacketFieldNames.embedding: [
                self.array_type_decoder(emb) for emb in packet.get(BasePacketFieldNames.embedding, [])
            ],
            BasePacketFieldNames.generic_data: self.decode_generic_dict(packet[BasePacketFieldNames.generic_data]),
        }
        return base_dict

    def decode_image(self, packet: dict[str, Any]) -> ImagePacket:
        """Decodes a dictionary into an ImagePacket, including annotations and color space.
        """
        base_dict = self.base_packet_decoder(packet)
        return ImagePacket(
            # content=content,
            annotations=[
                ImageAnnotations(**self.decode_arrays_in_dict(ann_dict))
                for ann_dict in packet[PacketFieldNames.annotations]
            ],
            color_space=ImageColor(packet[PacketFieldNames.color_space])
            if packet[PacketFieldNames.color_space]
            else None,
            **base_dict,
        )

    def decode_audio(self, packet: dict[str, Any]) -> AudioPacket:
        """Decodes a dictionary into an AudioPacket with duration and sample rate metadata.
        """
        return AudioPacket(
            # content=cls.array_type_decoder(packet[PacketFieldNames.content]),
            sample_rate=packet[PacketFieldNames.sample_rate],
            audio_duration=packet[PacketFieldNames.audio_duration],
            annotations=[
                AudioAnnotations(**self.decode_arrays_in_dict(ann_dict))
                for ann_dict in packet.get(PacketFieldNames.annotations, [])
            ],
            # source=packet[PacketFieldNames.source],
            # id=packet[BasePacketFieldNames.id]
            **self.base_packet_decoder(packet),
        )

    def decode_text(self, packet: dict[str, Any]) -> TextPacket:
        """Decodes a dictionary into a TextPacket, maintaining text-specific annotations.
        """
        anns = packet[PacketFieldNames.annotations]
        if isinstance(anns, dict):
            anns = anns.get(PacketFieldNames.annotations, [])
        annotations = [TextAnnotations(ann) for ann in anns] if anns else []
        return TextPacket(
            # content=packet[PacketFieldNames.content],
            annotations=annotations,
            **self.base_packet_decoder(packet),
        )

    def decode_data_frame(self, packet: dict[str, Any]) -> DataFramePacket:
        """Decodes a dictionary into a DataFramePacket.
        """
        return DataFramePacket(**self.base_packet_decoder(packet))

    def decode_file(self, packet: dict[str, Any]) -> FilePacket:
        """Decodes a dictionary into a FilePacket.
        """
        return FilePacket(**self.base_packet_decoder(packet))

    def decode_time_series(self, packet: dict[str, Any]) -> TimeSeriesPacket:
        """Decodes a dictionary into a TimeSeriesPacket, including covariates and predictions.
        """
        preds = packet[PacketFieldNames.predictions]
        future_covs = packet[PacketFieldNames.future_covariates]
        past_covs = packet[PacketFieldNames.past_covariates]

        return TimeSeriesPacket(
            # content= cls.array_type_decoder(packet[PacketFieldNames.content]),
            predictions=self.array_type_decoder(preds) if preds else None,
            past_covariates=self.array_type_decoder(past_covs) if past_covs else None,
            future_covariates=self.array_type_decoder(future_covs) if future_covs else None,
            **self.base_packet_decoder(packet),
        )

    def decode_binary(self, packet: dict[str, Any]) -> BinaryPacket:
        """Decode a binary packet into a BinaryPacket object."""
        return BinaryPacket(
            # content=cls.array_type_decoder(packet[PacketFieldNames.content]),
            **self.base_packet_decoder(packet)
        )

    @classmethod
    def array_type_decoder(cls, packet_content: dict[str, Any]) -> Any:
        """The master decoder for converting serialized array data back into native objects.

        Based on the 'array_type' flag, this method handles:
        - NumPy arrays from buffer strings.
        - PyTorch tensors (including device and dtype mapping).
        - Pandas Series (via pickle) and DataFrames (via JSON split orient).
        - Darts TimeSeries objects.

        Args:
            packet_content: A dictionary representing an encoded array,
                containing keys for content, shape, dtype, and type identifier.

        Returns:
            The reconstructed numerical or tabular object.
        """
        content = packet_content[PacketFieldNames.content]
        # we check for the special case where content is replaced by file names to be fetched
        if isinstance(content, dict) and "sample" in content:
            return packet_content

        array_type = packet_content[EncodedArrayFieldNames.array_type]
        # content = packet_content[PacketFieldNames.content]

        if array_type == SupportedArrayTypeNames.bytes:
            return content

        dtype = packet_content.get(EncodedArrayFieldNames.dtype)
        shape = tuple(packet_content.get(EncodedArrayFieldNames.shape, []))

        if array_type == SupportedArrayTypeNames.numpy:
            import numpy as np

            return np.frombuffer(content, dtype=dtype).reshape(shape)

        if array_type == SupportedArrayTypeNames.torch:
            import torch

            torch_dtype = eval(dtype) if isinstance(dtype, str) else dtype
            return (
                torch.frombuffer(bytearray(content), dtype=torch_dtype)
                .reshape(shape)
                .to(packet_content.get(EncodedArrayFieldNames.device, "cpu"))
            )

        if array_type == SupportedArrayTypeNames.pd_timeseries:
            import pandas as pd

            return pd.read_pickle(io.BytesIO(content))

        if array_type == SupportedArrayTypeNames.pd_dataframe:
            import pandas as pd

            df = pd.read_json(io.StringIO(content), orient="split")
            if isinstance(dtype, dict):
                if set(dtype.keys()) == set(df.columns):
                    df = df.astype(dtype)
            elif isinstance(dtype, str):
                df = df.astype(dtype)
            return df

        if array_type == SupportedArrayTypeNames.darts_timeseries:
            import darts
            import numpy as np

            ts = darts.TimeSeries.from_json(content)
            if isinstance(dtype, str) and dtype in np.sctypeDict:
                ts = ts.astype(np.dtype(dtype))
            return ts

        sinapsis_logger.warning(f"Unsupported array type '{array_type}', not decoding")
        return packet_content

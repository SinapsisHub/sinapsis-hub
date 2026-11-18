from dataclasses import dataclass


@dataclass
class BasePacketFieldNames:
    """Data class with base fields required when encoding/decoding data packets"""

    id: str = "id"
    source: str = "source"
    embedding: str = "embedding"
    generic_data: str = "generic_data"


@dataclass
class ContainerFieldNames:
    """Data class with base fields required when encoding/decoding full data containers."""

    container_id: str = "container_id"
    images: str = "images"
    audios: str = "audios"
    texts: str = "texts"
    data_frames: str = "data_frames"
    time_series: str = "time_series"
    binary_data: str = "binary_data"
    generic_data: str = "generic_data"
    files: str = "files"


@dataclass
class PacketFieldNames:
    """Data class the names of the fields for the Packet dataclass. It includes
    some packet specific fields.
    """

    content: str = "content"
    source: str = "source"
    shape: str = "shape"
    embedding: str = "embedding"
    annotations: str = "annotations"
    color_space: str = "color_space"
    sample_rate: str = "sample_rate"
    predictions: str = "predictions"
    audio_duration: str = "audio_duration"
    segmentation: str = "segmentation"
    mask: str = "mask"
    past_covariates: str = "past_covariates"
    future_covariates: str = "future_covariates"


@dataclass
class EncodedArrayFieldNames:
    """Dataclass for the fields that the content of the packet should be encoded into"""

    type: str = "type"
    content: str = "content"
    shape: str = "shape"
    device: str = "device"
    dtype: str = "dtype"
    array_type: str = "array_type"


@dataclass
class SupportedArrayTypeNames:
    """Dataclass for the types of content the encoder/decoder support"""

    numpy: str = "numpy"
    torch: str = "torch"
    bytes: str = "bytes"
    pd_dataframe: str = "pd_dataframe"
    pd_timeseries: str = "pd_timeseries"
    darts_timeseries: str = "darts_timeseries"


@dataclass
class SupportedContentArrays:
    """Dataclass for the types of content the encoder/decoder support"""

    image = "image"
    video = "video"
    embedding = "embedding"
    timeseries = "timeseries"
    dataframe = "dataframe"
    audio = "audio"
    binary = "binary"
    file = "file"

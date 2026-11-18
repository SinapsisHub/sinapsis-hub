import os
import shutil
from abc import abstractmethod
from datetime import datetime
from typing import Any
from uuid import uuid4

import cv2
import darts
import numpy as np
import pandas as pd
import soundfile
import torch
from sinapsis.data_transport import AudioPacket, ImageColor, ImagePacket, Packet
from sinapsis_generic_data_tools.helpers.audio_encoder import audio_bytes_to_numpy

from sinapsis_serializer_core.env_vars.env_vars import STREAMING_STAGING_DIR

# streaming reps
pd.set_option("display.max_rows", 5)
pd.set_option("display.max_columns", 5)
np.set_printoptions(threshold=20)
torch.set_printoptions(threshold=20)


class StagingFileManager:
    SAMPLE_EXTENSION: str
    FULL_FILE_EXTENSION: str
    SAMPLE_SUFFIX: str = "_sample"
    FULL_FILE_SUFFIX: str = "_original"

    @staticmethod
    def make_time_stamp() -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_id = f"{timestamp}_{uuid4()}"
        return file_id

    @staticmethod
    def get_save_file_path(agent_id: str, file_id: str, suffix: str, extension: str) -> str:
        file_dir = os.path.join(STREAMING_STAGING_DIR, agent_id)
        os.makedirs(file_dir, exist_ok=True)
        full_path = os.path.join(file_dir, file_id + suffix + extension)
        return full_path

    @classmethod
    def __call__(cls, packet: Packet, agent_id: str) -> dict[str, str] | str:
        return cls.save_staging_data(packet, agent_id)

    @classmethod
    @abstractmethod
    def save_staging_data(cls, packet: Packet, agent_id: str) -> dict[str, str]:
        """Save staging data to file to disk"""
        file_id = cls.make_time_stamp()
        path = packet.content.decode() if isinstance(packet.content, bytes) else packet.content
        extension = path.split(".")[-1]
        name = path.split(".")[-2].split("/")[-1]
        original_path = cls.get_save_file_path(agent_id, file_id, name, f".{extension}")
        shutil.copy2(path, original_path)
        thumbnail_path = cls.get_save_file_path(agent_id, file_id, cls.SAMPLE_SUFFIX, ".txt")
        thumbnail = "no preview for file, please download to see"
        with open(thumbnail_path, "w") as f:
            f.write(thumbnail)
        f.close()
        return cls.make_response_content(agent_id, thumbnail_path.split(agent_id)[1], original_path.split(agent_id)[1])

    @classmethod
    def get_full_file_path(cls, agent_id: str, file_id: str) -> str:
        return cls.get_save_file_path(agent_id, file_id, cls.FULL_FILE_SUFFIX, cls.FULL_FILE_EXTENSION)

    @classmethod
    def get_sample_file_path(cls, agent_id: str, file_id: str) -> str:
        # extension = cls.SAMPLE_EXTENSION if getattr(cls, "SAMPLE_EXTENSION") else '.txt'
        return cls.get_save_file_path(agent_id, file_id, cls.SAMPLE_SUFFIX, cls.SAMPLE_EXTENSION)

    @classmethod
    def make_preview(cls, packet: Packet) -> str:
        """For most things we don't want to stream the full thing.

        We just stream the str representation of the packet.
        """
        return str(packet.content)

    @classmethod
    def make_response_content(cls, agent_id: str, sample_file_name: str, original_file_name: str) -> dict[str, str]:
        if "/" in agent_id:
            agent_id = agent_id.split("/")[-1]
        sample_path = f"{agent_id}{sample_file_name}" if sample_file_name else ""
        original_path = f"{agent_id}{original_file_name}" if original_file_name else ""
        return {"sample": sample_path, "original": original_path}


class StagingImageManager(StagingFileManager):
    SAMPLE_EXTENSION: str = ".jpg"
    FULL_FILE_EXTENSION: str = ".jpg"

    @staticmethod
    def make_preview(  # ty: ignore[invalid-method-override]
        image: np.ndarray, max_size: tuple[int, int] = (200, 200)
    ) -> np.ndarray:
        h, w = image.shape[:2]
        scale = max_size[1] / h if h > w else max_size[0] / w
        new_h = int(h * scale)
        new_w = int(w * scale)
        return cv2.resize(image, (new_w, new_h))

    @classmethod
    def save_staging_data(  # ty: ignore[invalid-method-override]
        cls, packet: ImagePacket, agent_id: str
    ) -> dict[str, str]:
        if not isinstance(packet, ImagePacket):
            raise TypeError("packet must be of type ImagePacket")

        if packet.color_space == ImageColor.RGB:
            packet.content = cv2.cvtColor(packet.content, cv2.COLOR_RGB2BGR)

        file_id = StagingFileManager.make_time_stamp()
        original_path = cls.get_full_file_path(agent_id, file_id)
        cv2.imwrite(original_path, packet.content)

        thumbnail_path = cls.get_sample_file_path(agent_id, file_id)
        thumbnail = cls.make_preview(packet.content)
        cv2.imwrite(thumbnail_path, thumbnail)

        return cls.make_response_content(agent_id, thumbnail_path.split(agent_id)[1], original_path.split(agent_id)[1])


class StagingAudioManager(StagingFileManager):
    SAMPLE_EXTENSION: str = ".ogg"
    FULL_FILE_EXTENSION: str = ".ogg"

    @classmethod
    def make_preview(cls, packet: AudioPacket) -> np.ndarray:  # ty: ignore[invalid-method-override]
        sample_rate = packet.sample_rate
        preview_length = 2  # sec
        sample_length = sample_rate * preview_length  # ty: ignore[unsupported-operator]
        preview = packet.content[:sample_length]
        return preview

    @classmethod
    def save_staging_data(  # ty: ignore[invalid-method-override]
        cls, packet: AudioPacket, agent_id: str
    ) -> dict[str, str]:
        if not isinstance(packet, AudioPacket):
            raise TypeError("packet must be of type AudioPacket")
        if isinstance(packet.content, bytes):
            packet.content, packet.sample_rate = audio_bytes_to_numpy(packet.content)
        preview = cls.make_preview(packet)
        file_id = StagingFileManager.make_time_stamp()
        original_path = cls.get_full_file_path(agent_id, file_id)

        soundfile.write(
            original_path,
            packet.content,
            packet.sample_rate,  # format="OGG",
        )
        sample_path = cls.get_sample_file_path(agent_id, file_id)
        soundfile.write(
            sample_path,
            preview,
            packet.sample_rate,  # format="OGG",
        )
        return cls.make_response_content(agent_id, sample_path.split(agent_id)[1], original_path.split(agent_id)[1])


class StagingGenericArrayManager(StagingFileManager):
    SAMPLE_EXTENSION: str = ".txt"

    @classmethod
    def make_preview(cls, content: Any) -> str:  # ty: ignore[invalid-method-override]
        if isinstance(content, (np.ndarray, pd.DataFrame, pd.Series, darts.TimeSeries)):
            return repr(content)
        elif isinstance(content, torch.Tensor):
            return f"{content}\n\t shape={content.shape}, dtype={content.dtype}"
        elif isinstance(content, str):
            return content[:20]
        else:
            return str(content)

    @classmethod
    def _save_preview(cls, agent_id: str, file_id: str, content: Any) -> str:
        """For array types we only stream a preview of the full tensor or array"""
        sample_path = cls.get_sample_file_path(agent_id, file_id)
        with open(sample_path, "w") as f:
            f.write(cls.make_preview(content))
        return sample_path

    @classmethod
    def _handle_numpy_array(cls, file_id: str, agent_id: str, content: np.ndarray) -> tuple[str, str]:
        original_path = cls.get_save_file_path(agent_id, file_id, cls.FULL_FILE_SUFFIX, ".npy")
        np.save(original_path, content)
        return original_path, cls._save_preview(agent_id, file_id, content)

    @classmethod
    def _handle_torch_tensor(cls, file_id: str, agent_id: str, content: torch.Tensor) -> tuple[str, str]:
        original_path = cls.get_save_file_path(agent_id, file_id, cls.FULL_FILE_SUFFIX, ".pt")
        torch.save(content, original_path)
        return original_path, cls._save_preview(agent_id, file_id, content)

    @classmethod
    def _handle_strings(cls, file_id: str, agent_id: str, content: str | list | dict) -> tuple[str, str]:
        original_path = cls.get_save_file_path(agent_id, file_id, cls.FULL_FILE_SUFFIX, ".txt")
        with open(original_path, "w") as f:
            f.write(str(content))
        return original_path, cls._save_preview(agent_id, file_id, content)

    @classmethod
    def _handle_generic_series_type(
        cls, file_id: str, agent_id: str, content: pd.DataFrame | pd.Series | darts.TimeSeries
    ) -> tuple[str, str]:
        original_path = cls.get_save_file_path(agent_id, file_id, cls.FULL_FILE_SUFFIX, ".csv")
        original_df = content
        if isinstance(content, darts.TimeSeries):
            original_df = content.to_dataframe()

        # original_df = pd.concat(original_df.values(), keys=original_df.keys())
        original_df.to_csv(original_path, index=True)
        return original_path, cls._save_preview(agent_id, file_id, content)

    @classmethod
    def save_staging_data(  # ty: ignore[invalid-method-override]
        cls, content: Any, agent_id: str
    ) -> dict[str, str]:
        # content = packet.content
        file_id = StagingFileManager.make_time_stamp()

        # we need to make it easy for users to reconstruct the array
        # so we don't save as bytes to avoid losing metadata
        if isinstance(content, np.ndarray):
            original_path, sample_path = cls._handle_numpy_array(file_id, agent_id, content)
        elif isinstance(content, torch.Tensor):
            original_path, sample_path = cls._handle_torch_tensor(file_id, agent_id, content)
        elif isinstance(content, (str, list, dict)):
            original_path, sample_path = cls._handle_strings(file_id, agent_id, content)

        elif isinstance(content, bytes):
            sample_path = None  # we don't do samples for byte objects
            original_path = cls.get_save_file_path(agent_id, file_id, cls.FULL_FILE_SUFFIX, ".bin")
            with open(original_path, "wb") as f:
                f.write(content)

        elif isinstance(content, (pd.DataFrame, pd.Series, darts.TimeSeries)):
            original_path, sample_path = cls._handle_generic_series_type(file_id, agent_id, content)

        else:
            raise TypeError("Unsupported content type")

        return cls.make_response_content(
            agent_id,
            sample_path.split(agent_id)[1] if sample_path else "",
            original_path.split(agent_id)[1],
        )


class StagingTimeSeriesManager(StagingGenericArrayManager):
    @classmethod
    def _handle_generic_series_type(  # ty: ignore[invalid-method-override]
        cls, file_id: str, agent_id: str, packet: Any
    ) -> tuple[str, str]:
        original_path = cls.get_save_file_path(agent_id, file_id, cls.FULL_FILE_SUFFIX, ".csv")
        original_df = packet.content
        if isinstance(packet.content, darts.TimeSeries):
            original_df = packet.content.to_dataframe()
        ATTRIBUTES = ("predictions", "future_covariates", "past_covariates")
        dfs = {"original": original_df}
        for attr in ATTRIBUTES:
            value = getattr(packet, attr, None)
            if value is None:
                continue

            if isinstance(value, darts.TimeSeries):
                value = value.to_dataframe()

            dfs[attr] = value

        original_df = pd.concat(dfs.values(), keys=dfs.keys())
        original_df.to_csv(original_path, index=True)
        return original_path, cls._save_preview(agent_id, file_id, packet)

    @classmethod
    def save_staging_data(cls, packet: Any, agent_id: str) -> dict[str, str]:  # ty: ignore[invalid-method-override]
        content = packet.content
        file_id = StagingFileManager.make_time_stamp()

        # we need to make it easy for users to reconstruct the array
        # so we don't save as bytes to avoid losing metadata
        if isinstance(content, np.ndarray):
            original_path, sample_path = cls._handle_numpy_array(file_id, agent_id, content)
        elif isinstance(content, torch.Tensor):
            original_path, sample_path = cls._handle_torch_tensor(file_id, agent_id, content)
        elif isinstance(content, (list, str)):
            original_path, sample_path = cls._handle_strings(file_id, agent_id, content)

        elif isinstance(content, bytes):
            sample_path = None  # we don't do samples for byte objects
            original_path = cls.get_save_file_path(agent_id, file_id, cls.FULL_FILE_SUFFIX, ".bin")
            with open(original_path, "wb") as f:
                f.write(content)

        elif isinstance(content, (pd.DataFrame, pd.Series, darts.TimeSeries)):
            original_path, sample_path = cls._handle_generic_series_type(file_id, agent_id, packet)

        else:
            raise TypeError("Unsupported content type")

        return cls.make_response_content(
            agent_id,
            sample_path.split(agent_id)[1] if sample_path else "",
            original_path.split(agent_id)[1],
        )


class StagingVideoManager(StagingFileManager):
    @classmethod
    def save_staging_data(cls, packet: Any, agent_id: str) -> dict[str, str]:
        raise NotImplementedError

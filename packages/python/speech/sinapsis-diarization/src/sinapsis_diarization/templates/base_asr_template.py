# -*- coding: utf-8 -*-
import os
from abc import abstractmethod
from typing import Literal, cast

from sinapsis.data_transport import AudioAnnotations, AudioPacket, DataContainer
from sinapsis.env_vars import SINAPSIS_CACHE_DIR
from sinapsis.template import Template, TemplateAttributes, TemplateAttributeType

from sinapsis_diarization.base_models.diarization_output import AudioConfig
from sinapsis_diarization.pipelines.base_processors import ASREngine


class BaseAudioAttributes(TemplateAttributes):
    device: Literal["cpu", "cuda"] = "cuda"
    sample_rate: int = 16000
    chunk_size_in_secs: int = -1
    search_window: float = 5.0
    root_dir: str | None = SINAPSIS_CACHE_DIR
    audio_file_path: str | None = None

    @property
    def full_path(self) -> str | None:
        audio_file_path = cast(str, self.audio_file_path)
        root_dir = self.root_dir if self.root_dir is not None else SINAPSIS_CACHE_DIR
        if audio_file_path is not None:
            full_path = os.path.join(root_dir, audio_file_path)
            return full_path
        return None


class BaseASRAttributes(BaseAudioAttributes):
    """
    model_name (str): name of model to run
    device (str): device to run the model
    sample_rate (int): sample rate of the audio
    chunk_size_in_secs (int): Size of the chunks to divide the audio. -1 for full audio
    search_window (float): Size of the search window
    root_dir(str): Path to root directory. Optional
    audio_file_path (str): Path to audio file. Optional
    """

    model_name: str


class SinapsisBaseASR(Template):
    """Base template for ASR pipelines"""

    AttributesBaseModel = BaseASRAttributes
    attributes: BaseASRAttributes

    def __init__(self, attributes: TemplateAttributeType):
        super().__init__(attributes)
        self.asr_pipeline: ASREngine = self.make_inference_engine()
        self.audio_config = AudioConfig(
            sample_rate=self.attributes.sample_rate,
            max_secs=self.attributes.chunk_size_in_secs,
            search_window=self.attributes.search_window,
        )

    @abstractmethod
    def make_inference_engine(self):
        """Each template implements its own logic"""

    def execute(self, container: DataContainer) -> DataContainer:
        """Call the ASR pipeline and add the information to container

        Args:
            container (DataContainer): data container

        Returns:
            DataContainer: data container with added information
        """
        full_path = self.attributes.full_path
        if full_path is not None and os.path.exists(full_path):
            audio_arr = self.asr_pipeline.get_audio_array(audio_path=full_path, config=self.audio_config)
            container.audios = [AudioPacket(content=audio_arr, sample_rate=self.audio_config.sample_rate)]

        for audio_packet in container.audios:
            if audio_packet is None:
                self.logger.warning("Audio packet is None, skipping transcription.")
                continue
            if audio_packet.sample_rate and audio_packet.sample_rate != self.attributes.sample_rate:
                self.logger.warning("Sample rate in the incoming audio is not the same as used by the model")
            transcription_text = self.asr_pipeline.transcribe(audio_arr=audio_packet.content, config=self.audio_config)
            audio_packet.annotations.append(AudioAnnotations(raw_text=transcription_text))

        return container

    def reset_state(self, template_name: str | None = None) -> None:
        """Resets the state of the template and flushes the pipeline

        Args:
            template_name (str | None, optional): template name. Defaults to None.
        """
        self.asr_pipeline.flush()
        super().reset_state(template_name)

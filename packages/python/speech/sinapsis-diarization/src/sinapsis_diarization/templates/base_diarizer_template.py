# -*- coding: utf-8 -*-
import os
from abc import abstractmethod

from sinapsis.data_transport import AudioAnnotations, AudioPacket, DataContainer
from sinapsis.env_vars import SINAPSIS_CACHE_DIR
from sinapsis.template import Template, TemplateAttributeType

from sinapsis_diarization.base_models.diarization_output import AudioConfig
from sinapsis_diarization.pipelines.base_processors import DiarizationEngine
from sinapsis_diarization.templates.base_asr_template import BaseAudioAttributes


class BaseDiarizerAttributes(BaseAudioAttributes):
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


class SinapsisBaseDiarizer(Template):
    """Base for diarizer templates"""

    AttributesBaseModel = BaseDiarizerAttributes
    attributes: BaseDiarizerAttributes

    def __init__(self, attributes: TemplateAttributeType):
        super().__init__(attributes)
        self.attributes.root_dir = self.attributes.root_dir or SINAPSIS_CACHE_DIR
        self.diarizer_pipeline: DiarizationEngine = self.make_inference_engine()
        self.audio_config = AudioConfig(
            sample_rate=self.attributes.sample_rate,
            max_secs=self.attributes.chunk_size_in_secs,
            search_window=self.attributes.search_window,
        )

    @abstractmethod
    def make_inference_engine(self):
        """Each template implements its own logic"""

    def execute(self, container: DataContainer) -> DataContainer:
        """Call the Diarization pipeline and add the information to container

        Args:
            container (DataContainer): data container

        Returns:
            DataContainer: data container with added information
        """
        full_path = self.attributes.full_path
        if full_path is not None and os.path.exists(full_path):
            audio_arr = self.diarizer_pipeline.get_audio_array(audio_path=full_path, config=self.audio_config)
            container.audios = [AudioPacket(content=audio_arr, sample_rate=self.audio_config.sample_rate)]
        for audio_packet in container.audios:
            if audio_packet is None:
                self.logger.warning("Audio packet is None, skipping diarization")
                continue
            if audio_packet.sample_rate and audio_packet.sample_rate != self.attributes.sample_rate:
                self.logger.warning("Sample rate in the incoming audio is not the same as used by the model")
            speaker_turns = self.diarizer_pipeline.diarize(audio_arr=audio_packet.content, config=self.audio_config)
            for turn in speaker_turns:
                audio_packet.annotations.append(AudioAnnotations(raw_diarization=turn))

        return container

    def reset_state(self, template_name: str | None = None) -> None:
        """Reset the state of the template and flushes the pipeline

        Args:
            template_name (str | None, optional): template name. Defaults to None.
        """
        self.diarizer_pipeline.flush()
        super().reset_state(template_name)

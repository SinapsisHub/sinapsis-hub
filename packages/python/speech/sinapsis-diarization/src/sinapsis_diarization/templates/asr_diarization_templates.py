# -*- coding: utf-8 -*-
import os
from abc import abstractmethod

from sinapsis.data_transport import AudioAnnotations, AudioPacket, DataContainer
from sinapsis.env_vars import SINAPSIS_CACHE_DIR
from sinapsis.template import OutputTypes, Template, TemplateAttributeType, UIPropertiesMetadata

from sinapsis_diarization.base_models.diarization_output import AudioConfig
from sinapsis_diarization.base_models.supported_models import (
    DEFAULT_PARAKEET_MODEL,
    DEFAULT_PYANNOTE_MODEL,
    DEFAULT_SORTFORMER_MODEL,
    PARAKEET,
    PYANNOTE,
    SORTFORMER,
    SUPPORTED_PARAKEET_MODELS,
    SUPPORTED_PYANNOTE_MODELS,
    SUPPORTED_SORTFORMER_MODELS,
)
from sinapsis_diarization.helpers.tags import Tags
from sinapsis_diarization.pipelines.asr_diarization import DiarizedTranscriptionPipeline
from sinapsis_diarization.templates.base_asr_template import BaseAudioAttributes


class DiarizedTranscriptionAttributes(BaseAudioAttributes):
    """
    root_dir(str): Path to root directory. Optional
    audio_file_path(str): Path to audio file. Optional
    asr_model_name (str): Name of the ASR pipeline to use
    diarization_model_name (str): Name of the diarization pipeline
    device (str): device to run the model
    sample_rate (int): sample rate of the audio
    chunk_size_in_secs (int): Size of the chunks to divide the audio. -1 for full audio
    search_window (float): Size of the search window
    """

    asr_model_name: SUPPORTED_PARAKEET_MODELS = DEFAULT_PARAKEET_MODEL
    diarization_model_name: SUPPORTED_SORTFORMER_MODELS | SUPPORTED_PYANNOTE_MODELS = DEFAULT_PYANNOTE_MODEL


class DiarizedTranscriptionBaseTemplate(Template):
    """Base template for ASR Diarization pipelines"""

    AttributesBaseModel = DiarizedTranscriptionAttributes
    attributes: DiarizedTranscriptionAttributes

    def __init__(self, attributes: TemplateAttributeType):
        super().__init__(attributes)
        self.attributes.root_dir = self.attributes.root_dir or SINAPSIS_CACHE_DIR
        self.pipeline: DiarizedTranscriptionPipeline = self.init_pipeline()
        self.audio_config = AudioConfig(
            sample_rate=self.attributes.sample_rate,
            max_secs=self.attributes.chunk_size_in_secs,
            search_window=self.attributes.search_window,
        )

    @abstractmethod
    def init_pipeline(self):
        """Each template implements its own logic"""

    def execute(self, container: DataContainer) -> DataContainer:
        """Call the ASR Diarization pipeline and add the information to container

        Args:
            container (DataContainer): data container

        Returns:
            DataContainer: data container with added information
        """
        full_path = self.attributes.full_path
        if full_path is not None and os.path.exists(full_path):
            audio_arr = self.pipeline.get_audio_array(audio_path=full_path, config=self.audio_config)
            container.audios = [AudioPacket(content=audio_arr, sample_rate=self.audio_config.sample_rate)]
        for audio_packet in container.audios:
            if audio_packet is None:
                self.logger.warning("Audio packet is None, skipping transcribed diarization.")
                continue
            if audio_packet.sample_rate and audio_packet.sample_rate != self.attributes.sample_rate:
                self.logger.warning("Sample rate in the incoming audio is not the same as used by the model")
            diarized_transcript = self.pipeline.transcribed_diarization(
                audio_arr=audio_packet.content, config=self.audio_config
            )
            if self.attributes.audio_file_path:
                diarized_transcript = diarized_transcript.model_copy(
                    update={"filename": self.attributes.audio_file_path}
                )
            audio_packet.annotations.append(AudioAnnotations(diarized_transcript=diarized_transcript))

        return container

    def reset_state(self, template_name: str | None = None) -> None:
        """Resets the state of the template and flushes the pipeline

        Args:
            template_name (str | None, optional): template name. Defaults to None.
        """
        self.pipeline.flush_all()
        super().reset_state(template_name)


class ParakeetPyannoteAttributes(DiarizedTranscriptionAttributes):
    """num_speakers (int): Number of speakers to predict"""

    num_speakers: int = 2
    asr_model_name: SUPPORTED_PARAKEET_MODELS = DEFAULT_PARAKEET_MODEL
    diarization_model_name: SUPPORTED_PYANNOTE_MODELS = DEFAULT_PYANNOTE_MODEL


class PyannoteDiarizedTranscription(DiarizedTranscriptionBaseTemplate):
    """Template that runs an ASR with Diarization pipeline with Parakeet as ASR engine
    and Pyannote as Diarization engine

    Supported models:
    Parakeet
    -'nvidia/parakeet-tdt-0.6b-v2'
    -'nvidia/parakeet-tdt-0.6b-v3'
    Pyannote
    -'pyannote/speaker-diarization-community-1'

    Attributes:
    root_dir(str): Path to root directory. Optional
    audio_file_path(str): Path to audio file. Optional
    asr_model_name (str): Name of the ASR pipeline to use
    diarization_model_name (str): Name of the diarization pipeline
    device (str): device to run the model
    sample_rate (int): sample rate of the audio
    chunk_size_in_secs (int): Size of the chunks to divide the audio. -1 for full audio
    search_window (float): Size of the search window
    num_speakers (int): Number of speakers to predict

    Example agent:

    agent:
        name: my_test_agent
    templates:
    - template_name: InputTemplate
    class_name: InputTemplate
    attributes: {}
    - template_name: ParakeetPyannoteDiarizedTranscription
    class_name: ParakeetPyannoteDiarizedTranscription
    template_input: InputTemplate
    attributes:
        root_dir: /root/.cache/sinapsis
        audio_file_path: null
        asr_model_name: nvidia/parakeet-tdt-0.6b-v2
        diarization_model_name: pyannote/speaker-diarization-community-1
        device: cuda
        sample_rate: 16000
        chunk_size_in_secs: -1
        search_window: 5.0
        num_speakers: 2



    """

    UIProperties = UIPropertiesMetadata(
        category="ASR",
        output_type=OutputTypes.MULTIMODAL,
        tier="enterprise",
        tags=[
            Tags.ASR,
            Tags.AUDIO,
            Tags.DIARIZATION,
            Tags.PARAKEET,
            Tags.PYANNOTE,
            Tags.SPEAKER_DIARIZATION,
            Tags.TRANSCRIPTION,
        ],
    )
    AttributesBaseModel = ParakeetPyannoteAttributes
    attributes: ParakeetPyannoteAttributes

    def init_pipeline(self) -> DiarizedTranscriptionPipeline:
        """Starts a Parakeet Pyannote diarized transcription pipeline

        Returns:
            DiarizedTranscriptionPipeline: _description_
        """
        return DiarizedTranscriptionPipeline(
            asr_pipeline=PARAKEET,
            diarization_pipeline=PYANNOTE,
            asr_model_name=self.attributes.asr_model_name,
            diarization_model_name=self.attributes.diarization_model_name,
            device=self.attributes.device,
            sample_rate=self.attributes.sample_rate,
            chunk_size_in_secs=self.attributes.chunk_size_in_secs,
            num_speakers=self.attributes.num_speakers,
        )


class ParakeetSortformerAttributes(DiarizedTranscriptionAttributes):
    """num_speakers (int): Number of speakers to predict"""

    asr_model_name: SUPPORTED_PARAKEET_MODELS = DEFAULT_PARAKEET_MODEL
    diarization_model_name: SUPPORTED_SORTFORMER_MODELS = DEFAULT_SORTFORMER_MODEL


class SortformerDiarizedTranscription(DiarizedTranscriptionBaseTemplate):
    """Template that runs an ASR with Diarization pipeline with Parakeet as ASR engine
    and Sortformer as Diarization engine

    Supported models:
    Parakeet
    -'nvidia/parakeet-tdt-0.6b-v2'
    -'nvidia/parakeet-tdt-0.6b-v3'
    Sortformer
    -'nvidia/diar_streaming_sortformer_4spk-v2.1'

    Attributes:
    root_dir(str): Path to root directory. Optional
    audio_file_path(str): Path to audio file. Optional
    asr_model_name (str): Name of the ASR pipeline to use
    diarization_model_name (str): Name of the diarization pipeline
    device (str): device to run the model
    sample_rate (int): sample rate of the audio
    chunk_size_in_secs (int): Size of the chunks to divide the audio. -1 for full audio
    search_window (float): Size of the search window
    num_speakers (int): Number of speakers to predict

    Example agent:

    agent:
        name: my_test_agent
    templates:
    - template_name: InputTemplate
    class_name: InputTemplate
    attributes: {}
    - template_name: SortformerDiarizedTranscription
    class_name: SortformerDiarizedTranscription
    template_input: InputTemplate
    attributes:
        root_dir: /root/.cache/sinapsis
        audio_file_path: null
        asr_model_name: nvidia/parakeet-tdt-0.6b-v2
        diarization_model_name: nvidia/diar_streaming_sortformer_4spk-v2.1
        device: cuda
        sample_rate: 16000
        chunk_size_in_secs: -1
        search_window: 5.0

    """

    UIProperties = UIPropertiesMetadata(
        category="ASR",
        output_type=OutputTypes.MULTIMODAL,
        tier="enterprise",
        tags=[
            Tags.ASR,
            Tags.AUDIO,
            Tags.DIARIZATION,
            Tags.PARAKEET,
            Tags.SORTFORMER,
            Tags.SPEAKER_DIARIZATION,
            Tags.TRANSCRIPTION,
        ],
    )
    AttributesBaseModel = ParakeetSortformerAttributes

    def init_pipeline(self) -> DiarizedTranscriptionPipeline:
        """Starts a Parakeet Sortformer Diarized Transcription pipeline

        Returns:
            DiarizedTranscriptionPipeline: pipeline
        """
        return DiarizedTranscriptionPipeline(
            asr_pipeline=PARAKEET,
            diarization_pipeline=SORTFORMER,
            asr_model_name=self.attributes.asr_model_name,
            diarization_model_name=self.attributes.diarization_model_name,
            device=self.attributes.device,
            sample_rate=self.attributes.sample_rate,
            chunk_size_in_secs=self.attributes.chunk_size_in_secs,
        )

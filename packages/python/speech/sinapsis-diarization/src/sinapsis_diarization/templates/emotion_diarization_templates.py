# -*- coding: utf-8 -*-
import os

from sinapsis.data_transport import AudioAnnotations, AudioPacket, DataContainer
from sinapsis.template import OutputTypes, UIPropertiesMetadata

from sinapsis_diarization.base_models.supported_models import PARAKEET, PYANNOTE, SORTFORMER, SPEECHBRAIN
from sinapsis_diarization.helpers.tags import Tags
from sinapsis_diarization.pipelines.asr_emotion_diarization import EmotionTranscriptionPipeline
from sinapsis_diarization.templates.asr_diarization_templates import (
    DiarizedTranscriptionBaseTemplate,
    ParakeetPyannoteAttributes,
    ParakeetSortformerAttributes,
)


class EmotionParakeetPyannoteAttributes(ParakeetPyannoteAttributes):
    """min_emotion_confidence (float): Minimum confidence threshold to include an emotion
    emotion_chunk_secs (float): Maximum audio duration in seconds per emotion chunk. Default 60.0
    """

    min_emotion_confidence: float = 0.5
    emotion_chunk_secs: float = 60.0


class EmotionParakeetSortformerAttributes(ParakeetSortformerAttributes):
    """min_emotion_confidence (float): Minimum confidence threshold to include an emotion
    emotion_chunk_secs (float): Maximum audio duration in seconds per emotion chunk. Default 60.0
    """

    min_emotion_confidence: float = 0.5
    emotion_chunk_secs: float = 60.0


class EmotionTranscriptionBaseTemplate(DiarizedTranscriptionBaseTemplate):
    """Base template for ASR, diarization and emotion recognition pipelines"""

    attributes: EmotionParakeetPyannoteAttributes | EmotionParakeetSortformerAttributes

    def execute(self, container: DataContainer) -> DataContainer:
        """Execute the ASR with diarization and emotion recognition pipeline

        Args:
            container (DataContainer): data container

        Returns:
            DataContainer: data container
        """
        full_path = self.attributes.full_path
        if full_path is not None and os.path.exists(full_path):
            audio_arr = self.pipeline.get_audio_array(audio_path=full_path, config=self.audio_config)
            container.audios = [AudioPacket(content=audio_arr, sample_rate=self.audio_config.sample_rate)]
        for audio_packet in container.audios:
            if audio_packet is None:
                self.logger.warning("Audio packet is None, skipping transcribed diarization and emotion recognition.")
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


class PyannoteEmotionTranscription(EmotionTranscriptionBaseTemplate):
    """Template that runs a pipeline for ASR with Diarization and Emotion Recognition
    using Parakeet as ASR, Pyannote as Diarization engine and Speechbrain as Emotion Engine.

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
    min_emotion_confidence (float): Minimum confidence threshold to include an emotion. Default 0.5

    Example agent:

    agent:
    name: my_test_agent
    templates:
    - template_name: InputTemplate
    class_name: InputTemplate
    attributes: {}
    - template_name: PyannoteEmotionTranscription
    class_name: PyannoteEmotionTranscription
    template_input: InputTemplate
    attributes:
        /root/.cache/sinapsis
        audio_file_path: null
        asr_model_name: nvidia/parakeet-tdt-0.6b-v2
        diarization_model_name: pyannote/speaker-diarization-community-1
        device: cuda
        sample_rate: 16000
        chunk_size_in_secs: -1
        search_window: 5.0
        num_speakers: 2
        min_emotion_confidence: 0.5
    """

    UIProperties = UIPropertiesMetadata(
        category="ASR",
        output_type=OutputTypes.MULTIMODAL,
        tier="enterprise",
        tags=[
            Tags.ASR,
            Tags.AUDIO,
            Tags.DIARIZATION,
            Tags.EMOTION_RECOGNITION,
            Tags.PARAKEET,
            Tags.PYANNOTE,
            Tags.SPEAKER_DIARIZATION,
            Tags.TRANSCRIPTION,
        ],
    )
    AttributesBaseModel = EmotionParakeetPyannoteAttributes
    attributes: EmotionParakeetPyannoteAttributes

    def init_pipeline(self) -> EmotionTranscriptionPipeline:
        """Starts the pipeline with Parakeet, Pyannote and Speechbrain

        Returns:
            EmotionTranscriptionPipeline: Pipeline
        """
        return EmotionTranscriptionPipeline(
            asr_pipeline=PARAKEET,
            diarization_pipeline=PYANNOTE,
            emotion_pipeline=SPEECHBRAIN,
            asr_model_name=self.attributes.asr_model_name,
            diarization_model_name=self.attributes.diarization_model_name,
            device=self.attributes.device,
            sample_rate=self.attributes.sample_rate,
            chunk_size_in_secs=self.attributes.chunk_size_in_secs,
            num_speakers=self.attributes.num_speakers,
            min_emotion_confidence=self.attributes.min_emotion_confidence,
            emotion_chunk_secs=self.attributes.emotion_chunk_secs,
        )


class SortformerEmotionTranscription(EmotionTranscriptionBaseTemplate):
    """Template that runs a pipeline for ASR with Diarization and Emotion Recognition
    using Parakeet as ASR, Sortformer as Diarization engine and Speechbrain as Emotion Engine.

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
    min_emotion_confidence (float): Minimum confidence threshold to include an emotion. Default 0.5

    Example agent:

    agent:
        name: my_test_agent
    templates:
    - template_name: InputTemplate
    class_name: InputTemplate
    attributes: {}
    - template_name: SortformerEmotionTranscription
    class_name: SortformerEmotionTranscription
    template_input: InputTemplate
    attributes:
        /root/.cache/sinapsis
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
            Tags.EMOTION_RECOGNITION,
            Tags.PARAKEET,
            Tags.SORTFORMER,
            Tags.SPEAKER_DIARIZATION,
            Tags.TRANSCRIPTION,
        ],
    )
    AttributesBaseModel = EmotionParakeetSortformerAttributes
    attributes: AttributesBaseModel

    def init_pipeline(self) -> EmotionTranscriptionPipeline:
        """Starts the pipeline with Parakeet, Sortformer and Speechbrain

        Returns:
            EmotionTranscriptionPipeline: pipeline
        """
        return EmotionTranscriptionPipeline(
            asr_pipeline=PARAKEET,
            diarization_pipeline=SORTFORMER,
            emotion_pipeline=SPEECHBRAIN,
            asr_model_name=self.attributes.asr_model_name,
            diarization_model_name=self.attributes.diarization_model_name,
            device=self.attributes.device,
            sample_rate=self.attributes.sample_rate,
            chunk_size_in_secs=self.attributes.chunk_size_in_secs,
            min_emotion_confidence=self.attributes.min_emotion_confidence,
            emotion_chunk_secs=self.attributes.emotion_chunk_secs,
        )

# -*- coding: utf-8 -*-
from typing import Literal

from sinapsis.template import OutputTypes, UIPropertiesMetadata

from sinapsis_diarization.base_models.supported_models import DEFAULT_WHISPERX_MODEL, SUPPORTED_WHISPERX_MODELS
from sinapsis_diarization.helpers.tags import Tags
from sinapsis_diarization.pipelines.whisperx_pipeline import WhisperxDiarizedTranscriptionPipeline
from sinapsis_diarization.templates.asr_diarization_templates import (
    DiarizedTranscriptionAttributes,
    DiarizedTranscriptionBaseTemplate,
)


class WhisperxDiarizedTranscriptionAttributes(DiarizedTranscriptionAttributes):
    """
    diarization_model_name (str): defaults to empty string. Unused in Whisperx pipeline
    min_speakers (int): minimum speakers to predict
    max_speakers (int): maximum speakers to predict
    """

    asr_model_name: SUPPORTED_WHISPERX_MODELS = DEFAULT_WHISPERX_MODEL
    diarization_model_name: Literal["whisperx"] = "whisperx"
    min_speakers: int = 1
    max_speakers: int = 2


class WhisperxDiarizedTranscription(DiarizedTranscriptionBaseTemplate):
    """Template that runs an ASR with Diarization pipeline with Whisperx as ASR and Diarization engine

    Attributes:
    root_dir(str): Path to root directory. Optional
    audio_file_path(str): Path to audio file. Optional
    asr_model_name (str): Name of the ASR pipeline to use
    diarization_model_name (str): Name of the diarization pipeline
    device (str): device to run the model
    sample_rate (int): sample rate of the audio
    chunk_size_in_secs (int): Size of the chunks to divide the audio. -1 for full audio
    search_window (float): Size of the search window
    diarization_model_name (str): defaults to empty string. Unused in Whisperx pipeline
    min_speakers (int): minimum speakers to predict
    max_speakers (int): maximum speakers to predict


    Example agent:

    agent:
        name: my_test_agent
    templates:
    - template_name: InputTemplate
    class_name: InputTemplate
    attributes: {}
    - template_name: WhisperxDiarizedTranscription
    class_name: WhisperxDiarizedTranscription
    template_input: InputTemplate
    attributes:
        root_dir: /root/.cache/sinapsis
        audio_file_path: null
        asr_model_name: large-v3
        diarization_model_name: whisperx
        device: cuda
        sample_rate: 16000
        chunk_size_in_secs: -1
        search_window: 5.0
        min_speakers: 1
        max_speakers: 2

    """

    UIProperties = UIPropertiesMetadata(
        category="ASR",
        output_type=OutputTypes.MULTIMODAL,
        tier="enterprise",
        tags=[Tags.ASR, Tags.AUDIO, Tags.DIARIZATION, Tags.SPEAKER_DIARIZATION, Tags.TRANSCRIPTION, Tags.WHISPERX],
    )
    AttributesBaseModel = WhisperxDiarizedTranscriptionAttributes
    attributes: AttributesBaseModel

    def init_pipeline(self):
        return WhisperxDiarizedTranscriptionPipeline(
            asr_model_name=self.attributes.asr_model_name,
            device=self.attributes.device,
            sample_rate=self.attributes.sample_rate,
            chunk_size_in_secs=self.attributes.chunk_size_in_secs,
            min_speakers=self.attributes.min_speakers,
            max_speakers=self.attributes.max_speakers,
        )

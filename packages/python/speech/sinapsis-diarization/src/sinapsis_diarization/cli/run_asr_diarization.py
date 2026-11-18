# -*- coding: utf-8 -*-

import importlib
import os
import re

from sinapsis.logging import sinapsis_logger

from sinapsis_diarization.base_models.diarization_output import AudioConfig
from sinapsis_diarization.base_models.supported_models import (
    DEFAULT_PARAKEET_MODEL,
    DEFAULT_PYANNOTE_MODEL,
    DEFAULT_SORTFORMER_MODEL,
    DEFAULT_WHISPERX_MODEL,
    PARAKEET,
    PYANNOTE,
    SORTFORMER,
)

NO_MODEL = "NO_MODEL_NAME"


def run_asr_diarization(
    audio_path: str,
    asr_model: str,
    diarization_model: str,
    chunk_size: int = -1,
    asr_model_name: str = NO_MODEL,
    diarization_model_name: str = NO_MODEL,
    device: str = "cuda",
    sample_rate: int = 16000,
    output_dir: str = "results",
    num_speakers: int = 2,
):
    """Transcribe and diarize an audio file using separate ASR and diarization engines.

    Composes an ASR engine with a diarization engine, producing a
    speaker-attributed transcript saved to *output_dir*.

    Args:
        audio_path: Path to the input audio file.
        asr_model: ASR engine type (e.g. "parakeet").
        diarization_model: Diarization engine type (e.g. "pyannote", "sortformer").
        chunk_size: Audio chunk size in seconds. -1 disables chunking.
        asr_model_name: HuggingFace ASR model identifier. Uses the engine default when not provided.
        diarization_model_name: HuggingFace diarization model identifier. Uses the engine default when not provided.
        device: Torch device string (e.g. "cpu", "cuda").
        sample_rate: Expected sample rate in Hz.
        output_dir: Directory where the output file is saved.
        num_speakers: Expected number of speakers in the audio.

    Raises:
        FileNotFoundError: If *audio_path* does not exist.
        NotImplementedError: If *asr_model* or *diarization_model* is not supported.
    """
    if not os.path.isfile(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    module = importlib.import_module("sinapsis_diarization.pipelines.asr_diarization")
    diarized_pipeline_cls = getattr(module, "DiarizedTranscriptionPipeline")
    if asr_model == PARAKEET:
        asr_model_name_input = asr_model_name if asr_model_name != NO_MODEL else DEFAULT_PARAKEET_MODEL
    else:
        raise NotImplementedError(f"{asr_model} is not an implemented model")
    if diarization_model == PYANNOTE:
        diarization_model_name_input = (
            diarization_model_name if diarization_model_name != NO_MODEL else DEFAULT_PYANNOTE_MODEL
        )
        model = diarized_pipeline_cls(
            asr_pipeline=asr_model,
            diarization_pipeline=diarization_model,
            asr_model_name=asr_model_name_input,
            diarization_model_name=diarization_model_name_input,
            device=device,
            sample_rate=sample_rate,
            chunk_size_in_secs=chunk_size,
            num_speakers=num_speakers,
        )
    elif diarization_model == SORTFORMER:
        diarization_model_name_input = (
            diarization_model_name if diarization_model_name != NO_MODEL else DEFAULT_SORTFORMER_MODEL
        )
        model = diarized_pipeline_cls(
            asr_pipeline=asr_model,
            diarization_pipeline=diarization_model,
            asr_model_name=asr_model_name_input,
            diarization_model_name=diarization_model_name_input,
            device=device,
            sample_rate=sample_rate,
            chunk_size_in_secs=chunk_size,
            num_speakers=num_speakers,
        )
    else:
        raise NotImplementedError(f"{diarization_model} is not an implemented model")
    audio_config = AudioConfig(sample_rate)
    audio_array = model.asr_pipeline.get_audio_array(audio_path)
    transcription = model.transcribed_diarization(audio_array, audio_config)
    os.makedirs(output_dir, exist_ok=True)
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", f"{asr_model}_{diarization_model}")
    output_file = os.path.join(output_dir, f"transcribed_diarization_{safe_name}.txt")
    sinapsis_logger.info(f"Results saved at {output_file}")
    with open(output_file, "w") as output_obj:
        for turn in transcription.segments:
            output_obj.write(f"{turn.speaker}: {turn.text}\n")


def run_whisperx_asr_diarization(
    audio_path: str,
    chunk_size: int = -1,
    model_name: str = NO_MODEL,
    device: str = "cuda",
    sample_rate: int = 16000,
    output_dir: str = "results",
    min_speakers: int = 2,
    max_speakers: int = 2,
):
    """Transcribe and diarize an audio file using the WhisperX pipeline.

    Uses WhisperX as a monolithic ASR + diarization engine and writes
    the speaker-attributed transcript to *output_dir*.

    Args:
        audio_path: Path to the input audio file.
        chunk_size: Audio chunk size in seconds. -1 disables chunking.
        model_name: WhisperX model size (e.g. "large-v3"). Uses the default when not provided.
        device: Torch device string (e.g. "cpu", "cuda").
        sample_rate: Expected sample rate in Hz.
        output_dir: Directory where the output file is saved.
        min_speakers: Minimum expected number of speakers.
        max_speakers: Maximum expected number of speakers.

    Raises:
        FileNotFoundError: If *audio_path* does not exist.
    """
    if not os.path.isfile(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    module = importlib.import_module("sinapsis_diarization.pipelines.whisperx_pipeline")
    whisperx_cls = getattr(module, "WhisperxDiarizedTranscriptionPipeline")
    model = whisperx_cls(
        asr_model_name=model_name if model_name != NO_MODEL else DEFAULT_WHISPERX_MODEL,
        device=device,
        sample_rate=sample_rate,
        chunk_size_in_secs=chunk_size,
        min_speakers=min_speakers,
        max_speakers=max_speakers,
    )

    audio_config = AudioConfig(sample_rate)
    audio_array = model.asr_pipeline.get_audio_array(audio_path)
    transcription = model.transcribed_diarization(audio_array, audio_config)
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "transcribed_diarization_whisperx.txt")
    sinapsis_logger.info(f"Results saved at {output_file}")
    with open(output_file, "w") as output_obj:
        for turn in transcription.segments:
            output_obj.write(f"{turn.speaker}: {turn.text}\n")

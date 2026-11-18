# -*- coding: utf-8 -*-

import importlib
import os
import re

from sinapsis.logging import sinapsis_logger

from sinapsis_diarization.base_models.diarization_output import AudioConfig
from sinapsis_diarization.base_models.supported_models import (
    CANARY,
    DEFAULT_CANARY_MODEL,
    DEFAULT_PARAKEET_MODEL,
    PARAKEET,
)
from sinapsis_diarization.pipelines.base_processors import ASREngine

NO_MODEL = "NO_MODEL_NAME"


def run_asr(
    audio_path: str,
    model: str,
    chunk_size: int = -1,
    model_name: str = NO_MODEL,
    device: str = "cuda",
    sample_rate: int = 16000,
    output_dir: str = "results",
):
    """Transcribe an audio file using a single ASR engine.

    Loads the specified ASR model, transcribes the audio, and writes
    the raw transcription text to a file in *output_dir*.

    Args:
        audio_path: Path to the input audio file.
        model: ASR engine type (e.g. "parakeet", "canary").
        chunk_size: Audio chunk size in seconds. -1 disables chunking.
        model_name: HuggingFace model identifier. Uses the engine default when not provided.
        device: Torch device string (e.g. "cpu", "cuda").
        sample_rate: Expected sample rate in Hz.
        output_dir: Directory where the transcription file is saved.

    Raises:
        FileNotFoundError: If *audio_path* does not exist.
        NotImplementedError: If *model* is not a supported ASR engine.
    """
    if not os.path.isfile(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    asr_model: ASREngine
    if model == PARAKEET:
        module = importlib.import_module("sinapsis_diarization.pipelines.parakeet_asr")
        parakeet_asr = getattr(module, "ParakeetASR")
        asr_model = parakeet_asr(
            model_name=model_name if model_name != NO_MODEL else DEFAULT_PARAKEET_MODEL,
            device=device,
            sample_rate=sample_rate,
            chunk_size_in_secs=chunk_size,
        )
    elif model == CANARY:
        module = importlib.import_module("sinapsis_diarization.pipelines.canary_asr")
        canary_transcriber = getattr(module, "CanaryTranscriber")
        asr_model = canary_transcriber(
            model_name=model_name if model_name != NO_MODEL else DEFAULT_CANARY_MODEL,
            device=device,
            sample_rate=sample_rate,
            chunk_size_in_secs=chunk_size,
        )
    else:
        raise NotImplementedError(f"{model} is not implemented")

    audio_config = AudioConfig(sample_rate)
    audio_array = asr_model.get_audio_array(audio_path)
    transcription = asr_model.transcribe(audio_array, audio_config)
    os.makedirs(output_dir, exist_ok=True)
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", model)
    output_file = os.path.join(output_dir, f"transcription_{safe_name}.txt")
    sinapsis_logger.info(f"Results saved at {output_file}")
    with open(output_file, "w") as output_obj:
        output_obj.write(transcription)

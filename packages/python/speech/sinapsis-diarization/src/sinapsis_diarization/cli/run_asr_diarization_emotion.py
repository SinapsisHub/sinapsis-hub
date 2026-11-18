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
    PARAKEET,
    PYANNOTE,
    SORTFORMER,
    SPEECHBRAIN,
)

NO_MODEL = "NO_MODEL_NAME"


def run_asr_diarization_emotion(
    audio_path: str,
    asr_model: str,
    diarization_model: str,
    emotion_model: str = SPEECHBRAIN,
    chunk_size: int = -1,
    asr_model_name: str = NO_MODEL,
    diarization_model_name: str = NO_MODEL,
    device: str = "cuda",
    sample_rate: int = 16000,
    output_dir: str = "results",
    num_speakers: int = 2,
):
    """Transcribe, diarize, and detect emotions in an audio file.

    Composes ASR, diarization, and emotion detection engines, producing
    a speaker-attributed transcript with per-segment emotions saved to
    *output_dir*.

    Args:
        audio_path: Path to the input audio file.
        asr_model: ASR engine type (e.g. "parakeet").
        diarization_model: Diarization engine type (e.g. "pyannote", "sortformer").
        emotion_model: Emotion detection engine type (e.g. "speechbrain").
        chunk_size: Audio chunk size in seconds. -1 disables chunking.
        asr_model_name: HuggingFace ASR model identifier. Uses the engine default when not provided.
        diarization_model_name: HuggingFace diarization model identifier. Uses the engine default when not provided.
        device: Torch device string (e.g. "cpu", "cuda").
        sample_rate: Expected sample rate in Hz.
        output_dir: Directory where the output file is saved.
        num_speakers: Expected number of speakers in the audio.

    Raises:
        FileNotFoundError: If *audio_path* does not exist.
        NotImplementedError: If *asr_model*, *diarization_model*, or *emotion_model* is not supported.
    """
    if not os.path.isfile(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    module = importlib.import_module("sinapsis_diarization.pipelines.asr_emotion_diarization")
    emotion_pipeline_cls = getattr(module, "EmotionTranscriptionPipeline")
    if asr_model == PARAKEET:
        asr_model_name_input = asr_model_name if asr_model_name != NO_MODEL else DEFAULT_PARAKEET_MODEL
    else:
        raise NotImplementedError(f"{asr_model} is not an implemented model")
    if emotion_model != SPEECHBRAIN:
        raise NotImplementedError(f"{emotion_model} is not an implemented model")
    if diarization_model == PYANNOTE:
        diarization_model_name_input = (
            diarization_model_name if diarization_model_name != NO_MODEL else DEFAULT_PYANNOTE_MODEL
        )
        model = emotion_pipeline_cls(
            asr_pipeline=asr_model,
            diarization_pipeline=diarization_model,
            emotion_pipeline=emotion_model,
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
        model = emotion_pipeline_cls(
            asr_pipeline=asr_model,
            diarization_pipeline=diarization_model,
            emotion_pipeline=emotion_model,
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
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", f"{asr_model}_{diarization_model}_{emotion_model}")
    output_file = os.path.join(output_dir, f"transcribed_diarization_{safe_name}.txt")
    sinapsis_logger.info(f"Results saved at {output_file}")
    with open(output_file, "w") as output_obj:
        for turn in transcription.segments:
            emotions = ""
            for emotion in turn.emotions or []:
                emotions = emotions + " " + emotion.name
                if emotion.confidence is not None:
                    emotions = emotions + ": " + str(emotion.confidence)
            output_obj.write(f"{turn.speaker}: {turn.text}, emotions: {emotions}\n")

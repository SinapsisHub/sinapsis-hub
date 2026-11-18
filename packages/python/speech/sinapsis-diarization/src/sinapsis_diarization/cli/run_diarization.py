# -*- coding: utf-8 -*-

import importlib
import os
import re

from sinapsis.logging import sinapsis_logger

from sinapsis_diarization.base_models.diarization_output import AudioConfig
from sinapsis_diarization.base_models.supported_models import (
    DEFAULT_PYANNOTE_MODEL,
    DEFAULT_SORTFORMER_MODEL,
    PYANNOTE,
    SORTFORMER,
)
from sinapsis_diarization.pipelines.base_processors import DiarizationEngine

NO_MODEL = "NO_MODEL_NAME"


def run_diarization(
    audio_path: str,
    model: str,
    chunk_size: int = -1,
    model_name: str = NO_MODEL,
    device: str = "cuda",
    sample_rate: int = 16000,
    output_dir: str = "results",
):
    """Diarize an audio file using a single diarization engine.

    Loads the specified diarization model, identifies speaker turns,
    and writes the speaker segments to a file in *output_dir*.

    Args:
        audio_path: Path to the input audio file.
        model: Diarization engine type (e.g. "pyannote", "sortformer").
        chunk_size: Audio chunk size in seconds. -1 disables chunking.
        model_name: HuggingFace model identifier. Uses the engine default when not provided.
        device: Torch device string (e.g. "cpu", "cuda").
        sample_rate: Expected sample rate in Hz.
        output_dir: Directory where the diarization file is saved.

    Raises:
        FileNotFoundError: If *audio_path* does not exist.
        NotImplementedError: If *model* is not a supported diarization engine.
    """
    if not os.path.isfile(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    diarization_model: DiarizationEngine
    if model == SORTFORMER:
        module = importlib.import_module("sinapsis_diarization.pipelines.sortformer_diarizer")
        sortformer_engine = getattr(module, "SortformerEngine")
        diarization_model = sortformer_engine(
            model_name=model_name if model_name != NO_MODEL else DEFAULT_SORTFORMER_MODEL,
            device=device,
            sample_rate=sample_rate,
            chunk_size_in_secs=chunk_size,
        )
    elif model == PYANNOTE:
        module = importlib.import_module("sinapsis_diarization.pipelines.pyannote_diarizer")
        pyannote_engine = getattr(module, "PyannoteEngine")
        diarization_model = pyannote_engine(
            model_name=model_name if model_name != NO_MODEL else DEFAULT_PYANNOTE_MODEL,
            device=device,
            sample_rate=sample_rate,
            chunk_size_in_secs=chunk_size,
        )
    else:
        raise NotImplementedError(f"{model} is not implemented")

    audio_config = AudioConfig(sample_rate)
    audio_array = diarization_model.get_audio_array(audio_path)
    diarization = diarization_model.diarize(audio_array, audio_config)
    os.makedirs(output_dir, exist_ok=True)
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", model)
    output_file = os.path.join(output_dir, f"diarization_{safe_name}.txt")
    sinapsis_logger.info(f"Results saved at {output_file}")
    with open(output_file, "w") as output_obj:
        for turn in diarization:
            output_obj.write(f"{turn.speaker}: start:{turn.start_time}, end: {turn.end_time}\n")

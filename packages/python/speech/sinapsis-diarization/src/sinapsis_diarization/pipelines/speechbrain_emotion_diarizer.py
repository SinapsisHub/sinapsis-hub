# -*- coding: utf-8 -*-
from typing import Literal

from sinapsis.data_transport import PredictedEmotion, TranscriptSegment
from sinapsis.env_vars import SINAPSIS_CACHE_DIR
from speechbrain.inference.diarization import Speech_Emotion_Diarization

from sinapsis_diarization.base_models.supported_models import DEFAULT_SPEECHBRAIN_MODEL
from sinapsis_diarization.pipelines.base_processors import BaseEmotionEngine

EMOTION_LABEL_MAP = {"n": "Neutral", "h": "Happy", "s": "Sad", "a": "Angry"}


class SpeechbrainEmotionEngine(BaseEmotionEngine):
    """Pipeline for Speechbrain Emotion Recognition"""

    model: Speech_Emotion_Diarization

    def __init__(self, device: Literal["cpu", "cuda"] = "cuda", sample_rate: int = 16000):
        super().__init__(device=device, sample_rate=sample_rate)

    def _load_model_weights(self) -> Speech_Emotion_Diarization:
        """Loads a Speechbrain emotion recognition model

        Returns:
            Speech_Emotion_Diarization: Speechbrain model
        """
        if self.device == "cuda":
            model = Speech_Emotion_Diarization.from_hparams(
                source=DEFAULT_SPEECHBRAIN_MODEL, savedir=SINAPSIS_CACHE_DIR, run_opts={"device": self.device}
            )
        else:
            model = Speech_Emotion_Diarization.from_hparams(
                source=DEFAULT_SPEECHBRAIN_MODEL, savedir=SINAPSIS_CACHE_DIR
            )
        return model

    def _inference(self, audio_path: str) -> list[TranscriptSegment]:
        """Gets emotion by segments from an audio

        Args:
            audio_path (str): path to audio

        Returns:
            list[TranscriptSegment]: list of emotion segments
        """
        diarization_result: dict[str, list[dict]] = self.model.diarize_file(audio_path)

        segments = []
        for segment in diarization_result[audio_path]:
            emotion_full = EMOTION_LABEL_MAP.get(segment["emotion"], segment["emotion"])
            segments.append(
                TranscriptSegment(
                    text="",
                    start_time=segment["start"],
                    end_time=segment["end"],
                    emotions=[PredictedEmotion(name=emotion_full)],
                )
            )

        return segments

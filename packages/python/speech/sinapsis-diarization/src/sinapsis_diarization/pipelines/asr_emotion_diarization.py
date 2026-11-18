# -*- coding: utf-8 -*-
from typing import Literal

import numpy as np
from sinapsis.data_transport import DiarizedTranscript, PredictedEmotion, TranscriptSegment

from sinapsis_diarization.base_models.diarization_output import AudioConfig
from sinapsis_diarization.base_models.supported_models import (
    SPEECHBRAIN,
    SUPPORTED_ASR_ENGINES,
    SUPPORTED_DIARIZER_ENGINES,
    SUPPORTED_EMOTION_ENGINES,
    SUPPORTED_PARAKEET_MODELS,
    SUPPORTED_PYANNOTE_MODELS,
    SUPPORTED_SORTFORMER_MODELS,
)
from sinapsis_diarization.pipelines.asr_diarization import DiarizedTranscriptionPipeline
from sinapsis_diarization.pipelines.base_processors import BaseEmotionEngine
from sinapsis_diarization.pipelines.context_manager import ManagedAudio
from sinapsis_diarization.pipelines.speechbrain_emotion_diarizer import SpeechbrainEmotionEngine


class EmotionTranscriptionPipeline(DiarizedTranscriptionPipeline):
    """Pipeline that combines Automatic Speech Recognition, Diarization and Emotion Recognition"""

    emotion_pipeline: BaseEmotionEngine
    EMOTION_OVERLAP_SECS: float = 5.0

    def __init__(
        self,
        asr_pipeline: SUPPORTED_ASR_ENGINES,
        diarization_pipeline: SUPPORTED_DIARIZER_ENGINES,
        emotion_pipeline: SUPPORTED_EMOTION_ENGINES,
        asr_model_name: SUPPORTED_PARAKEET_MODELS,
        diarization_model_name: SUPPORTED_SORTFORMER_MODELS | SUPPORTED_PYANNOTE_MODELS,
        device: Literal["cpu", "cuda"] = "cuda",
        sample_rate: int = 16000,
        chunk_size_in_secs: int = -1,
        num_speakers: int = 2,
        min_emotion_confidence: float = 0.5,
        emotion_chunk_secs: float = 60.0,
    ):
        super().__init__(
            asr_pipeline=asr_pipeline,
            diarization_pipeline=diarization_pipeline,
            asr_model_name=asr_model_name,
            diarization_model_name=diarization_model_name,
            device=device,
            sample_rate=sample_rate,
            chunk_size_in_secs=chunk_size_in_secs,
            num_speakers=num_speakers,
        )
        self.min_emotion_confidence = min_emotion_confidence
        self.emotion_chunk_secs = emotion_chunk_secs
        self.emotion_pipeline = self.init_emotion_pipeline(emotion_pipeline)

    def init_emotion_pipeline(self, emotion_pipeline: str) -> BaseEmotionEngine:
        """Chooses the emotion pipeline to initialize

        Args:
            emotion_pipeline (str): Name of the emotion pipeline

        Returns:
            BaseEmotionEngine: _description_
        """
        if emotion_pipeline == SPEECHBRAIN:
            return SpeechbrainEmotionEngine(
                device=self.device,  # ty: ignore[invalid-argument-type]
                sample_rate=self.sample_rate,
            )
        raise ValueError(f"{emotion_pipeline} is not an implemented emotion engine")

    def _get_emotion_segments(self, audio_arr: np.ndarray) -> list[TranscriptSegment]:
        """Run emotion recognition on the audio, chunking with overlap for large files.

        For audio shorter than emotion_chunk_secs, runs on the full audio.
        For longer audio, splits into overlapping chunks and keeps only the interior
        (non-overlapping) predictions from each chunk to avoid boundary artifacts.

        Args:
            audio_arr (np.ndarray): audio array

        Returns:
            list[TranscriptSegment]: emotion segments with absolute timestamps
        """
        total_duration = len(audio_arr) / self.sample_rate
        overlap = self.EMOTION_OVERLAP_SECS

        if total_duration <= self.emotion_chunk_secs:
            with ManagedAudio(audio_arr, sample_rate=self.sample_rate, return_path=True) as audio_path:
                return self.emotion_pipeline._inference(audio_path)  # ty: ignore[invalid-argument-type]

        step = self.emotion_chunk_secs - overlap
        emotion_segments: list[TranscriptSegment] = []
        chunk_start = 0.0

        while chunk_start < total_duration:
            chunk_end = min(chunk_start + self.emotion_chunk_secs, total_duration)
            is_first = chunk_start == 0.0
            is_last = chunk_end >= total_duration

            s_idx = int(chunk_start * self.sample_rate)
            e_idx = int(chunk_end * self.sample_rate)
            chunk_audio = audio_arr[s_idx:e_idx]

            with ManagedAudio(chunk_audio, sample_rate=self.sample_rate, return_path=True) as audio_path:
                chunk_segments = self.emotion_pipeline._inference(audio_path)  # ty: ignore[invalid-argument-type]

            # Define the trusted region: discard the overlap margins where
            # boundary artifacts occur. First chunk keeps the leading edge,
            # last chunk keeps the trailing edge.
            half_overlap = overlap / 2
            trust_start = 0.0 if is_first else half_overlap
            trust_end = (chunk_end - chunk_start) if is_last else (chunk_end - chunk_start) - half_overlap

            for seg in chunk_segments:
                if seg.end_time <= trust_start or seg.start_time >= trust_end:
                    continue
                # Clamp to trusted region and shift to absolute time
                seg.start_time = max(seg.start_time, trust_start) + chunk_start
                seg.end_time = min(seg.end_time, trust_end) + chunk_start
                emotion_segments.append(seg)

            chunk_start += step

        return emotion_segments

    def transcribed_diarization(self, audio_arr: np.ndarray, config: AudioConfig = AudioConfig()) -> DiarizedTranscript:
        """Runs the ASR, Diarization and Emotion Recognition pipelines and aligns the results

        Args:
            audio_path_or_array (np.ndarray): path or array for audio
            config (AudioConfig): configuration for the audio

        Returns:
            DiarizedTranscript: Transcript of the audio with speaker and emotion labels
        """
        word_timestamps = []
        grouped_segments = self.prepare_audio(audio_arr, config)
        if not grouped_segments:
            return DiarizedTranscript(segments=[])

        with ManagedAudio(audio_arr, sample_rate=self.sample_rate, return_path=True) as full_audio_path:
            speakers_probs = np.asarray(self.diarization_pipeline.get_diarization_probs(full_audio_path))  # ty: ignore[invalid-argument-type]

        emotion_segments = self._get_emotion_segments(audio_arr)

        pad_secs = self.pad_samples / self.sample_rate
        for chunk in grouped_segments:
            sliced_audio = self.slice_audio(
                audio=audio_arr,
                start=chunk.start,
                end=chunk.end,
                sample_rate=self.sample_rate,
                pad_samples=self.pad_samples,
            )
            actual_start = max(0.0, chunk.start - pad_secs)
            chunk_word_ts = self.asr_pipeline.get_asr_timestamps(sliced_audio)
            for w in chunk_word_ts:
                w["start"] += actual_start
                w["end"] += actual_start
            word_timestamps.extend(chunk_word_ts)

        # 2. Tokenize into sentences
        sentences = self._tokenize_sentences(word_timestamps)

        # 3. Align and return
        script = self._align_sentences_to_speakers(sentences, word_timestamps, speakers_probs)
        return self._align_emotions_to_script(script, emotion_segments)

    def _align_emotions_to_script(
        self, script: DiarizedTranscript, emotion_segments: list[TranscriptSegment]
    ) -> DiarizedTranscript:
        """Aligns the emotions detected to the transcript

        Args:
            script (DiarizedTranscript): Transcript of audio
            emotion_segments (list[TranscriptSegment]): Segments of recognized emotions

        Returns:
            DiarizedTranscript: Aligned transcript with emotions.
        """
        final_segments = []
        for segment in script.segments:
            emotions = self.find_segment_emotions(
                segment.start_time, segment.end_time, emotion_segments, self.min_emotion_confidence
            )
            new_segment = TranscriptSegment(
                text=segment.text,
                speaker=segment.speaker,
                start_time=segment.start_time,
                end_time=segment.end_time,
                emotions=emotions,
            )
            final_segments.append(new_segment)
        return DiarizedTranscript(segments=final_segments)

    @staticmethod
    def find_segment_emotions(
        start: float, end: float, emotion_segments: list[TranscriptSegment], min_confidence: float = 0.5
    ) -> list[PredictedEmotion]:
        """Find emotions that appear in a given window of time, weighted by overlap duration.

        Emotions are sorted by their total overlapping duration (dominant emotion first).
        Each emotion's confidence is set to its fraction of coverage over the transcript segment.
        Emotions with confidence below min_confidence are filtered out.

        Args:
            start (float): start of time segment
            end (float): end of time segment
            emotion_segments (list[TranscriptSegment]): list of emotions and their time
            appearances
            min_confidence (float): minimum confidence threshold to include an emotion

        Returns:
            list[PredictedEmotion]: list of predicted emotions sorted by dominance
        """
        segment_duration = end - start
        if segment_duration <= 0:
            return []

        emotion_durations: dict[str, float] = {}
        for segment in emotion_segments:
            if segment.emotions and (segment.start_time < end and segment.end_time > start):
                overlap_start = max(start, segment.start_time)
                overlap_end = min(end, segment.end_time)
                overlap_duration = overlap_end - overlap_start
                if overlap_duration > 0:
                    emotion_name = segment.emotions[0].name
                    emotion_durations[emotion_name] = emotion_durations.get(emotion_name, 0.0) + overlap_duration

        emotions = [
            PredictedEmotion(name=name, confidence=round(duration / segment_duration, 2))
            for name, duration in sorted(emotion_durations.items(), key=lambda x: x[1], reverse=True)
            if round(duration / segment_duration, 2) >= min_confidence
        ]
        return emotions

    def flush_all(self):
        """Flush all the pipelines"""
        self.asr_pipeline.flush()
        self.diarization_pipeline.flush()
        self.emotion_pipeline.flush()

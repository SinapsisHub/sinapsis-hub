# -*- coding: utf-8 -*-
from typing import Any, Literal

import numpy as np
import pandas as pd
import torch
from sinapsis.data_transport import DiarizedTranscript, SpeechConstantKeys, TranscriptSegment
from whisperx.alignment import align, load_align_model
from whisperx.asr import load_model
from whisperx.audio import load_audio
from whisperx.diarize import DiarizationPipeline, assign_word_speakers
from whisperx.schema import AlignedTranscriptionResult

from sinapsis_diarization.base_models.diarization_output import AudioConfig
from sinapsis_diarization.base_models.supported_models import DEFAULT_WHISPERX_MODEL, SUPPORTED_WHISPERX_MODELS
from sinapsis_diarization.helpers.env_var_keys import DiarizationEnvVars
from sinapsis_diarization.pipelines.base_processors import (
    ASREngine,
    BaseDiarizedTranscriptionPipeline,
    DiarizationEngine,
)
from sinapsis_diarization.pipelines.context_manager import ManagedAudio


class WhisperxASREngine(ASREngine):
    def __init__(
        self,
        model_name: SUPPORTED_WHISPERX_MODELS = DEFAULT_WHISPERX_MODEL,
        device: Literal["cpu", "cuda"] = "cuda",
        sample_rate: int = 16000,
        chunk_size_in_secs: int = -1,
    ):
        self.model_name = model_name
        self.device_str = device
        super().__init__(device=device, sample_rate=sample_rate, chunk_size=chunk_size_in_secs)

    def _load_model_weights(self) -> Any:
        """Loads a whisperx ASR model

        Returns:
            Any: Whisperx model
        """
        model = load_model(self.model_name, self.device_str)
        return model

    @torch.inference_mode()
    def _inference(self, audio_path: str) -> str:  # ty: ignore[invalid-method-override]
        """Transcribes an audio as a single string

        Args:
            audio (np.ndarray): path to audio

        Returns:
            str: transcription
        """
        audio = load_audio(audio_path)
        if self.model:
            result = self.model.transcribe(audio, batch_size=1, language="en")
            segments_texts = [segment["text"] for segment in result["segments"]]
            return " ".join(segments_texts)
        return ""

    def get_asr_timestamps(self, audio: np.ndarray):
        """Not implemented for Whisperx"""
        _ = audio
        return

    @torch.inference_mode()
    def _inference_pipeline(self, audio_path: str) -> list[dict]:
        """Transcribes an audio as a list of segments for the full ASR Diarization pipeline

        Args:
            audio (np.ndarray): path to audio

        Returns:
            list[dict]: transcription segments
        """
        audio = load_audio(audio_path)
        if self.model:
            result = self.model.transcribe(audio, batch_size=1, language="en")
            return result["segments"]
        return []


class WhisperxDiarizationEngine(DiarizationEngine):
    """Pipeline for Diarization with Whisperx"""

    model: DiarizationPipeline

    def __init__(
        self,
        device: Literal["cpu", "cuda"] = "cuda",
        sample_rate: int = 16000,
        chunk_size_in_secs: int = -1,
        min_speakers: int = 1,
        max_speakers: int = 2,
    ):
        self.min_speakers = min_speakers
        self.max_speakers = max_speakers
        super().__init__(device=device, sample_rate=sample_rate, chunk_size=chunk_size_in_secs)

    def _load_model_weights(self) -> DiarizationPipeline:
        """Loads a Whisperx diarization model

        Returns:
            DiarizationPipeline: Whisperx model
        """
        model = DiarizationPipeline(token=DiarizationEnvVars.HF_TOKEN, device=self.device)
        return model

    @torch.inference_mode()
    def _inference(self, audio_path: str) -> list[list[str]]:
        """Diarizes an audio as a list of speaker turns 'start end speaker_label'

        Args:
            audio_path (str): path to audio

        Returns:
            list[list[str]]: list of speaker turns
        """
        audio = load_audio(audio_path)
        result: pd.DataFrame = self.model(  # ty: ignore[invalid-assignment]
            audio, min_speakers=self.min_speakers, max_speakers=self.max_speakers
        )
        segments: list[str] = [
            f"{float(row.start)} {float(row.end)} {row.speaker}"  # ty: ignore[unresolved-attribute]
            for row in result.itertuples()
        ]
        return [segments]

    @torch.inference_mode()
    def get_diarization_probs(self, audio_path: str) -> np.ndarray:
        """Not implemented for Whisperx"""
        _ = audio_path
        return np.array([])

    @torch.inference_mode()
    def _inference_pipeline(self, audio_path: str) -> list[list[str]] | pd.DataFrame:
        """Diarizes an audio as a DataFrame for the full ASR Diarization pipeline

        Args:
            audio_path (str): path to audio

        Returns:
            list[list[str]] | pd.DataFrame: diarization result as DataFrame for the full pipeline
        """
        audio = load_audio(audio_path)
        result: pd.DataFrame = self.model(  # ty: ignore[invalid-assignment]
            audio, min_speakers=self.min_speakers, max_speakers=self.max_speakers
        )
        return result


class WhisperxDiarizedTranscriptionPipeline(BaseDiarizedTranscriptionPipeline):
    """Pipeline for ASR and diarization with Whisperx"""

    diarization_pipeline: WhisperxDiarizationEngine
    asr_pipeline: WhisperxASREngine

    def __init__(
        self,
        asr_model_name: SUPPORTED_WHISPERX_MODELS,
        device: Literal["cpu", "cuda"] = "cuda",
        sample_rate: int = 16000,
        chunk_size_in_secs: int = -1,
        min_speakers: int = 1,
        max_speakers: int = 2,
    ):
        self.asr_model_name = asr_model_name
        self.min_speakers = min_speakers
        self.max_speakers = max_speakers
        super().__init__(
            asr_pipeline="whisperx",
            diarization_pipeline="whisperx",
            device=device,
            sample_rate=sample_rate,
            chunk_size_in_secs=chunk_size_in_secs,
        )
        # Initialize NLTK
        self.__sent_detector = self.make_sentence_tokenizer()

    def init_asr_pipeline(self, asr_pipeline: str) -> ASREngine:
        """Starts the ASR pipeline for Whisperx

        Args:
            asr_pipeline (str): name of ASR pipeline. Not used in Whisperx

        Returns:
            ASREngine: Whisperx ASR Engine
        """
        _ = asr_pipeline
        return WhisperxASREngine(
            model_name=self.asr_model_name,
            device=self.device,  # ty: ignore[invalid-argument-type]
            sample_rate=self.sample_rate,
            chunk_size_in_secs=self.chunk_size_in_secs,
        )

    def init_diarization_pipeline(self, diarization_pipeline: str) -> DiarizationEngine:
        """Starts the Diarization Pipeline for Whisperx

        Args:
            diarization_pipeline (str): name of the Diarization pipeline. Not used for Whisperx

        Returns:
            DiarizationEngine: Whisperx Diarization Pipeline
        """
        _ = diarization_pipeline
        return WhisperxDiarizationEngine(
            device=self.device,  # ty: ignore[invalid-argument-type]
            sample_rate=self.sample_rate,
            chunk_size_in_secs=self.chunk_size_in_secs,
            min_speakers=self.min_speakers,
            max_speakers=self.max_speakers,
        )

    def transcribed_diarization(self, audio_arr: np.ndarray, config: AudioConfig = AudioConfig()):
        """Transcribes, diarizes and aligns the results.

        Runs diarization on the full audio for globally consistent speaker labels,
        then chunks only the ASR and alignment steps. Word timestamps are shifted
        to global time before speaker assignment, and duplicate words at chunk
        boundaries (caused by padding overlap) are removed.

        Args:
            audio_arr (np.ndarray): audio array
            config (AudioConfig): configuration for audio. Defaults to AudioConfig()

        Returns:
            DiarizedTranscript: Base model with the transcript by speaker turn
        """
        with ManagedAudio(audio_arr, sample_rate=self.sample_rate, return_path=True) as full_audio_path:
            global_diarization = self.diarization_pipeline._inference_pipeline(full_audio_path)  # ty: ignore[invalid-argument-type]

        grouped_segments = self.prepare_audio(audio_arr, config)
        if not grouped_segments:
            self.flush_all()
            return DiarizedTranscript(segments=[])

        results = self._process_chunks(audio_arr, grouped_segments, global_diarization)  # ty: ignore[invalid-argument-type]
        diarized_transcript = self.__reconstruct_sentences(results)

        self.flush_all()
        return diarized_transcript

    def _process_chunks(self, audio_arr: np.ndarray, chunks: list, global_diarization: pd.DataFrame) -> list[dict]:
        """Runs ASR, alignment and speaker assignment per chunk, deduplicating
        overlapping words at chunk boundaries.

        Args:
            audio_arr (np.ndarray): full audio array
            chunks (list): audio chunks with start/end times
            global_diarization (pd.DataFrame): full-audio diarization result

        Returns:
            list[dict]: accumulated segments with word-level speaker labels
        """
        results: list[dict] = []
        prev_chunk_end_time = 0.0

        for chunk in chunks:
            aligned_result = self._transcribe_and_align_chunk(audio_arr, chunk)
            result = assign_word_speakers(global_diarization, aligned_result)  # ty: ignore[invalid-argument-type]
            result, prev_chunk_end_time = self._deduplicate_boundary_words(result, prev_chunk_end_time)  # ty: ignore[invalid-argument-type]
            results.extend(result["segments"])

        return results

    def _transcribe_and_align_chunk(self, audio_arr: np.ndarray, chunk) -> dict:
        """Transcribes and aligns a single audio chunk, shifting timestamps
        to global time.

        Args:
            audio_arr (np.ndarray): full audio array
            chunk: audio chunk with start/end times

        Returns:
            dict: aligned result with globally shifted timestamps
        """
        s_idx = max(0, int(chunk.start * self.sample_rate) - self.pad_samples)
        chunk_offset = s_idx / self.sample_rate

        sliced_audio = self.slice_audio(
            audio=audio_arr,
            start=chunk.start,
            end=chunk.end,
            sample_rate=self.sample_rate,
            pad_samples=self.pad_samples,
        )

        with ManagedAudio(sliced_audio, sample_rate=self.sample_rate, return_path=True) as audio_path:
            audio = load_audio(audio_path)  # ty: ignore[invalid-argument-type]
            raw_segments_asr = self.asr_pipeline._inference_pipeline(audio_path)  # ty: ignore[invalid-argument-type]
            aligned_result = self.__align(audio, raw_segments_asr)

        self._shift_timestamps(aligned_result, chunk_offset)  # ty: ignore[invalid-argument-type]
        return aligned_result  # ty: ignore[invalid-return-type]

    @staticmethod
    def _shift_timestamps(aligned_result: dict, offset: float) -> None:
        """Shifts word-level and segment-level timestamps by the given offset.

        Args:
            aligned_result (dict): aligned transcription result to mutate
            offset (float): time offset in seconds
        """
        for seg in aligned_result.get("segments", []):
            if "start" in seg:
                seg["start"] += offset
            if "end" in seg:
                seg["end"] += offset
            for w in seg.get("words", []):
                if "start" in w:
                    w["start"] += offset
                if "end" in w:
                    w["end"] += offset

    @staticmethod
    def _deduplicate_boundary_words(result: dict, prev_chunk_end_time: float) -> tuple[dict, float]:
        """Removes duplicate words at chunk boundaries caused by padding overlap.

        Args:
            result (dict): speaker-assigned transcription result
            prev_chunk_end_time (float): end time of the previous chunk's last word

        Returns:
            tuple[dict, float]: cleaned result and updated end time
        """
        for seg in result["segments"]:
            seg["words"] = [w for w in seg.get("words", []) if w.get("start", 0) >= prev_chunk_end_time - 0.05]
        result["segments"] = [s for s in result["segments"] if s.get("words")]

        if result["segments"]:
            all_ends = [w["end"] for s in result["segments"] for w in s.get("words", []) if "end" in w]
            if all_ends:
                prev_chunk_end_time = max(all_ends)

        return result, prev_chunk_end_time

    @torch.inference_mode()
    def __align(self, audio: np.ndarray, segments: list[dict]) -> AlignedTranscriptionResult:
        """Aligns transcription segments to exact word-level timestamps.

        Args:
            audio (np.ndarray): audio array
            segments (list[dict]): transcription segments

        Returns:
            dict: aligned result
        """
        model_a, metadata = load_align_model(language_code="en", device=self.device)
        result = align(
            segments,  # ty: ignore[invalid-argument-type]
            model_a,
            metadata,
            audio,
            self.device,
            return_char_alignments=False,
        )

        return result

    def __reconstruct_sentences(self, segments: list[dict]) -> DiarizedTranscript:
        """Uses NLTK to group words into sentences and assigns dominant speakers.

        Args:
            segments (list[dict]): list of segments

        Returns:
            DiarizedTranscript: Transcript with speaker label
        """
        all_words = [w for seg in segments for w in seg.get("words", []) if "start" in w]
        if not all_words:
            return DiarizedTranscript(segments=[])

        full_text = " ".join([w["word"].strip() for w in all_words])
        sentences = self.__sent_detector.tokenize(full_text)

        word_idx = 0
        final_entries = DiarizedTranscript(segments=[])

        for sentence in sentences:
            sentence_parts = sentence.split()
            sentence_data = all_words[word_idx : word_idx + len(sentence_parts)]
            word_idx += len(sentence_parts)

            if not sentence_data:
                continue

            # Duration-based majority vote for speaker
            spk_votes: dict[str, float] = {}
            for w in sentence_data:
                spk = w.get("speaker", SpeechConstantKeys.unknown_speaker_tag)
                dur = w["end"] - w["start"]
                spk_votes[spk] = spk_votes.get(spk, 0) + dur

            dominant_spk = (
                max(spk_votes, key=lambda k: spk_votes[k]) if spk_votes else SpeechConstantKeys.unknown_speaker_tag
            )

            final_entries.segments.append(
                TranscriptSegment(
                    speaker=dominant_spk,
                    start_time=sentence_data[0]["start"],
                    end_time=sentence_data[-1]["end"],
                    text=sentence.strip(),
                )
            )

        return self.__smooth_speakers(final_entries)

    def __smooth_speakers(self, entries: DiarizedTranscript) -> DiarizedTranscript:
        """Prevents rapid flickering between speakers for short durations.

        Args:
            entries (DiarizedTranscript): Transcript with speaker labels

        Returns:
            DiarizedTranscript: smoothed transcript
        """
        for i in range(1, len(entries.segments) - 1):
            prev_s = entries.segments[i - 1].speaker
            next_s = entries.segments[i + 1].speaker
            curr_s = entries.segments[i].speaker

            if (prev_s == next_s and curr_s != prev_s) and (
                entries.segments[i].end_time - entries.segments[i].start_time < 1.2
            ):
                entries.segments[i].speaker = prev_s
        return entries

# -*- coding: utf-8 -*-
import argparse


def args_parser() -> argparse.Namespace:
    """
    Arg parser for sinapsis-asr and sinapsis-diarize commands (single-model pipelines).
    """
    cli_parser = argparse.ArgumentParser(
        description="Run a single ASR or diarization model on an audio file (sinapsis-asr / sinapsis-diarize)."
    )

    cli_parser.add_argument("--audio", type=str, help="Path to audio", metavar="AUDIO_PATH", required=True)
    cli_parser.add_argument("--model", type=str, help="Type of model to run", metavar="MODEL", required=True)
    cli_parser.add_argument(
        "--chunk-size-in-secs", type=int, help="Size of chunks in seconds", default=-1, metavar="CHUNK_SIZE"
    )
    cli_parser.add_argument(
        "--model-name", type=str, help="Name of model to use", metavar="MODEL_NAME", default="NO_MODEL_NAME"
    )
    cli_parser.add_argument("--device", type=str, help="Device to run the model", metavar="DEVICE", required=True)
    cli_parser.add_argument(
        "--sample-rate", type=int, help="Sample rate of audio", default=16000, metavar="SAMPLE_RATE"
    )
    cli_parser.add_argument("--output-dir", type=str, help="Output directory for transcription", default="results")

    return cli_parser.parse_args()


def asr_diarization_args_parser() -> argparse.Namespace:
    """
    Arg parser for the sinapsis-asr-diarize command (ASR + diarization pipeline).
    """
    cli_parser = argparse.ArgumentParser(
        description="Run combined ASR and speaker diarization on an audio file (sinapsis-asr-diarize)."
    )

    cli_parser.add_argument("--audio", type=str, help="Path to audio", metavar="AUDIO_PATH", required=True)
    cli_parser.add_argument(
        "--asr-model", type=str, help="Type of ASR model to run", metavar="ASR_MODEL", required=True
    )
    cli_parser.add_argument(
        "--diarization-model",
        type=str,
        help="Type of Diarization model to run",
        metavar="DIARIZATION_MODEL",
        required=True,
    )
    cli_parser.add_argument(
        "--chunk-size-in-secs", type=int, help="Size of chunks in seconds", default=-1, metavar="CHUNK_SIZE"
    )
    cli_parser.add_argument(
        "--asr-model-name", type=str, help="Name of ASR model to use", metavar="ASR_MODEL_NAME", default="NO_MODEL_NAME"
    )
    cli_parser.add_argument(
        "--diarization-model-name",
        type=str,
        help="Name of Diarization model to use",
        metavar="DIARIZATION_MODEL_NAME",
        default="NO_MODEL_NAME",
    )
    cli_parser.add_argument("--device", type=str, help="Device to run the model", metavar="DEVICE", required=True)
    cli_parser.add_argument(
        "--sample-rate", type=int, help="Sample rate of audio", default=16000, metavar="SAMPLE_RATE"
    )
    cli_parser.add_argument("--output-dir", type=str, help="Output directory for transcription", default="results")
    cli_parser.add_argument("--num-speakers", type=int, help="Number of speakers for models that require it", default=2)

    return cli_parser.parse_args()


def whisperx_asr_diarization_args_parser() -> argparse.Namespace:
    """
    Arg parser for the sinapsis-whisperx-asr-diarize command (WhisperX pipeline).
    """
    cli_parser = argparse.ArgumentParser(
        description="Run WhisperX ASR and speaker diarization on an audio file (sinapsis-whisperx-asr-diarize)."
    )

    cli_parser.add_argument("--audio", type=str, help="Path to audio", metavar="AUDIO_PATH", required=True)
    cli_parser.add_argument("--model-name", type=str, help="Type of ASR model to run", metavar="MODEL", required=True)
    cli_parser.add_argument(
        "--chunk-size-in-secs", type=int, help="Size of chunks in seconds", default=-1, metavar="CHUNK_SIZE"
    )
    cli_parser.add_argument("--device", type=str, help="Device to run the model", metavar="DEVICE", required=True)
    cli_parser.add_argument(
        "--sample-rate", type=int, help="Sample rate of audio", default=16000, metavar="SAMPLE_RATE"
    )
    cli_parser.add_argument("--output-dir", type=str, help="Output directory for transcription", default="results")
    cli_parser.add_argument("--min-speakers", type=int, help="Minimum number of speakers", default=2)
    cli_parser.add_argument("--max-speakers", type=int, help="Maximum number of speakers", default=2)

    return cli_parser.parse_args()


def asr_diarization_emotion_args_parser() -> argparse.Namespace:
    """
    Arg parser for the sinapsis-asr-diarize-emotion command (ASR + diarization + emotion pipeline).
    """
    cli_parser = argparse.ArgumentParser(
        description=(
            "Run combined ASR, speaker diarization, and emotion detection on an audio file "
            "(sinapsis-asr-diarize-emotion)."
        )
    )

    cli_parser.add_argument("--audio", type=str, help="Path to audio", metavar="AUDIO_PATH", required=True)
    cli_parser.add_argument(
        "--asr-model", type=str, help="Type of ASR model to run", metavar="ASR_MODEL", required=True
    )
    cli_parser.add_argument(
        "--diarization-model",
        type=str,
        help="Type of Diarization model to run",
        metavar="DIARIZATION_MODEL",
        required=True,
    )
    cli_parser.add_argument(
        "--emotion-model", type=str, help="Type of Emotion model to run", metavar="EMOTION_MODEL", required=True
    )

    cli_parser.add_argument(
        "--chunk-size-in-secs", type=int, help="Size of chunks in seconds", default=-1, metavar="CHUNK_SIZE"
    )
    cli_parser.add_argument(
        "--asr-model-name", type=str, help="Name of ASR model to use", metavar="ASR_MODEL_NAME", default="NO_MODEL_NAME"
    )
    cli_parser.add_argument(
        "--diarization-model-name",
        type=str,
        help="Name of Diarization model to use",
        metavar="DIARIZATION_MODEL_NAME",
        default="NO_MODEL_NAME",
    )
    cli_parser.add_argument(
        "--emotion-model-name",
        type=str,
        help="Name of emotion model to use",
        metavar="EMOTION_MODEL_NAME",
        default="NO_MODEL_NAME",
    )
    cli_parser.add_argument("--device", type=str, help="Device to run the model", metavar="DEVICE", required=True)
    cli_parser.add_argument(
        "--sample-rate", type=int, help="Sample rate of audio", default=16000, metavar="SAMPLE_RATE"
    )
    cli_parser.add_argument("--output-dir", type=str, help="Output directory for transcription", default="results")
    cli_parser.add_argument("--num-speakers", type=int, help="Number of speakers for models that require it", default=2)

    return cli_parser.parse_args()

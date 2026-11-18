<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Diarization
<br>
</h1>

<h3 align="center">Combine speaker diarization, ASR and optional emotion signals.</h3>

## Overview

**`sinapsis-diarization`** — Speech processing templates and pipelines for transcription, speaker diarization, and emotion analysis.

A transcript without speaker attribution loses who said what. These Templates support workflows that align speech recognition with speaker segments and, optionally, additional audio analytics.

### Where it fits

The implementation offers multiple backend choices with different GPU and dependency needs. `pyannote`, `whisperx` and `emotion` extras select the relevant capabilities; not every task needs all of them.

## Installation

Requires **Python 3.13 or later**, as declared in this package’s manifest. Install the base distribution using your preferred package manager:

```bash
uv pip install sinapsis-diarization
# or
pip install sinapsis-diarization
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

| Extra | Adds / when to select it |
|---|---|
| `pyannote` | pyannote speaker diarization backend. **Dependencies:** `pyannote-audio`, `torchcodec` |
| `data-tools` | Media readers/writers or data utilities for a complete pipeline. **Dependencies:** `sinapsis-data-readers` |
| `all` | Bundle declared by this package; its manifest includes `data-tools`, `dev`, `emotion`, `pyannote`, `whisperx`. |
| `emotion` | Optional emotion analysis functionality. **Dependencies:** `ruamel-yaml`, `speechbrain` |
| `whisperx` | WhisperX transcription/alignment backend. **Dependencies:** `onnx`, `onnxruntime`, `whisperx` |
| `dev` | Development-only tooling, not a runtime feature. **Dependencies:** `ty` |

For example:

```bash
uv pip install "sinapsis-diarization[pyannote]"
```

The manifest also defines development-only dependency groups: `dev` (`pre-commit`, `ruff`, `ty`). These support source development and testing and are **not** runtime extras.

<h2 id="features">🚀 Features</h2>

<h3> Templates</h3>

The **Sinapsis Diarization** module provides multiple templates for Automatic Speech Recognition, Diarization, Emotion Recognition and combined pipelines.

<h4>Automatic Speech Recognition (ASR)</h4>

These templates provide transcriptions of audios.

- **SinapsisParakeetASR**: Runs Parakeet speech recognition for audio transcription.
- **SinapsisCanaryASR**: Runs Canary speech recognition for audio transcription

<h4>Diarization</h4>

These templates identify speakers in a conversation and their turn times during the audio.

- **SinapsisSortformerDiarizer**: Runs Sortformer to get diarization of the speakers in an audio.
- **SinapsisPyannoteDiarizer**: Runs Pyannote to get diarization of speakers in an audio.

<h4>ASR plus Diarization</h4>

These templates combine ASR with Diarization to transcribe a conversation and identify the speakers automatically.

- **PyannoteDiarizedTranscription**: Runs Parakeet and Pyannote to transcribe a conversation with speaker identification.
- **SortformerDiarizedTranscription**: Runs Parakeet and Sortformer to transcribe a conversation with speaker identification.
- **WhisperxDiarizedTranscription**: Runs Whisperx to transcribe an audio and divide it by speaker and time.

<h4>ASR plus Diarization and Emotion Recognition</h4>

These templates combine the diarized transcription templates with an emotion recognition pipeline to show the emotions detected by each speaker in the audio.

- **PyannoteEmotionTranscription**: Runs Parakeet, Pyannote and Speechbrain to transcribe an audio, divide it by speaker and assign emotions to the segments.
- **SortformerEmotionTranscription**: Runs Parakeet, Sortformer and Speechbrain to transcribe an audio, divide it by speaker and assign emotions to the segments.

Examples for template use can be found at <code>src/sinapsis_diarization/configs</code>

To get information on any of the templates use <code>uv run sinx templates docstring TemplateName</code> and substitute TemplateName for any of the sinapsis-diarization templates


<h2 id="usage-example">📚 Example usage</h2>

All templates can be run through YAML configuration files using the `sinx jobs run` command. The example below shows how to set up the **WhisperxDiarizedTranscription** template, which performs ASR and speaker diarization in a single pipeline.

Configuration attributes:
- **root_dir**: Base directory for resolving relative file paths.
- **audio_file_path**: Path to the audio file to process (relative to `root_dir`).
- **asr_model_name**: WhisperX model size. Available options: `"tiny"`, `"base"`, `"small"`, `"medium"`, `"large-v1"`, `"large-v2"`, `"large-v3"`.
- **device**: `"cuda"` or `"cpu"`.
- **chunk_size_in_secs**: Split audio into chunks of *n* seconds for processing. Use `-1` to process the full audio at once.
- **min_speakers** / **max_speakers**: Expected speaker count range.

<details>
  <summary id="docker"><strong><span style="font-size: 1.2em;">Config file</span></strong></summary>

```yaml
agent:
  name: whisperx_asr_diarization
templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}
- template_name: WhisperxDiarizedTranscription
  class_name: WhisperxDiarizedTranscription
  template_input: InputTemplate
  attributes:
    root_dir: path_to_root_dir
    audio_file_path: audio_sample.mp3
    asr_model_name: large-v3
    device: cuda
    sample_rate: 16000
    chunk_size_in_secs: 20
    min_speakers: 2
    max_speakers: 2
```
</details>

To run the agent with the config above:

```bash
sinx jobs run /path/to/sinapsis-diarization/src/sinapsis_diarization/configs/transcription_with_diarization/whisperx_asr_diarization.yaml
```

More config examples for all available templates can be found in <code>src/sinapsis_diarization/configs/</code>.


<h2 id="cli">📙 CLI</h2>

The pipelines for ASR, Diarization and Emotion diarization are available as CLI commands. Each command takes an audio file and model options as input, then writes results to a given output directory (by default <code>results</code>). Required arguments are marked with <code>(required)</code>.

<details>
  <summary id="docker"><strong><span style="font-size: 1.2em;">Sinapsis ASR</span></strong></summary>

Transcribe an audio file using a single ASR engine.

Run using <code>uv run sinapsis-asr</code>

Example:
<code>uv run sinapsis-asr --audio "path to audio" --model parakeet --chunk-size-in-secs 20 --device cuda
</code>

This command has the following options:

```bash
--audio AUDIO_PATH       Path to audio (required)
--model MODEL            Type of model to run (required)
--device DEVICE          Device to run the model (required)
--chunk-size-in-secs CHUNK_SIZE Size of chunks in seconds
--model-name MODEL_NAME  Name of model to use
--sample-rate SAMPLE_RATE Sample rate of audio
--output-dir OUTPUT_DIR  Output directory for results
```
**Models**
- "parakeet"
- "canary"

**Model names**
- Parakeet:
  - "nvidia/parakeet-tdt-0.6b-v2"
  - "nvidia/parakeet-tdt-0.6b-v3"

- Canary:
  - "nvidia/canary-qwen-2.5b"

**Device options**
- "cuda"
- "cpu"


</details>

<details>
  <summary id="docker"><strong><span style="font-size: 1.2em;">Sinapsis Diarize</span></strong></summary>

Identify speakers and their turn times in an audio file using a single diarization engine.

Run using <code>uv run sinapsis-diarize</code>

Example:
<code>uv run sinapsis-diarize --audio "path to audio" --model sortformer --chunk-size-in-secs 20 --device cuda</code>

This command has the following options:

```bash
--audio AUDIO_PATH       Path to audio (required)
--model MODEL            Type of model to run (required)
--device DEVICE          Device to run the model (required)
--chunk-size-in-secs CHUNK_SIZE Size of chunks in seconds
--model-name MODEL_NAME  Name of model to use
--sample-rate SAMPLE_RATE Sample rate of audio
--output-dir OUTPUT_DIR  Output directory for results
```
**Models**
- "sortformer"
- "pyannote"

**Model names**
- Sortformer:
  - "nvidia/diar_streaming_sortformer_4spk-v2.1"

- Pyannote:
  - "pyannote/speaker-diarization-community-1"

**Device options**
- "cuda"
- "cpu"


</details>

<details>
  <summary id="docker"><strong><span style="font-size: 1.2em;">Sinapsis ASR Diarize</span></strong></summary>

Transcribe and diarize an audio file by composing separate ASR and diarization engines. Produces a speaker-attributed transcript.

Run using <code>uv run sinapsis-asr-diarize</code>

Example:

<code>uv run sinapsis-asr-diarize --audio "path to audio" --asr-model parakeet --diarization-model sortformer --chunk-size-in-secs 20 --device cuda</code>

This command has the following options:

```bash
--audio AUDIO_PATH       Path to audio (required)
--asr-model ASR_MODEL    Type of ASR model to run (required)
--diarization-model DIARIZATION_MODEL Type of Diarization model to run (required)
--device DEVICE          Device to run the model (required)
--chunk-size-in-secs CHUNK_SIZE Size of chunks in seconds
--asr-model-name ASR_MODEL_NAME Name of ASR model to use
--diarization-model-name DIARIZATION_MODEL_NAME Name of Diarization model to use
--sample-rate SAMPLE_RATE Sample rate of audio
--output-dir OUTPUT_DIR  Output directory for results
--num-speakers NUM_SPEAKERS Number of speakers for models that require it

```
**ASR Models**
- "parakeet"
- "canary"

**Diarization Models**
- "sortformer"
- "pyannote"

**Model names**
- Parakeet:
  - "nvidia/parakeet-tdt-0.6b-v2"
  - "nvidia/parakeet-tdt-0.6b-v3"

- Canary:
  - "nvidia/canary-qwen-2.5b"

- Sortformer:
  - "nvidia/diar_streaming_sortformer_4spk-v2.1"

- Pyannote:
  - "pyannote/speaker-diarization-community-1"

**Device options**
- "cuda"
- "cpu"


</details>

<details>
  <summary id="docker"><strong><span style="font-size: 1.2em;">Sinapsis Whisperx ASR Diarize</span></strong></summary>

Transcribe and diarize an audio file using the WhisperX monolithic pipeline. Unlike <code>sinapsis-asr-diarize</code>, this uses a single model for both ASR and diarization.

Run using <code>uv run sinapsis-whisperx-asr-diarize</code>

Example:

<code>uv run sinapsis-whisperx-asr-diarize --audio "path to audio" --model-name large-v3 --chunk-size-in-secs 20 --device cuda</code>

This command has the following options:

```bash
--audio AUDIO_PATH       Path to audio (required)
--model-name MODEL       WhisperX model size (required)
--device DEVICE          Device to run the model (required)
--chunk-size-in-secs CHUNK_SIZE Size of chunks in seconds
--sample-rate SAMPLE_RATE Sample rate of audio
--output-dir OUTPUT_DIR  Output directory for results
--min-speakers MIN_SPEAKERS Minimum number of speakers
--max-speakers MAX_SPEAKERS Maximum number of speakers
```
**Model names**
- "tiny"
- "base"
- "small"
- "medium"
- "large-v1"
- "large-v2"
- "large-v3"

**Device options**
- "cuda"
- "cpu"


</details>

<details>
  <summary id="docker"><strong><span style="font-size: 1.2em;">Sinapsis ASR Diarize Emotion</span></strong></summary>

Transcribe, diarize, and detect emotions in an audio file. Composes ASR, diarization, and emotion detection engines to produce a speaker-attributed transcript with per-segment emotions.

Run using <code>uv run sinapsis-asr-diarize-emotion</code>

Example:

<code>uv run sinapsis-asr-diarize-emotion --audio "path to audio" --asr-model parakeet --diarization-model sortformer --emotion-model speechbrain --chunk-size-in-secs 20 --device cuda</code>

This command has the following options:

```bash
--audio AUDIO_PATH       Path to audio (required)
--asr-model ASR_MODEL    Type of ASR model to run (required)
--diarization-model DIARIZATION_MODEL Type of Diarization model to run (required)
--emotion-model EMOTION_MODEL Type of Emotion model to run (required)
--device DEVICE          Device to run the model (required)
--chunk-size-in-secs CHUNK_SIZE Size of chunks in seconds
--asr-model-name ASR_MODEL_NAME Name of ASR model to use
--diarization-model-name DIARIZATION_MODEL_NAME Name of Diarization model to use
--emotion-model-name EMOTION_MODEL_NAME Name of emotion model to use
--sample-rate SAMPLE_RATE Sample rate of audio
--output-dir OUTPUT_DIR  Output directory for results
--num-speakers NUM_SPEAKERS Number of speakers for models that require it

```
**ASR Models**
- "parakeet"
- "canary"

**Diarization Models**
- "sortformer"
- "pyannote"

**Emotion Models**
- "speechbrain"

**Model names**
- Parakeet:
  - "nvidia/parakeet-tdt-0.6b-v2"
  - "nvidia/parakeet-tdt-0.6b-v3"

- Canary:
  - "nvidia/canary-qwen-2.5b"

- Sortformer:
  - "nvidia/diar_streaming_sortformer_4spk-v2.1"

- Pyannote:
  - "pyannote/speaker-diarization-community-1"

**Device options**
- "cuda"
- "cpu"


</details>

## Example Agent

The following is adapted directly from the package’s shipped [`canary_asr.yaml`](src/sinapsis_diarization/configs/asr/canary_asr.yaml) configuration. Save it as `my_diarization_agent.yaml`. The example may require model checkpoints, input files, additional Template packages, or provider credentials as described in its configuration.

```yaml
agent:
  name: my_diarization_agent
templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}
- template_name: SinapsisCanaryASR
  class_name: SinapsisCanaryASR
  template_input: InputTemplate
  attributes:
    model_name: "nvidia/canary-qwen-2.5b"
    device: cuda
    chunk_size_in_secs: -1
    root_dir: path_to_root_dir
    audio_file_path: audio_sample.mp3
```

```bash
sinx jobs run my_diarization_agent.yaml
```

More configurations: [`canary_asr.yaml`](src/sinapsis_diarization/configs/asr/canary_asr.yaml), [`parakeet_asr.yaml`](src/sinapsis_diarization/configs/asr/parakeet_asr.yaml), [`sortformer_diarizer.yaml`](src/sinapsis_diarization/configs/diarization/sortformer_diarizer.yaml), [`pyannote_diarizer.yaml`](src/sinapsis_diarization/configs/diarization/pyannote_diarizer.yaml), [`parakeet_sortformer_pipeline.yaml`](src/sinapsis_diarization/configs/transcription_with_diarization/parakeet_sortformer_pipeline.yaml), [`parakeet_pyannote_pipeline.yaml`](src/sinapsis_diarization/configs/transcription_with_diarization/parakeet_pyannote_pipeline.yaml), [`whisperx_asr_diarization.yaml`](src/sinapsis_diarization/configs/transcription_with_diarization/whisperx_asr_diarization.yaml), [`parakeet_sortformer_emotion.yaml`](src/sinapsis_diarization/configs/emotion/parakeet_sortformer_emotion.yaml), [`canary_asr_packet.yaml`](src/sinapsis_diarization/configs/asr/canary_asr_packet.yaml), [`parakeet_asr_packet.yaml`](src/sinapsis_diarization/configs/asr/parakeet_asr_packet.yaml), [`parakeet_pyannote_emotion.yaml`](src/sinapsis_diarization/configs/emotion/parakeet_pyannote_emotion.yaml), [`sinapsis_parakeet_sortformer_worker.yaml`](src/sinapsis_diarization/configs/workers/sinapsis_parakeet_sortformer_worker.yaml), [`sinapsis_pyannote_emotion_worker.yaml`](src/sinapsis_diarization/configs/workers/sinapsis_pyannote_emotion_worker.yaml), [`sinapsis_sortformer_emotion_worker.yaml`](src/sinapsis_diarization/configs/workers/sinapsis_sortformer_emotion_worker.yaml) (and 11 more).

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.

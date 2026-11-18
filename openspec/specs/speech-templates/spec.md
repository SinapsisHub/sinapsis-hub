# Speech Templates

## Purpose
These packages cover text-to-speech, speech-to-speech, voice cloning, ASR, speaker diarization and emotion recognition:
- `sinapsis-csm`: Sesame CSM
- `sinapsis-f5-tts`: F5-TTS
- `sinapsis-kokoro`: Kokoro
- `sinapsis-orpheus-cpp`: Orpheus GGUF models via llama.cpp
- `sinapsis-elevenlabs`: ElevenLabs cloud API
- `sinapsis-diarization`: NVIDIA NeMo Parakeet, Canary and Sortformer; pyannote; WhisperX; SpeechBrain

These templates read text from `container.texts` and produce audio into, or consume audio from, `container.audios`.

Citations are relative to `packages/python/speech/<package>/src/<module>/`.

## Requirements

### Requirement: CSM text-to-speech
`CSMTTS` SHALL synthesize each text with `sesame/csm-1b` and append one AudioPacket per text. Each packet SHALL have `source=instance_name`. (src: sinapsis-csm templates/csm_tts.py:11-89)

#### Scenario: Defaults
- **WHEN** CSMTTS runs with default attributes
- **THEN** the sample rate SHALL be 24000 Hz
- **AND** `max_audio_length_ms` SHALL be 10000
- **AND** the device SHALL be `cpu`

### Requirement: Kokoro text-to-speech
`KokoroTTS` SHALL load `hexgrad/Kokoro-82M`, concatenate all texts, and append one 24000 Hz AudioPacket per generated chunk. (src: sinapsis-kokoro templates/kokoro_tts.py:14-116)

#### Scenario: Kokoro synthesis
- **WHEN** KokoroTTS runs on "Hello" with default attributes
- **THEN** at least one AudioPacket SHALL be appended
- **AND** the voice SHALL be `af_heart`
- **AND** `split_pattern` SHALL be `\n+`

### Requirement: F5-TTS
`F5TTSInference` SHALL invoke `f5-tts_infer-cli` once per text. `ref_audio` is a required attribute. On CLI failure, the template SHALL log the error and skip that text. (src: sinapsis-f5-tts templates/f5_tts_inference.py:67-305)

#### Scenario: CLI failure
- **WHEN** the CLI exits with an error for one text
- **THEN** the error SHALL be logged
- **AND** no AudioPacket SHALL be appended for that text

### Requirement: Orpheus text-to-speech
`OrpheusTTS` SHALL download the `model_id` GGUF file and the SNAC decoder from Hugging Face. `model_id` and `voice_id` are required. If llama.cpp fails to create its context, the template SHALL disable itself and return containers unchanged. (src: sinapsis-orpheus-cpp templates/orpheus_tts.py:70-291)

#### Scenario: Defaults
- **WHEN** the optional attributes are omitted
- **THEN** `n_ctx` SHALL be 8192
- **AND** `temperature` SHALL be 0.8

#### Scenario: Out of memory
- **WHEN** llama.cpp fails to create the context
- **THEN** the container SHALL be returned unchanged

### Requirement: ElevenLabs authentication and output
Every ElevenLabs template SHALL use `api_key`, falling back to `ELEVENLABS_API_KEY`. Generated packets SHALL overwrite `container.audios`. If no key is available, the template SHALL log an error and produce no output. (src: sinapsis-elevenlabs templates/elevenlabs_base.py:22-162)

#### Scenario: Missing key
- **GIVEN** neither `api_key` nor `ELEVENLABS_API_KEY` is set
- **WHEN** ElevenLabsTTS executes
- **THEN** an error SHALL be logged
- **AND** no audio SHALL be produced

#### Scenario: Defaults
- **WHEN** model and output format are omitted
- **THEN** the model SHALL be `eleven_turbo_v2_5`
- **AND** the output format SHALL be `mp3_44100_128`

### Requirement: ElevenLabs operations
The ElevenLabs package SHALL provide four templates:
- `ElevenLabsTTS`
- `ElevenLabsSTS`, which converts only the first audio packet
- `ElevenLabsVoiceClone`, which creates a new cloned voice on every execute
- `ElevenLabsVoiceGeneration`, which requires texts of at least 100 characters

An unknown voice name SHALL fall back to the account's first voice. (src: sinapsis-elevenlabs helpers/voice_utils.py:66-100)

#### Scenario: STS default model
- **WHEN** ElevenLabsSTS runs with default attributes
- **THEN** it SHALL use the model `eleven_multilingual_sts_v2` on `audios[0]`

### Requirement: ASR templates
`SinapsisParakeetASR` (default `nvidia/parakeet-tdt-0.6b-v2`) and `SinapsisCanaryASR` SHALL write the transcription as `AudioAnnotations(raw_text=...)`. (src: sinapsis-diarization templates/parakeet_asr_template.py:10; templates/canary_asr_template.py:10)

#### Scenario: Defaults
- **WHEN** the ASR attributes are omitted
- **THEN** the device SHALL be `cuda` and the sample rate 16000
- **AND** a sample-rate mismatch SHALL only log a warning, without resampling
- **AND** setting `chunk_size_in_secs > 0` SHALL enable Silero VAD chunking

### Requirement: Diarization templates
`SinapsisSortformerDiarizer` (4 speakers) and `SinapsisPyannoteDiarizer` SHALL write one `raw_diarization` annotation per speaker turn. Gated models SHALL authenticate with `HF_TOKEN`. (src: sinapsis-diarization templates/sortformer_diarizer_template.py:14; templates/pyannote_diarizer_template.py:20)

#### Scenario: Two speakers
- **WHEN** the Pyannote diarizer runs on a two-speaker recording
- **THEN** each speaker turn SHALL appear as a `raw_diarization` annotation

### Requirement: Diarized transcription and emotion
These templates SHALL write a `diarized_transcript` annotation:
- `PyannoteDiarizedTranscription`
- `SortformerDiarizedTranscription`
- `WhisperxDiarizedTranscription`
- `PyannoteEmotionTranscription` and `SortformerEmotionTranscription`, which also add SpeechBrain emotions with `min_emotion_confidence` 0.5

(src: sinapsis-diarization templates/asr_diarization_templates.py; templates/emotion_diarization_templates.py)

#### Scenario: Diarized transcript
- **GIVEN** a two-speaker recording
- **WHEN** PyannoteDiarizedTranscription runs
- **THEN** the audio packet SHALL carry a `diarized_transcript` with segments labelled by speaker

### Requirement: Diarization CLI scripts
`sinapsis-diarization` SHALL install these console scripts:
- `sinapsis-asr`
- `sinapsis-diarize`
- `sinapsis-asr-diarize`
- `sinapsis-whisperx-asr-diarize`
- `sinapsis-asr-diarize-emotion`

(src: packages/python/speech/sinapsis-diarization/pyproject.toml:56-61)

#### Scenario: Run ASR from shell
- **WHEN** a user runs `sinapsis-asr` on an audio file
- **THEN** the transcription SHALL be produced without writing an Agent YAML

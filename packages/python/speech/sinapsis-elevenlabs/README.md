<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Elevenlabs
<br>
</h1>

<h3 align="center">Use hosted ElevenLabs speech generation and speech-to-speech APIs.</h3>

## Overview

**`sinapsis-elevenlabs`** — Generate realistic voices from text, other speeches, and more using the Elevenlabs library.

An API-backed voice service is useful when voice generation or transformation belongs inside a larger Agent. Templates abstract request preparation and map audio results back into Sinapsis data packets.

### Where it fits

It needs a provider API key and supported endpoint access. Latency, rate limits and voice/model permissions are controlled by the provider.

## Installation

Requires **Python 3.13 or later**, as declared in this package’s manifest. Install the base distribution using your preferred package manager:

```bash
uv pip install sinapsis-elevenlabs
# or
pip install sinapsis-elevenlabs
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

| Extra | Adds / when to select it |
|---|---|
| `data-tools` | Media readers/writers or data utilities for a complete pipeline. **Dependencies:** `sinapsis-data-readers`, `sinapsis-data-writers[soundfile]` |
| `all` | Bundle declared by this package; its manifest includes `data-tools`. |

For example:

```bash
uv pip install "sinapsis-elevenlabs[data-tools]"
```

The manifest also defines development-only dependency groups: `dev` (`pre-commit`, `ruff`, `ty`). These support source development and testing and are **not** runtime extras.

<h2 id="features">🚀 Features</h2>

<h3>Templates Supported</h3>

- **ElevenLabsSTS**: Template for transforming a voice into a different character or style using the ElevenLabs Speech-to-Speech API.

    <details>
    <summary>Attributes</summary>

    - `api_key`(Optional): The API key used to authenticate with ElevenLabs' API. Although this parameter is optional in the function signature, **the API key must be provided** either through this argument or the `ELEVENLABS_API_KEY` environmental variable. If neither is provided, an error will be logged, and no speech    will be generated.
    - `model`(Optional): The model identifier to use for speech synthesis (default: `eleven_multilingual_sts_v2`). Options: `eleven_english_sts_v2`, `eleven_multilingual_sts_v2`.
    - `output_format`(Optional): The output audio format and quality (default: `mp3_44100_128`). Options: `mp3_22050_32`, `mp3_44100_32`, `mp3_44100_64`, `mp3_44100_96`, `mp3_44100_128`, `mp3_44100_192`, `pcm_16000`, `pcm_22050`, `pcm_24000`, `pcm_44100`, `ulaw_8000`.
    - `output_folder`(Optional): The folder where generated audio files will be saved (default: `SINAPSIS_CACHE_DIR/elevenlabs/ audios`).
    - `stream`(Optional): If True, the audio is returned as a stream; otherwise, saved to a file (default: `False`).
    - `streaming_latency`(Optional): Latency optimization for streaming (default: None).
    - `voice`(Optional): Voice for speech synthesis. Can be a voice ID (str), name (str), or ElevenLabs voice object (Voice) (default: None).
    - `voice_settings`(Optional):Dictionary of voice control settings:
        - `stability`: Controls voice randomness and emotional range (range: 0.0 to 1.0).
        - `similarity_boost`: Adjusts how closely the voice matches the original (range: 0.0 to 1.0).
        - `style`: Amplifies the speaker’s style, consuming more resources (range: 0.0 to 1.0).
        - `use_speaker_boost`: Increases similarity to the speaker with higher computational cost (boolean: `True` or `False`).
        - `speed`: Adjusts speech speed (range: 0.7 to 1.2, default: 1.0).
    </details>


- **ElevenLabsTTS**: Template for converting text into speech using ElevenLabs' voice models.

    <details>
    <summary>Attributes</summary>

    - `api_key`(Optional): The API key used to authenticate with ElevenLabs' API. Although this parameter is optional in the function signature, **the API key must be provided** either through this argument or the `ELEVENLABS_API_KEY` environmental variable. If neither is provided, an error will be logged, and no speech    will be generated.
    - `model`(Optional): The model identifier to use for speech synthesis (default: `eleven_turbo_v2_5`). Options: `eleven_turbo_v2_5`, `eleven_multilingual_v2`, `eleven_turbo_v2`, `eleven_monolingual_v1`, `eleven_multilingual_v1`.
    - `output_format`(Optional): The output audio format and quality (default: `mp3_44100_128`). Options: `mp3_22050_32`, `mp3_44100_32`, `mp3_44100_64`, `mp3_44100_96`, `mp3_44100_128`, `mp3_44100_192`, `pcm_16000`, `pcm_22050`, `pcm_24000`, `pcm_44100`, `ulaw_8000`.
    - `output_folder`(Optional): The folder where generated audio files will be saved (default: `SINAPSIS_CACHE_DIR/elevenlabs/audios`).
    - `stream`(Optional): If True, the audio is returned as a stream; otherwise, saved to a file (default: `False`).
    - `voice`(Optional): Voice for speech synthesis. Can be a voice ID (str), name (str), or ElevenLabs voice object (Voice) (default: None).
    - `voice_settings`(Optional):Dictionary of voice control settings:
        - `stability`: Controls voice randomness and emotional range (range: 0.0 to 1.0).
        - `similarity_boost`: Adjusts how closely the voice matches the original (range: 0.0 to 1.0).
        - `style`: Amplifies the speaker’s style, consuming more resources (range: 0.0 to 1.0).
        - `use_speaker_boost`: Increases similarity to the speaker with higher computational cost (boolean: `True` or `False`).
        - `speed`: Adjusts speech speed (range: 0.7 to 1.2, default: 1.0).
    </details>

- **ElevenLabsVoiceClone**: Template for creating a synthetic copy of an existing voice using the ElevenLabs API.

    <details>
    <summary>Attributes</summary>

    - `api_key`(Optional): The API key used to authenticate with ElevenLabs' API. Although this parameter is optional in the function signature, **the API key must be provided** either through this argument or the `ELEVENLABS_API_KEY` environmental variable. If neither is provided, an error will be logged, and no speech will be generated.
    - `description`(Optional): Description for the cloned voice (default: None).
    - `model`(Optional): The model identifier to use for speech synthesis (default: `eleven_turbo_v2_5`). Options: `eleven_turbo_v2_5`, `eleven_multilingual_v2`, `eleven_turbo_v2`, `eleven_monolingual_v1`, `eleven_multilingual_v1`.
    - `name`(Optional): Name for the cloned voice (default: None). If None, a default name may be used.
    - `output_format`(Optional): The output audio format and quality (default: `mp3_44100_128`). Options: `mp3_22050_32`, `mp3_44100_32`, `mp3_44100_64`, `mp3_44100_96`, `mp3_44100_128`, `mp3_44100_192`, `pcm_16000`, `pcm_22050`, `pcm_24000`, `pcm_44100`, `ulaw_8000`.
    - `output_folder`(Optional): The folder where generated audio files will be saved (default: `SINAPSIS_CACHE_DIR/elevenlabs/audios`).
    - `remove_background_noise`(Optional): Whether to remove background noise from samples (default: `False`).
    - `stream`(Optional): If True, the audio is returned as a stream; otherwise, saved to a file (default: `False`).
    - `voice`(Optional): Voice for speech synthesis. Can be a voice ID (str), name (str), or ElevenLabs voice object (Voice) (default: None).
    - `voice_description`(Required): A description of the voice to be used for synthesis. This field is mandatory and helps to define the voice's characteristics or style.
    - `voice_settings`(Optional):Dictionary of voice control settings:
        - `stability`: Controls voice randomness and emotional range (range: 0.0 to 1.0).
        - `similarity_boost`: Adjusts how closely the voice matches the original (range: 0.0 to 1.0).
        - `style`: Amplifies the speaker’s style, consuming more resources (range: 0.0 to 1.0).
        - `use_speaker_boost`: Increases similarity to the speaker with higher computational cost (boolean: `True` or `False`).
        - `speed`: Adjusts speech speed (range: 0.7 to 1.2, default: 1.0).
    </details>

- **ElevenLabsVoiceGeneration**: Template for generating custom synthetic voices based on user-provided descriptions.

    <details>
    <summary>Attributes</summary>

    - `api_key`(Optional): The API key used to authenticate with ElevenLabs' API. Although this parameter is optional in the function signature, **the API key must be provided** either through this argument or the `ELEVENLABS_API_KEY` environmental variable. If neither is provided, an error will be logged, and no speech will be generated.
    - `model`(Optional): The model identifier to use for speech synthesis (default: `eleven_turbo_v2_5`). Options: `eleven_turbo_v2_5`, `eleven_multilingual_v2`, `eleven_turbo_v2`, `eleven_monolingual_v1`, `eleven_multilingual_v1`.
    - `output_format`(Optional): The output audio format and quality (default: `mp3_44100_128`). Options: `mp3_22050_32`, `mp3_44100_32`, `mp3_44100_64`, `mp3_44100_96`, `mp3_44100_128`, `mp3_44100_192`, `pcm_16000`, `pcm_22050`, `pcm_24000`, `pcm_44100`, `ulaw_8000`.
    - `output_folder`(Optional): The folder where generated audio files will be saved (default: `SINAPSIS_CACHE_DIR/elevenlabs/audios`).
    - `stream`(Optional): If True, the audio is returned as a stream; otherwise, saved to a file (default: `False`).
    - `voice`(Optional): Voice for speech synthesis. Can be a voice ID (str), name (str), or ElevenLabs voice object (Voice) (default: None).
    - `voice_description`(Required): A description of the voice to be used for synthesis. This field is mandatory and helps to define the voice's characteristics or style.
    - `voice_settings`(Optional):Dictionary of voice control settings:
        - `stability`: Controls voice randomness and emotional range (range: 0.0 to 1.0).
        - `similarity_boost`: Adjusts how closely the voice matches the original (range: 0.0 to 1.0).
        - `style`: Amplifies the speaker’s style, consuming more resources (range: 0.0 to 1.0).
        - `use_speaker_boost`: Increases similarity to the speaker with higher computational cost (boolean: `True` or `False`).
        - `speed`: Adjusts speech speed (range: 0.7 to 1.2, default: 1.0).
    </details>


For example, for ***ElevenLabsTTS*** use ```sinx templates example-config ElevenLabsTTS``` to produce an example config like:

```yaml
agent:
  name: my_sinapsis_elevenlabs_agent
templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}
- template_name: ElevenLabsTTS
  class_name: ElevenLabsTTS
  template_input: InputTemplate
  attributes:
    api_key: null
    voice: null
    voice_settings:
      stability: null
      similarity_boost: null
      style: null
      use_speaker_boost: null
      speed: null
    model: eleven_turbo_v2_5
    output_format: mp3_44100_128
    output_folder: ~/.cache/sinapsis/elevenlabs/audios
    stream: false
```

## Example Agent

The following is adapted directly from the package’s shipped [`voice_generation_demo.yaml`](src/sinapsis_elevenlabs/configs/voice_generation_demo.yaml) configuration. Save it as `my_elevenlabs_agent.yaml`. The example may require model checkpoints, input files, additional Template packages, or provider credentials as described in its configuration.

```yaml
agent:
  name: my_elevenlabs_agent
  description: voice generation agent using Elevenlabs

templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}

- template_name: ElevenLabsVoiceGeneration
  class_name: ElevenLabsVoiceGeneration
  template_input: InputTemplate
  attributes:
    voice_description: A clear and professional British middle-aged male voice, smooth and well-spoken. Perfect for narrations, audiobooks, and corporate content, offering a balanced and engaging delivery.
```

```bash
sinx jobs run my_elevenlabs_agent.yaml
```

More configurations: [`voice_generation_demo.yaml`](src/sinapsis_elevenlabs/configs/voice_generation_demo.yaml), [`elevenlabs_tts_demo.yaml`](src/sinapsis_elevenlabs/configs/elevenlabs_tts_demo.yaml), [`elevenlabs_voice_clone_demo.yaml`](src/sinapsis_elevenlabs/configs/elevenlabs_voice_clone_demo.yaml), [`elevenlabs_sts_demo.yaml`](src/sinapsis_elevenlabs/configs/elevenlabs_sts_demo.yaml), [`elevenlabs_voice_generation.yaml`](src/sinapsis_elevenlabs/configs/elevenlabs_voice_generation.yaml), [`elevenlabs_tts.yaml`](src/sinapsis_elevenlabs/configs/elevenlabs_tts.yaml), [`elevenlabs_voice_clone.yaml`](src/sinapsis_elevenlabs/configs/elevenlabs_voice_clone.yaml), [`elevenlabs_sts.yaml`](src/sinapsis_elevenlabs/configs/elevenlabs_sts.yaml).

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.

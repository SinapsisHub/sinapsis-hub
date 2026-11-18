<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis F5-Tts
<br>
</h1>

<h3 align="center">Generate speech with F5-TTS, including reference-conditioned speech workflows.</h3>

## Overview

**`sinapsis-f5-tts`** — Text to speech using F5-TTS library.

Reference audio can help control a target voice without using an external TTS endpoint. A Sinapsis Template keeps this step composable with transcription, audio conditioning and result writing.

### Where it fits

Inference and reference-audio quality depend on compatible checkpoints and compute. Verify rights to the voice material you supply.

## Installation

Requires **Python 3.13 or later**, as declared in this package’s manifest. Install the base distribution using your preferred package manager:

```bash
uv pip install sinapsis-f5-tts
# or
pip install sinapsis-f5-tts
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

| Extra | Adds / when to select it |
|---|---|
| `sinapsis-data-tools` | Sinapsis data tools support. **Dependencies:** `sinapsis-data-readers`, `sinapsis-data-writers` |
| `all` | Bundle declared by this package; its manifest includes `sinapsis-data-tools`. |

For example:

```bash
uv pip install "sinapsis-f5-tts[sinapsis-data-tools]"
```

The manifest also defines development-only dependency groups: `dev` (`ruff`, `pre-commit`). These support source development and testing and are **not** runtime extras.

<h2 id="features">🚀 Features
</h2>


<h3>Templates Supported</h3>

This module includes a template for text-to-speech synthesis using the F5TTS model:

**F5TTSInference**: Converts text to speech using the F5TTS model with voice cloning capabilities. The template processes text packets from the input container, generates corresponding audio using F5TTS, and adds the resulting audio packets to the container.

<details>
<summary>Attributes</summary>

- `model`: Model name to use for inference (default: "F5TTS_v1_Base")
- `model_cfg`: Optional path to model configuration file
- `ckpt_file`: Optional path to model checkpoint file
- `vocab_file`: Optional path to vocabulary file
- `ref_audio`: Path to reference audio file for voice cloning (default: "artifacts/town.mp3")
- `ref_text`: Reference text corresponding to the reference audio (default: empty string)
- `vocoder_name`: Vocoder to use for waveform generation, either "vocos" or "bigvgan" (default: "vocos")
- `load_vocoder_from_local`: Whether to load vocoder from local path (default: False)
- `nfe_step`: Number of function evaluation steps for diffusion, higher values give better quality but slower inference (default: 32)
- `cfg_strength`: Classifier-free guidance strength, higher values give more stable output but less expressivity (default: 2.0)
- `cross_fade_duration`: Duration of cross-fade between audio segments in seconds (default: 0.15)
- `speed`: Speed factor for generated speech, values > 1 make speech faster, < 1 make it slower (default: 1.0)
- `sway_sampling_coef`: Coefficient for sway sampling (default: -1.0)
- `target_rms`: Target RMS value for audio normalization (default: None)
- `fix_duration`: Fixed duration for generated audio in seconds (default: None)
- `remove_silence`: Whether to remove silence from generated audio (default: False)
- `save_chunk`: Whether to save individual audio chunks (default: False)
- `device`: Device to use for inference, e.g., "cuda", "cpu" (default: None, auto-detect)
</details>


For example, for ***F5TTSInference*** use ```sinx templates example-config F5TTSInference``` to produce an example config like:

```yaml
agent:
  name: my_sinapsis_f5_tts_agent
templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}
- template_name: F5TTSInference
  class_name: F5TTSInference
  template_input: InputTemplate
  attributes:
    model: F5TTS_v1_Base
    model_cfg: null
    ckpt_file: null
    vocab_file: null
    ref_audio: '`replace_me:<class ''str''>`'
    ref_text: ' '
    vocoder_name: vocos
    load_vocoder_from_local: false
    nfe_step: 32
    cfg_strength: 2.0
    cross_fade_duration: 0.15
    speed: 1.0
    sway_sampling_coef: -1.0
    target_rms: null
    fix_duration: null
    remove_silence: false
    save_chunk: false
    device: null

```

## Example Agent

The following is adapted directly from the package’s shipped [`f5_tts_app.yaml`](src/sinapsis_f5_tts/configs/f5_tts_app.yaml) configuration. Save it as `my_f5_tts_agent.yaml`. The example may require model checkpoints, input files, additional Template packages, or provider credentials as described in its configuration.

```yaml
agent:
  name: my_f5_tts_agent
  description: "Agent that generates speech from text using the F5TTS template."

templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}

- template_name: F5TTSInference
  class_name: F5TTSInference
  template_input: InputTemplate
  attributes:
    model: "F5TTS_v1_Base"
    ref_audio: "artifacts/small.mp3"
    ref_text: " "
    vocoder_name: "vocos"
    nfe_step: 32
    cfg_strength: 2.0
    cross_fade_duration: 0.15
    speed: 1.0
    sway_sampling_coef: -1
```

```bash
sinx jobs run my_f5_tts_agent.yaml
```

More configurations: [`f5_tts_app.yaml`](src/sinapsis_f5_tts/configs/f5_tts_app.yaml), [`f5_tts_inference.yaml`](src/sinapsis_f5_tts/configs/f5_tts_inference.yaml).

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.

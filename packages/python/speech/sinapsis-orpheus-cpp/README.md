<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Orpheus-Cpp
<br>
</h1>

<h3 align="center">Run Orpheus speech synthesis using the C++-oriented inference stack.</h3>

## Overview

**`sinapsis-orpheus-cpp`** — Text to speech using Orpheus TTS model.

The package turns a specialised local TTS runtime into a reusable Sinapsis component. This helps pair text generation with audio output without building a separate process orchestration layer for the speech engine.

### Where it fits

Model and inference-backend installation determine hardware support and performance; check the provided examples before choosing a voice or checkpoint.

## Installation

Requires **Python 3.13 or later**, as declared in this package’s manifest. Install the base distribution using your preferred package manager:

```bash
uv pip install sinapsis-orpheus-cpp
# or
pip install sinapsis-orpheus-cpp
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

| Extra | Adds / when to select it |
|---|---|
| `data-tools` | Media readers/writers or data utilities for a complete pipeline. **Dependencies:** `sinapsis-data-readers[all]`, `sinapsis-data-writers[soundfile]` |
| `all` | Bundle declared by this package; its manifest includes `data-tools`. |

For example:

```bash
uv pip install "sinapsis-orpheus-cpp[data-tools]"
```

The manifest also defines development-only dependency groups: `dev` (`pre-commit`, `ruff`, `ty`). These support source development and testing and are **not** runtime extras.

<h2 id="features">🚀 Features
</h2>


<h3>Templates Supported</h3>

This module includes a template for text-to-speech synthesis using the Orpheus TTS model:

**OrpheusTTS**: Advanced text-to-speech synthesis template powered by Orpheus TTS, delivering human-like speech with natural intonation, emotion, and rhythm that surpasses state-of-the-art closed-source models. The template supports expressive speech synthesis through emotive tags including `<laugh>`, `<chuckle>`, `<sigh>`, `<cough>`, `<sniffle>`, `<groan>`, `<yawn>`, and `<gasp>` for enhanced vocal expressions. Additionally, it provides multi-language support when configured with the appropriate Hugging Face model path, making it versatile for global applications.

<details>
<summary>Attributes</summary>

- `n_gpu_layers`: Number of model layers to offload to GPU (-1 = use all layers, 0 = CPU only) (default: -1)
- `n_threads`: Number of CPU threads to use for model inference (0 = auto-detect) (default: 0)
- `n_ctx`: Context window size (maximum number of tokens, 0 = use model's maximum) (default: 8192)
- `model_id`: Hugging Face model repository ID (required)
- `model_variant`: Specific GGUF file to download from the repository (default: None)
- `cache_dir`: Directory to store downloaded models and cache files (default: SINAPSIS_CACHE_DIR)
- `verbose`: Enable verbose logging for model operations (default: False)
- `voice_id`: Voice identifier for speech synthesis (required)
- `batch_size`: Batch size for model inference (default: 1)
- `max_tokens`: Maximum number of tokens to generate for speech (default: 2048)
- `temperature`: Sampling temperature for token generation (default: 0.8)
- `top_p`: Nucleus sampling probability threshold (default: 0.95)
- `top_k`: Top-k sampling parameter (default: 40)
- `min_p`: Minimum probability threshold for token selection (default: 0.05)
- `pre_buffer_size`: Duration in seconds of audio to generate before yielding the first chunk (default: 1.5)

</details>


For example, for ***OrpheusTTS*** use ```sinx templates example-config OrpheusTTS``` to produce an example config like:

```yaml
agent:
  name: my_sinapsis_orpheus_cpp_agent
templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}
- template_name: OrpheusTTS
  class_name: OrpheusTTS
  template_input: InputTemplate
  attributes:
    n_gpu_layers: -1
    n_threads: 0
    n_ctx: 8192
    model_id: '`replace_me:<class ''str''>`'
    model_variant: null
    cache_dir: ~/sinapsis_cache
    verbose: false
    voice_id: '`replace_me:<class ''str''>`'
    batch_size: 1
    max_tokens: 2048
    temperature: 0.8
    top_p: 0.95
    top_k: 40
    min_p: 0.05
    pre_buffer_size: 1.5
```

## Example Agent

The following is adapted directly from the package’s shipped [`orpheus_tts_app.yaml`](src/sinapsis_orpheus_cpp/configs/orpheus_tts_app.yaml) configuration. Save it as `my_orpheus_cpp_agent.yaml`. The example may require model checkpoints, input files, additional Template packages, or provider credentials as described in its configuration.

```yaml
agent:
  name: my_orpheus_cpp_agent
  description: "Agent that generates speech from text using the Orpheus TTS model."

templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}

- template_name: OrpheusTTS
  class_name: OrpheusTTS
  template_input: InputTemplate
  attributes:
    n_gpu_layers: -1
    n_ctx: 30000
    model_id: "Mungert/orpheus-3b-0.1-ft-GGUF"
    model_variant: "orpheus-3b-0.1-ft-iq3_xxs.gguf"
    voice_id: "tara"
    temperature: 0.8
    top_p: 0.95
    top_k: 40
    min_p: 0.05
    pre_buffer_size: 1.5
    max_tokens: 4096
```

```bash
sinx jobs run my_orpheus_cpp_agent.yaml
```

More configurations: [`orpheus_tts_app.yaml`](src/sinapsis_orpheus_cpp/configs/orpheus_tts_app.yaml), [`orpheus_tts.yaml`](src/sinapsis_orpheus_cpp/configs/orpheus_tts.yaml).

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.

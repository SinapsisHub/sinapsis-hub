<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Kokoro
<br>
</h1>

<h3 align="center">Run lightweight Kokoro text-to-speech synthesis.</h3>

## Overview

**`sinapsis-kokoro`** — Text to speech using Kokoro TTS model.

Kokoro offers local TTS for applications that need generated speech without a hosted inference API. Its relatively small model makes it a different fit from heavier, conversational speech generators.

### Where it fits

It suits straightforward speech synthesis where voice and language options are supported by the model. The optional app integration is separate from core inference.

## Installation

Requires **Python 3.13 or later**, as declared in this package’s manifest. Install the base distribution using your preferred package manager:

```bash
uv pip install sinapsis-kokoro
# or
pip install sinapsis-kokoro
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

| Extra | Adds / when to select it |
|---|---|
| `data-tools` | Media readers/writers or data utilities for a complete pipeline. **Dependencies:** `sinapsis-data-readers`, `sinapsis-data-writers[soundfile]` |
| `all` | Bundle declared by this package; its manifest includes `data-tools`. It does not include `kokoro-app`. |
| `kokoro-app` | Kokoro application/demo integration. **Dependencies:** `sinapsis[webapp]` |

For example:

```bash
uv pip install "sinapsis-kokoro[data-tools]"
```

The manifest also defines development-only dependency groups: `dev` (`pre-commit`, `ruff`, `ty`). These support source development and testing and are **not** runtime extras.

<h2 id="features">🚀 Features
</h2>


<h3>Templates Supported</h3>

This module includes a template for text-to-speech synthesis using the Kokoro TTS model:

- **KokoroTTS**: Converts text to speech using the Kokoro TTS model. The template processes text packets from the input container, generates corresponding audio using Kokoro, and adds the resulting audio packets to the container.

  <details>
  <summary>Attributes</summary>

  - `speed` (Optional): The speed at which the speech will be generated     (default: `1`).
  - `split_pattern` (Optional): The regular expression pattern used to split the input text into smaller chunks (default: `r"\+"`).
  - `voice` (Optional): The voice model to use for speech synthesis (default:`af_heart`).

  The list of languages and voices supported by Kokoro can be found [here](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md)
  </details>


For example, for ***KokoroTTS*** use ```sinx templates example-config KokoroTTS``` to produce an example config like:

```yaml
agent:
  name: my_sinapsis_kokoro_agent
templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}
- template_name: KokoroTTS
  class_name: KokoroTTS
  template_input: InputTemplate
  attributes:
    speed: 1
    split_pattern: \n+
    voice: af_heart

```

## Example Agent

The following is adapted directly from the package’s shipped [`kokoro_demo.yaml`](src/sinapsis_kokoro/configs/kokoro_demo.yaml) configuration. Save it as `my_kokoro_agent.yaml`. The example may require model checkpoints, input files, additional Template packages, or provider credentials as described in its configuration.

```yaml
agent:
  name: my_kokoro_agent
  description: "Agent that generates speech from text using the Kokoro-TTS model."
  attributes:
    queue_name: KokoroTTS
templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}

- template_name: KokoroTTS
  class_name: KokoroTTS
  template_input: InputTemplate
  attributes:
    speed: 1
    voice: af_heart
```

```bash
sinx jobs run my_kokoro_agent.yaml
```

More configurations: [`kokoro_demo.yaml`](src/sinapsis_kokoro/configs/kokoro_demo.yaml), [`kokoro_tts.yaml`](src/sinapsis_kokoro/configs/kokoro_tts.yaml).

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.

<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Csm
<br>
</h1>

<h3 align="center">Generate speech with a conversational speech model.</h3>

## Overview

**`sinapsis-csm`** — Text to speech using CSM TTS model.

Conversational speech generation can use context to produce more natural spoken continuations than isolated sentence synthesis. Exposing it as a Template lets text creation and audio playback share one graph.

### Where it fits

Model weights and GPU memory requirements matter. Use it when voice quality and conversational context justify running a local speech model.

## Installation

Requires **Python 3.13 or later**, as declared in this package’s manifest. Install the base distribution using your preferred package manager:

```bash
uv pip install sinapsis-csm
# or
pip install sinapsis-csm
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

| Extra | Adds / when to select it |
|---|---|
| `data-tools` | Media readers/writers or data utilities for a complete pipeline. **Dependencies:** `sinapsis-data-readers[all]`, `sinapsis-data-writers[soundfile]` |
| `all` | Bundle declared by this package; its manifest includes `data-tools`. |

For example:

```bash
uv pip install "sinapsis-csm[data-tools]"
```

The manifest also defines development-only dependency groups: `dev` (`pre-commit`, `ruff`, `ty`). These support source development and testing and are **not** runtime extras.

<h2 id="features">🚀 Features</h2>

<h3>Templates Supported</h3>

- **CSMTTS**: Converts text into speech using the CSM model.

  <details>
  <summary>Attributes</summary>

  - `speaker_id` (int, default: 0): Speaker identity index.
  - `max_audio_length_ms` (int, default: 10000): Max audio length in milliseconds.
  - `device` ("cpu" or "cuda", default: "cpu"): Device used for inference.
  - `context` (context: list[str] | None = None): Optional list of past utterances for context.
  - `sample_rate_hz` (int, default: 24000): Output audio sample rate.
  </details>

---

## Example Agent

The following is adapted directly from the package’s shipped [`csm_app.yaml`](src/sinapsis_csm/configs/csm_app.yaml) configuration. Save it as `my_csm_agent.yaml`. The example may require model checkpoints, input files, additional Template packages, or provider credentials as described in its configuration.

```yaml
agent:
  name: my_csm_agent
  description: Agent that synthesizes speech from text using the CSM model.

templates:
  - template_name: InputTemplate
    class_name: InputTemplate
    attributes: {}

  - template_name: CSMTTS
    class_name: CSMTTS
    template_input: InputTemplate
    attributes:
      speaker_id: 0
      max_audio_length_ms: 10000
      device: cpu
      context: null
      sample_rate_hz: 24000
```

```bash
sinx jobs run my_csm_agent.yaml
```

More configurations: [`csm_app.yaml`](src/sinapsis_csm/configs/csm_app.yaml), [`csm_agent.yaml`](src/sinapsis_csm/configs/csm_agent.yaml).

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.

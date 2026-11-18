<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Huggingface-Hub
<br>
</h1>

<h3 align="center">Download and manage Hugging Face Hub assets within Agent workflows.</h3>

## Overview

**`sinapsis-huggingface-hub`** — Templates for managing Hugging Face models, spaces and datasets.

Models and datasets frequently need to be acquired before another Template can execute. A dedicated Hub step makes that dependency explicit, improving reproducibility and avoiding ad hoc downloads in model-specific code.

### Where it fits

Authentication, gated assets and cache management depend on the Hub configuration. The `hf-xet` extra enables the corresponding transfer implementation where useful.

## Installation

Requires **Python 3.13 or later**, as declared in this package’s manifest. Install the base distribution using your preferred package manager:

```bash
uv pip install sinapsis-huggingface-hub
# or
pip install sinapsis-huggingface-hub
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

| Extra | Adds / when to select it |
|---|---|
| `hf-xet` | Hf xet support. **Dependencies:** `huggingface-hub[hf-xet]` |
| `all` | Bundle declared by this package; its manifest includes `hf-xet`. |

For example:

```bash
uv pip install "sinapsis-huggingface-hub[hf-xet]"
```

The manifest also defines development-only dependency groups: `dev` (`pre-commit`, `ruff`, `ty`). These support source development and testing and are **not** runtime extras.

<h2 id="features">📦 Features</h2>

The templates in this package include functionality to:

- **HuggingFaceDownloader**: Downloads a repository snapshot from the Hugging Face Hub.

## Example Agent

The following is adapted directly from the package’s shipped [`diffusers_download.yaml`](src/sinapsis_huggingface_hub/configs/diffusers_download.yaml) configuration. Save it as `my_huggingface_hub_agent.yaml`. The example may require model checkpoints, input files, additional Template packages, or provider credentials as described in its configuration.

```yaml
agent:
  name: my_huggingface_hub_agent

templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}

- template_name: HuggingFaceDownloader
  class_name: HuggingFaceDownloader
  template_input: InputTemplate
  attributes:
    repo_id: stable-diffusion-v1-5/stable-diffusion-v1-5
    max_workers: 4
```

```bash
sinx jobs run my_huggingface_hub_agent.yaml
```

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.

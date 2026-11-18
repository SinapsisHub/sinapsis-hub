<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Huggingface-Grounding-Dino
<br>
</h1>

<h3 align="center">Ground free-text object descriptions in image regions.</h3>

## Overview

**`sinapsis-huggingface-grounding-dino`** — Templates for GroundingDINO with HuggingFace.

GroundingDINO links text phrases to candidate bounding boxes, allowing a workflow to detect categories without hard-coding a fixed detector label set. Its output can feed cropping, segmentation or annotation steps in the same Agent.

### Where it fits

Use it for open-vocabulary localisation rather than high-throughput fixed-class detection when a smaller specialised detector may be more efficient. Validate results and thresholds for your own images.

## Installation

Requires **Python 3.13 or later**, as declared in this package’s manifest. Install the base distribution using your preferred package manager:

```bash
uv pip install sinapsis-huggingface-grounding-dino
# or
pip install sinapsis-huggingface-grounding-dino
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

The manifest also defines development-only dependency groups: `dev` (`pre-commit`, `ruff`, `ty`). These support source development and testing and are **not** runtime extras.

<h2 id="features">📦 Features</h2>

The templates in this package include functionality for different **Grounding DINO-based** tasks:

- **GroundingDINO**: Detect objects with **bounding boxes** based on text prompts (**zero-shot object detection**).
- **GroundingDINOClassification**: Classify images using **predefined classes or text prompts**, handling as many classes as possible within token limits.

## Example Agent

The following is adapted directly from the package’s shipped [`grounding_dino_detection.yml`](src/sinapsis_huggingface_grounding_dino/configs/grounding_dino_detection.yml) configuration. Save it as `my_huggingface_grounding_dino_agent.yaml`. The example may require model checkpoints, input files, additional Template packages, or provider credentials as described in its configuration.

```yaml
agent:
  name: my_huggingface_grounding_dino_agent
  description: "GroundingDino image detection"

templates:
  - template_name: InputTemplate
    class_name: InputTemplate
    attributes: { }

  - template_name: GroundingDINO
    class_name: GroundingDINO
    template_input: InputTemplate
    attributes:
      model_path: IDEA-Research/grounding-dino-base
      inference_mode: zero_shot
      text_input: a person.
      device: cuda
      threshold: 0.2
      text_threshold: 0.3

  - template_name: BBoxDrawer
    class_name: BBoxDrawer
    template_input: GroundingDINO
    attributes:
      overwrite: true
      randomized_color: false
```

```bash
sinx jobs run my_huggingface_grounding_dino_agent.yaml
```

More configurations: [`grounding_dino_detection.yml`](src/sinapsis_huggingface_grounding_dino/configs/grounding_dino_detection.yml), [`grounding_dino_classification.yml`](src/sinapsis_huggingface_grounding_dino/configs/grounding_dino_classification.yml), [`grounding_dino_ultralytics_segmentation.yml`](src/sinapsis_huggingface_grounding_dino/configs/grounding_dino_ultralytics_segmentation.yml).

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.

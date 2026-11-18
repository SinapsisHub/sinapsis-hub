<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Anomalib
<br>
</h1>

<h3 align="center">Train, export and run industrial/visual anomaly detectors with anomalib.</h3>

## Overview

**`sinapsis-anomalib`** — Templates for anomaly detection with computer vision using anomalib library.

Anomaly detection is useful when normal examples are abundant but defect examples are rare. Templates expose training, checkpoint export and inference so an inspection system can evolve without rewriting its surrounding data flow.

### Where it fits

Model assumptions and threshold calibration matter, especially when deployment conditions differ from training. Optional logging and VLM features are not required for baseline anomaly detection.

## Installation

Requires **Python 3.13 or later**, as declared in this package’s manifest. Install the base distribution using your preferred package manager:

```bash
uv pip install sinapsis-anomalib
# or
pip install sinapsis-anomalib
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

| Extra | Adds / when to select it |
|---|---|
| `vlm` | Vision-language model integration. **Dependencies:** `python-dotenv`, `transformers`, `openai`, `ollama` |
| `loggers` | Additional training or experiment logging. **Dependencies:** `comet`, `mlflow`, `tensorboard`, `wandb` |
| `all` | Bundle declared by this package; its manifest includes `vlm`, `loggers`. |

For example:

```bash
uv pip install "sinapsis-anomalib[vlm]"
```

The manifest also defines development-only dependency groups: `dev` (`pre-commit`, `ruff`, `ty`). These support source development and testing and are **not** runtime extras.

<h2 id="features">🚀 Features</h2>

<h3> Templates Supported</h3>

The **Sinapsis Anomalib** provides a powerful and flexible implementation for anomaly detection with [Anomalib library](https://anomalib.readthedocs.io/en/v1.2.0/).

- **AnomalibTorchInference**\
_Run anomaly detection inference using PyTorch models._
- **AnomalibOpenVINOInference**\
_Perform optimized inference using OpenVINO-accelerated models._
- **AnomalibTrain**\
_Train custom anomaly detection models with Anomalib._
- **AnomalibExport**\
_Export trained models for deployment in different formats._


For example, for ***CflowTrain*** use ```sinx templates example-config CflowTrain``` to produce the following example config:

```yaml
agent:
  name: my_sinapsis_anomalib_agent
templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}
- template_name: CflowTrain
  class_name: CflowTrain
  template_input: InputTemplate
  attributes:
    folder_attributes:
      name: 'dataset'
      root: null
      normal_dir: 'images/normal'
      abnormal_dir: null
      normal_test_dir: null
      mask_dir: null
      normal_split_ratio: 0.2
      extensions: null
      train_batch_size: 32
      eval_batch_size: 32
      num_workers: 8
      test_split_mode:
      - from_dir
      test_split_ratio: 0.2
      val_split_mode:
      - from_test
      val_split_ratio: 0.5
      seed: null
    callbacks: null
    normalization: null
    threshold: null
    image_metrics: null
    pixel_metrics: null
    logger: null
    callback_configs: null
    logger_configs: null
    ckpt_path: null
    train_root: null
    trainer_args:
      devices: auto
      accelerator: cpu
      min_epochs: 1
      max_epochs: 5
    cflow_init:
      backbone: wide_resnet50_2
      layers:
      - layer2
      - layer3
      - layer4
      pre_trained: true
      fiber_batch_size: 64
      decoder: freia-cflow
      condition_vector: 128
      coupling_blocks: 8
      clamp_alpha: 1.9
      permute_soft: false
      lr: 0.0001
      pre_processor: true
      post_processor: true
      evaluator: true
      visualizer: true

```

<details>
<summary><strong><span style="font-size: 1.25em;">🚫 Excluded Models</span></strong></summary>

Some models that required additional configuration have been excluded and support for this will be included in future releases.

- **EfficientAd**
- **VlmAd**
- **Cfa**
- **Dfkde**
- **Fastflow**
- **Supersimplenet**
- **AiVad**

For all other supported models, refer to the Anomalib documentation linked above.
</details>

## Example Agent

The following is adapted directly from the package’s shipped [`torch_demo.yml`](src/sinapsis_anomalib/configs/inference/torch_demo.yml) configuration. Save it as `my_anomalib_agent.yaml`. The example may require model checkpoints, input files, additional Template packages, or provider credentials as described in its configuration.

```yaml
agent:
  name: my_anomalib_agent
  description: "Agent to perform torch classificaction inference and draw resulting label."

templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}

- template_name: AnomalibTorchInference
  class_name: AnomalibTorchInference
  template_input: InputTemplate
  attributes:
    model_path: "artifacts/exported_models/weights/torch/model.pt"
    device: "cuda"

- template_name: BBoxDrawer
  class_name: BBoxDrawer
  template_input:  AnomalibTorchInference
  attributes:
    randomized_color: false
    draw_classification_label: false

- template_name: SegmentationMaskDrawer
  class_name: SegmentationMaskDrawer
  template_input: BBoxDrawer
  attributes:
    overwrite: true
    randomized_color: false
    draw_classification_label: false
```

```bash
sinx jobs run my_anomalib_agent.yaml
```

More configurations: [`export_from_ckpt_path.yaml`](src/sinapsis_anomalib/configs/export_from_ckpt_path.yaml), [`torch_demo.yml`](src/sinapsis_anomalib/configs/inference/torch_demo.yml), [`openvino_demo.yml`](src/sinapsis_anomalib/configs/inference/openvino_demo.yml), [`train.yaml`](src/sinapsis_anomalib/configs/train.yaml), [`patchcore_train_export_unsupervised.yaml`](src/sinapsis_anomalib/configs/patchcore_train_export_unsupervised.yaml), [`train_export.yaml`](src/sinapsis_anomalib/configs/train_export.yaml), [`train_export_unsupervised.yaml`](src/sinapsis_anomalib/configs/train_export_unsupervised.yaml), [`torch_from_dataset.yml`](src/sinapsis_anomalib/configs/inference/torch_from_dataset.yml), [`openvino_from_dataset.yml`](src/sinapsis_anomalib/configs/inference/openvino_from_dataset.yml), [`cflow_train_export_unsupervised.yaml`](src/sinapsis_anomalib/configs/cflow_train_export_unsupervised.yaml).

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.

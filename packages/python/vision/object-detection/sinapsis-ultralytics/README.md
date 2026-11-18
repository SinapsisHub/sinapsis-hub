<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Ultralytics
<br>
</h1>

<h3 align="center">Use Ultralytics models for detection, pose, segmentation and training workflows.</h3>

## Overview

**`sinapsis-ultralytics`** — Package to build computer vision applications based on the Ultralytics library.

Ultralytics covers several related vision tasks with common tooling. Templates expose training, prediction, validation and export, letting an Agent reuse readers and annotation writers across these model families.

### Where it fits

Use a model head and checkpoint suited to the task—object boxes, poses and oriented boxes are different outputs. GPU needs and dataset annotation formats depend on the selected training or inference mode.

## Installation

Requires **Python 3.13 or later**, as declared in this package’s manifest. Install the base distribution using your preferred package manager:

```bash
uv pip install sinapsis-ultralytics
# or
pip install sinapsis-ultralytics
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

| Extra | Adds / when to select it |
|---|---|
| `sinapsis-data-visualization` | Render plots or annotate results for inspection. **Dependencies:** `sinapsis-data-visualization` |
| `all` | Bundle declared by this package; its manifest includes `sinapsis-data-readers`, `sinapsis-data-visualization`, `sinapsis-data-writers`. |
| `sinapsis-data-writers` | Save the resulting DataContainer content to files. **Dependencies:** `sinapsis-data-writers` |
| `sinapsis-data-readers` | Load external media or datasets into DataContainers. **Dependencies:** `sinapsis-data-readers` |

For example:

```bash
uv pip install "sinapsis-ultralytics[sinapsis-data-visualization]"
```

The manifest also defines development-only dependency groups: `dev` (`ruff`, `pre-commit`). These support source development and testing and are **not** runtime extras.

<h2 id="features">🚀 Features</h2>

<h3> Templates Supported</h3>

- **UltralyticsTrain**: Template for training Ultralytics models.

    <details>
    <summary>Attributes</summary>

    - `model_class`(Required): The Ultralytics model class name. Options: `YOLO`, `YOLOWorld`, `SAM`, `FastSAM`, `NAS`, `RTDETR`.
    - `model`(Required): The model name or model path to be loaded.
    - `task`(Optional): The task to be performed by the model. Only needed by YOLO models if the task can't be obtained from the specified model name. Options: `classify`, `detect`, `segment`, `pose`, `obb` (default: `None`).
    - `verbose`(Optional): Whether to print verbose logs (default: `False`).
    - `working_dir`(Optional): The working directory for ultralytics. Ultralytics default models are downloaded to this directory (default :`SINAPSIS_CACHE_DIR/ultralytics`).
    - `datasets_dir`(Optional): The directory where the datasets are located. Ultralytics datasets ar downloaded to this directory (default: `working_dir/datasets`).
    - `runs_dir`(Optional): The directory where the training experiment artifacts are saved (default: `working_dir/runs`).
    - `checkpoint_path`(Optional): Optional explicit path to a checkpoint (pre-trained) model (default: `None`).
    - `training_params`(Optional): A dictionary containing the training parameters for the Ultralytics model. If not specified, default parameters will be used. The full documentation for available training parameters can be found in the Ultralytics [docs](https://docs.ultralytics.com/modes/train/#train-settings).

    </details>

- **UltralyticsVal**: Template for validating Ultralytics models.

    <details>
    <summary>Attributes</summary>

    - `model_class`(Required): The Ultralytics model class name. Options: `YOLO`, `YOLOWorld`, `SAM`, `FastSAM`, `NAS`, `RTDETR`.
    - `model`(Required): The model name or model path to be loaded.
    - `task`(Optional): The task to be performed by the model. Only needed by YOLO models if the task can't be obtained from the specified model name. Options: `classify`, `detect`, `segment`, `pose`, `obb` (default: `None`).
    - `verbose`(Optional): Whether to print verbose logs (default: `False`).
    - `working_dir`(Optional): The working directory for ultralytics. Ultralytics default models are downloaded to this directory (default :`SINAPSIS_CACHE_DIR/ultralytics`).
    - `datasets_dir`(Optional): The directory where the datasets are located. Ultralytics datasets ar downloaded to this directory (default: `working_dir/datasets`).
    - `runs_dir`(Optional): The directory where the training experiment artifacts are saved (default: `working_dir/runs`).
    - `checkpoint_path`(Optional): Optional explicit path to a checkpoint (pre-trained) model (default: `None`).
    - `validation_params`(Optional): A dictionary containing the validation parameters for the Ultralytics model. If not specified, default parameters will be used. The full documentation for available validation parameters can be found in the Ultralytics [docs](https://docs.ultralytics.com/modes/val/#arguments-for-yolo-model-validation).

    </details>

- **UltralyticsPredict**: Template for generating inference predictions with trained models.

    <details>
    <summary>Attributes</summary>

    - `model_class`(Required): The Ultralytics model class name. Options: `YOLO`, `YOLOWorld`, `SAM`, `FastSAM`, `NAS`, `RTDETR`.
    - `model`(Required): The model name or model path to be loaded.
    - `task`(Optional): The task to be performed by the model. Only needed by YOLO models if the task can't be obtained from the specified model name. Options: `classify`, `detect`, `segment`, `pose`, `obb` (default: `None`).
    - `verbose`(Optional): Whether to print verbose logs (default: `False`).
    - `working_dir`(Optional): The working directory for ultralytics. Ultralytics default models are downloaded to this directory (default :`SINAPSIS_CACHE_DIR/ultralytics`).
    - `datasets_dir`(Optional): The directory where the datasets are located. Ultralytics datasets ar downloaded to this directory (default: `working_dir/datasets`).
    - `runs_dir`(Optional): The directory where the training experiment artifacts are saved (default: `working_dir/runs`).
    - `checkpoint_path`(Optional): Optional explicit path to a checkpoint (pre-trained) model (default: `None`).
    - `predict_params`(Optional)**: A dictionary containing the inference parameters for the Ultralytics model. If not specified, default parameters will be used. The full documentation for available inference parameters can be found in the Ultralytics [docs](https://docs.ultralytics.com/modes/predict/#inference-arguments).
    - `use_detections_as_sam_prompt`(Optional): Whether to use the available detections as prompts for SAM model (default: `False`).

    </details>

- **UltralyticsExport**: Template for exporting models to deployment-ready format.

    <details>
    <summary>Attributes</summary>

    - `model_class`(Required): The Ultralytics model class name. Options: `YOLO`, `YOLOWorld`, `SAM`, `FastSAM`, `NAS`, `RTDETR`.
    - `model`(Required): The model name or model path to be loaded.
    - `task`(Optional): The task to be performed by the model. Only needed by YOLO models if the task can't be obtained from the specified model name. Options: `classify`, `detect`, `segment`, `pose`, `obb` (default: `None`).
    - `verbose`(Optional): Whether to print verbose logs (default: `False`).
    - `working_dir`(Optional): The working directory for ultralytics. Ultralytics default models are downloaded to this directory (default :`SINAPSIS_CACHE_DIR/ultralytics`).
    - `datasets_dir`(Optional): The directory where the datasets are located. Ultralytics datasets ar downloaded to this directory (default: `working_dir/datasets`).
    - `runs_dir`(Optional): The directory where the training experiment artifacts are saved (default: `working_dir/runs`).
    - `checkpoint_path`(Optional): Optional explicit path to a checkpoint (pre-trained) model (default: `None`).
    - `export_params`(Optional): A dictionary containing the export parameters for the Ultralytics model. If not specified, default parameters will be used. The full documentation for available export parameters can be found in the Ultralytics [docs](https://docs.ultralytics.com/modes/export/#arguments).

    </details>


For example, for ***UltralyticsPredict*** use ```sinx templates example-config UltralyticsPredict``` to produce the following example config:

```yaml
agent:
  name: my_sinapsis_ultralytics_agent
templates:
- template_name: InputTemplate
  class_name: InputTemplate
- template_name: UltralyticsPredict
  class_name: UltralyticsPredict
  template_input: InputTemplate
  attributes:
    model_class: 'YOLO'
    model: null
    task: null
    verbose: false
    working_dir: /path/to/sinapsis/cache
    datasets_dir: /path/to/sinapsis/cache/datasets
    run_id: null
    checkpoint_name: last.pt
    checkpoint_path: null
    predict_params: {}
    use_detections_as_sam_prompt: false

```

## Example Agent

The following is adapted directly from the package’s shipped [`predict_classify.yaml`](src/sinapsis_ultralytics/configs/predict_classify.yaml) configuration. Save it as `my_ultralytics_agent.yaml`. The example may require model checkpoints, input files, additional Template packages, or provider credentials as described in its configuration.

```yaml
agent:
  name: my_ultralytics_agent
  description: agent to run inference with a classification model using Ultralytics

templates:
- template_name: InputTemplate-1
  class_name: InputTemplate
  attributes: { }

- template_name: UltralyticsPredict
  class_name: UltralyticsPredict
  template_input: InputTemplate-1
  attributes:
    model_class: YOLO
    model: yolo11n-cls.pt
    task: classify
    verbose: 0
    predict_params: {}

- template_name: LabelDrawer
  class_name: LabelDrawer
  template_input: UltralyticsPredict
  attributes:
    draw_confidence: True
    draw_classification_label: True
    draw_extra_labels: false
    text_box_to_border_offset: 0.025
```

```bash
sinx jobs run my_ultralytics_agent.yaml
```

More configurations: [`eval_model.yaml`](src/sinapsis_ultralytics/configs/eval_model.yaml), [`train_classify.yaml`](src/sinapsis_ultralytics/configs/train_classify.yaml), [`train_detect.yaml`](src/sinapsis_ultralytics/configs/train_detect.yaml), [`train_obb.yaml`](src/sinapsis_ultralytics/configs/train_obb.yaml), [`train_pose.yaml`](src/sinapsis_ultralytics/configs/train_pose.yaml), [`train_segment.yaml`](src/sinapsis_ultralytics/configs/train_segment.yaml), [`predict_classify.yaml`](src/sinapsis_ultralytics/configs/predict_classify.yaml), [`predict_pose.yaml`](src/sinapsis_ultralytics/configs/predict_pose.yaml), [`predict_obb.yaml`](src/sinapsis_ultralytics/configs/predict_obb.yaml), [`predict_segment.yaml`](src/sinapsis_ultralytics/configs/predict_segment.yaml), [`predict_detect.yaml`](src/sinapsis_ultralytics/configs/predict_detect.yaml).

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.

For ultralytics please see their license and ensure you comply with it. 
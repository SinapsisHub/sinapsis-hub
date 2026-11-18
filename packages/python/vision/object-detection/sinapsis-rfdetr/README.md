<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Rfdetr
<br>
</h1>

<h3 align="center">Train, evaluate and infer with RF-DETR detectors.</h3>

## Overview

**`sinapsis-rfdetr`** — Training and inference templates based on the RF-DETR object detection model.

RF-DETR brings transformer-based detection into the same DataContainer contract as other Sinapsis vision components. This means a model can be swapped in a detection and tracking pipeline without rewriting the data-handling steps.

### Where it fits

Choose it when its accuracy/latency characteristics match your workload; training and high-resolution inference can be GPU-intensive. Separate export and inference configs are provided.

## Installation

Requires **Python 3.13 or later**, as declared in this package’s manifest. Install the base distribution using your preferred package manager:

```bash
uv pip install sinapsis-rfdetr
# or
pip install sinapsis-rfdetr
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

| Extra | Adds / when to select it |
|---|---|
| `all` | Bundle declared by this package; its manifest includes `data-tools`. |
| `data-tools` | Media readers/writers or data utilities for a complete pipeline. **Dependencies:** `sinapsis-data-readers`, `sinapsis-data-visualization[all]`, `sinapsis-data-writers[all]` |

For example:

```bash
uv pip install "sinapsis-rfdetr[data-tools]"
```

The manifest also defines development-only dependency groups: `dev` (`ruff`, `pre-commit`). These support source development and testing and are **not** runtime extras.

<h2 id="features">🚀 Features</h2>

<h3>🗂️ Templates Supported</h3>

- **RFDETRExport** and **RFDETRLargeExport**: Templates for exporting the RFDETRBase and RFDETRLarge models to ONNX format.
    <details>
    <summary>Attributes</summary>

    - `model_params`(Optional): A dictionary containing model parameters for initializing the RF-DETR model (default: None). The parameters in `model_params` can include:
        - `resolution`: Defines the resolution of the input images. It must be divisible by 56.
        - `pretrain_weights`: Specifies pretrained weights path for loading a fine-tuned model.
        - `num_classes`: Specifies the number of classes for the model.
    - `export_params`(Optional): A dictionary containing the export parameters for the RF-DETR model (default: None). Key parameters that can be included in `export_params` are:
        - `output_dir`: The directory where the exported ONNX model will be saved (default: `SINAPSIS_CACHE_DIR/rfdetr`).

    </details>

- **RFDETRInference** and **RFDETRLargeInference**: Templates designed to perform inference on a set of images using the RFDETRBase and RFDETRLarge models.

    <details>
    <summary>Attributes</summary>

    - `model_params`(Optional): A dictionary containing model parameters for initializing the RF-DETR model (default: None). The parameters in `model_params` can include:
        - `resolution`: Defines the resolution of the input images. It must be divisible by 56.
        - `pretrain_weights`: Specifies pretrained weights path for loading a fine-tuned model.
        - `num_classes`: Specifies the number of classes for the model.
    - `annotations_path`(Optional): The file path to a JSON file containing annotations (default: "").
    - `threshold`(Required): A threshold for the confidence score used to filter the model's predictions (default: 0.5).

    </details>

- **RFDETRTrain** and **RFDETRLargeTrain**: Templates for training the RFDETRBase and RFDETRLarge models.

    <details>
    <summary>Attributes</summary>

    - `model_params`(Optional): A dictionary containing model parameters for initializing the RF-DETR model (default: None). The parameters in `model_params` can include:
        - `resolution`: Defines the resolution of the input images. It must be divisible by 56.
        - `num_classes`: Specifies the number of classes for the model.
    - `callback`(Required): Specifies the callback that will be used during training (default: `on_fit_epoch_end`).
    - `training_params`(Required): A dictionary containing the training parameters for the RF-DETR model (default: None). The only required argument is `dataset_dir`, which is the path to the COCO-formatted dataset directory, including `train`, `valid`, and `test` folders, each containing an `_annotations.coco.json` file.

    You can find the complete documentation for the available training parameters on the [RF-DETR GitHub](https://github.com/roboflow/rf-detr/tree/main) page.

    </details>


For example, for ***RFDETRTrain*** use ```sinx templates example-config RFDETRTrain``` to produce an example config like:

```yaml
agent:
  name: my_sinapsis_rfdetr_agent
templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}
- template_name: RFDETRTrain
  class_name: RFDETRTrain
  template_input: InputTemplate
  attributes:
    model_params:
      encoder: dinov2_windowed_small
      out_feature_indexes:
      - 2
      - 5
      - 8
      - 11
      dec_layers: 3
      two_stage: true
      projector_scale:
      - P4
      hidden_dim: 256
      sa_nheads: 8
      ca_nheads: 16
      dec_n_points: 2
      bbox_reparam: true
      lite_refpoint_refine: true
      layer_norm: true
      amp: true
      num_classes: 90
      pretrain_weights: rf-detr-base.pth
      device: cuda
      resolution: 560
      group_detr: 13
      gradient_checkpointing: false
      num_queries: 300
    callback: on_fit_epoch_end
    training_params:
      lr: 0.0001
      lr_encoder: 0.00015
      batch_size: 4
      grad_accum_steps: 4
      epochs: 100
      ema_decay: 0.993
      ema_tau: 100
      lr_drop: 100
      checkpoint_interval: 10
      warmup_epochs: 0
      lr_vit_layer_decay: 0.8
      lr_component_decay: 0.7
      drop_path: 0.0
      group_detr: 13
      ia_bce_loss: true
      cls_loss_coef: 1.0
      num_select: 300
      dataset_file: roboflow
      square_resize_div_64: true
      dataset_dir: 'path/to/dataset'
      output_dir: output
      multi_scale: true
      expanded_scales: true
      use_ema: true
      num_workers: 2
      weight_decay: 0.0001
      early_stopping: false
      early_stopping_patience: 10
      early_stopping_min_delta: 0.001
      early_stopping_use_ema: false
      tensorboard: true
      wandb: false
      project: null
      run: null
      class_names: null
```

<details>
<summary id="uv"><strong><span style="font-size: 1.4em;">📈 Training the RF-DETR model</span></strong></summary>


The **RFDETRTrain** and **RFDETRLargeTrain** templates in `sinapsis-rfdetr` simplify the process of training RF-DETR models using custom datasets. Here’s a breakdown of the training process and how to use the attributes effectively:

1. **Dataset Requirements**: Your dataset must be in **COCO format**, split into three directories: `train`, `valid`, and `test`. Each directory should contain an `_annotations.coco.json` file, which holds annotations for the respective subset, along with the corresponding image files.

The [Roboflow Universe](https://universe.roboflow.com/) provides a diverse selection of pre-labeled datasets for various use cases. To access and download a dataset, simply [create a free account account](https://app.roboflow.com/login). Additionally, [Roboflow](https://roboflow.com/annotate) allows you to create custom object detection datasets from scratch or convert existing datasets (e.g., YOLO) into COCO JSON format for training.

2. **Key Training Parameters**: The following parameters in `training_params` help configure and fine-tune the training process:
- `dataset_dir`: The path to the COCO-formatted dataset directory, containing `train`, `valid`, and `test` folders, each of which contains an `_annotations.coco.json` file.
- `epochs`: Total number of training epochs.
- `batch_size`: The number of samples per training iteration. Adjust based on available GPU memory, and use  it alongside `grad_accum_steps` to maintain the intended effective batch size.
- `grad_accum_steps`: The number of mini-batches over which gradients are accumulated.  This increases the total batch size without requiring additional memory, making it useful for GPUs with less VRAM.
- `lr`: Learning rate for optimization.
- `resume`: Allows resuming training from a saved checkpoint by specifying the checkpoint file path. This is helpful for continuing interrupted training or fine-tuning a previously trained model.
- `early_stopping`: Halts training when the model's validation performance (mAP) shows no improvement over a specified number of epochs. The stopping behavior can be adjusted using parameters like `early_stopping_patience`, `early_stopping_min_delta`, and `early_stopping_use_ema`.

**Note on memory usage**: Adjust `batch_size` and `grad_accum_steps` according to GPU VRAM. For example:
- On powerful GPUs like the A100, you can use `batch_size=16` and `grad_accum_steps=1`.
- On smaller GPUs like the T4, you may want to use `batch_size=4` and `grad_accum_steps=4`.

 Detail documentation is available on the [RF-DETR GitHub](https://github.com/roboflow/rf-detr/tree/main) page.

3. **Checkpoints**: During training, two model checkpoints will be saved: one for regular weights (`checkpoint_best_regular.pth`) and another for the Exponential Moving Average (EMA) of the model’s weights (`checkpoint_best_total.pth`), which helps improve stability and generalization.

4. **Using the Fine-Tuned Model**:
After training, load the fine-tuned model by setting the path to the pre-trained weights in  `pretrain_weights` within the `model_params` argument. Use the **RFDETRInference** template to run predictions on images.

</details>

## Example Agent

The following is adapted directly from the package’s shipped [`rfdetr_demo.yml`](src/sinapsis_rfdetr/configs/rfdetr_demo.yml) configuration. Save it as `my_rfdetr_agent.yaml`. The example may require model checkpoints, input files, additional Template packages, or provider credentials as described in its configuration.

```yaml
agent:
  name: my_rfdetr_agent
  description: Agent that runs inferences on images using the gradio interface

templates:
  - template_name: InputTemplate
    class_name: InputTemplate
    attributes: {}

  - template_name: RFDETRInference
    class_name: RFDETRInference
    template_input: InputTemplate
    attributes:
      threshold: 0.5
      #annotations_path: datasets/COCO Dataset.v37i.coco/test/_annotations.coco.json
      #model_params:
      #  pretrain_weights: checkpoint_best_total.pth
      #  num_classes: 78

  - template_name: BBoxDrawer
    class_name: BBoxDrawer
    template_input: RFDETRInference
    attributes:
      randomized_color: false
```

```bash
sinx jobs run my_rfdetr_agent.yaml
```

More configurations: [`rfdetr_export.yml`](src/sinapsis_rfdetr/configs/rfdetr_export.yml), [`rfdetr_train.yml`](src/sinapsis_rfdetr/configs/rfdetr_train.yml), [`rfdetr_demo.yml`](src/sinapsis_rfdetr/configs/rfdetr_demo.yml), [`rfdetr_inference.yml`](src/sinapsis_rfdetr/configs/rfdetr_inference.yml), [`rfdetr_inference_trained.yml`](src/sinapsis_rfdetr/configs/rfdetr_inference_trained.yml).

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.

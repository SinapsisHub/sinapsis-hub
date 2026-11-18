<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Fast-Alpr
<br>
</h1>

<h3 align="center">Detect and read license plates, with optional tracking and speed analysis.</h3>

## Overview

**`sinapsis-fast-alpr`** — Fast ALPR license plate recognition.

A plate-recognition pipeline benefits from combining detection, OCR and temporal information rather than treating every frame independently. This package includes plate-focused processing and utility steps for monitoring applications.

### Where it fits

License-plate accuracy depends on camera angle, resolution, region and lighting. `tracking` and `detection` extras add capabilities beyond basic recognition; speed calculations require calibrated geometry.

## Installation

Requires **Python 3.13 or later**, as declared in this package’s manifest. Install the base distribution using your preferred package manager:

```bash
uv pip install sinapsis-fast-alpr
# or
pip install sinapsis-fast-alpr
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

| Extra | Adds / when to select it |
|---|---|
| `detection` | Plate/object detection capabilities. **Dependencies:** `sinapsis-rfdetr` |
| `tracking` | Multi-frame object tracking capabilities. **Dependencies:** `sinapsis-supervision` |
| `all` | Bundle declared by this package; its manifest includes `detection`, `tracking`, `data-tools`. |
| `data-tools` | Media readers/writers or data utilities for a complete pipeline. **Dependencies:** `sinapsis-data-readers`, `sinapsis-data-visualization`, `sinapsis-data-writers` |

For example:

```bash
uv pip install "sinapsis-fast-alpr[detection]"
```

The manifest also defines development-only dependency groups: `dev` (`pre-commit`, `ruff`, `ty`). These support source development and testing and are **not** runtime extras.

<h2 id="features">🚀 Features</h2>

<h3> Templates Supported</h3>

The **Sinapsis Fast ALPR** module provides the following templates for Speed Calculation and License Plate Recognition.

- **ClassFilter**: Limits object detections to certain given classes.
- **FastALPR**: Runs fast-alpr pipeline to detect and recognize license plates.
- **DetectionPerspectiveTransform**: Transforms the perspective of a camera into a rectangle to compensate for the view and works along with ObjectSpeedCalculation template.
- **ObjectSpeedCalculation**: Approximates the speed of objects detected in video.


<h2 id="usage-example">📚 Example usage</h2>

The example available in <code>sinapsis-fast-alpr/src/sinapsis_fast_alpr/configs/speed_calculation.yaml</code> demonstrates how to use the sinapsis-fast-alpr templates. This configuration defines an **agent** and a sequence of **templates** to run fast-alpr and speed calculation.

To adjust the configuration details for your own video, you can use the pick-coordinates and meters-per-pixel commands to obtain the values to add in the DetectionPerspectiveTransform and ObjectSpeedCalculation templates.

- Use <code>uv run pick-coordinates [path to your video]</code> and pick four points of the road to compensate the perspective. The script will give the values for source_points that can be added to **DetectionPerspectiveTransform**

- Use <code>uv run meters-per-pixel [path to your video]</code> and pick two points on the road which represent a meter in real-life distance. The script will give a meters_per_pixel value that can be added to **ObjectSpeedCalculation**

- You can substitute the values for frames per second, thresholds, detector models according to your provided video and requirements.

<details>
  <summary id="config"><strong><span style="font-size: 1.2em;">Config file</span></strong></summary>

```yaml
agent:
  name: speed_calculation
  attributes:
    agent_mode: generator

templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}

- template_name: Video
  class_name: VideoReaderCV2
  template_input: InputTemplate
  attributes:
    root_dir: path to root dir
    video_file_path: path to video
    batch_size: 1
    device: cpu
    loop_forever: true


- template_name: Inference
  class_name: RFDETRInference
  template_input: Video
  attributes:
    model_params:
      encoder: dinov2_windowed_small
      num_classes: 90
      pretrain_weights: rf-detr-base.pth
      device: cuda
      resolution: 560
    threshold: 0.6

- template_name: Filter
  class_name: ClassFilter
  template_input: Inference
  attributes: {}


- template_name: Track
  class_name: ByteTrack
  template_input: Filter
  attributes:
    track_activation_threshold: 0.2
    minimum_matching_threshold: 0.5
    minimum_consecutive_frames: 1
    frame_rate: 25

- template_name: Transform
  class_name: DetectionPerspectiveTransform
  template_input: Track
  attributes:
    source_points: [[806, 291], [1237, 291], [1562, 931], [325, 920]]

- template_name: Speed
  class_name: ObjectSpeedCalculation
  template_input: Transform
  attributes:
    fps: 25
    meters_per_pixel: 0.06
    speed_limit: 20

- template_name: License
  class_name: FastALPR
  template_input: Speed
  attributes:
    detector_model: yolo-v9-s-608-license-plate-end2end
    ocr_model: cct-xs-v1-global-model
    detection_treshold: 0.6
    ocr_threshold: 0.6

- template_name: Drawer
  class_name: BBoxDrawer
  template_input: License
  attributes:
    overwrite: true
    randomized_color: false
    draw_confidence: true
    draw_extra_labels: true
    text_style:
      font: 0
      font_scale: 0.5
      thickness: 2
    draw_classification_label: true
    classification_label_position: top_right
    text_box_to_border_offset: 0.01

- template_name: VideoWriterCV2
  class_name: VideoWriterCV2
  template_input: Drawer
  attributes:
    root_dir: .
    destination_path: results/video.mp4
    height: -1
    width: -1
    fps: 25
    codec: mp4v
    save_image_batch: false

```
</details>

To run the agent, use:

```bash
uv run sinx jobs run sinapsis-fast-alpr/src/sinapsis_fast_alpr/configs/speed_calculation.yaml
```

## Example Agent

Start from the package’s shipped [`speed_calculation.yaml`](src/sinapsis_fast_alpr/configs/speed_calculation.yaml) configuration, which includes the model-specific attributes and graph connections. Copy it to `my_fast_alpr_agent.yaml`, adjust its input paths, model configuration and credentials, then run:

```bash
sinx jobs run my_fast_alpr_agent.yaml
```

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.

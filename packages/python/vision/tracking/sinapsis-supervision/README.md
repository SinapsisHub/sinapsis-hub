<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Supervision
<br>
</h1>

<h3 align="center">Use Supervision and ByteTrack for detection-based multi-object tracking.</h3>

## Overview

**`sinapsis-supervision`** — Templates for multi-object tracking using the ByteTrack algorithm.

ByteTrack links detections across frames using confidence and motion information, enabling temporal applications while preserving the same annotation and output conventions as other Sinapsis vision packages.

### Where it fits

It is suited to tracking when detections are available; it does not replace an object detector. Detector extras and output writers are optional components of a full pipeline.

## Installation

Requires **Python 3.13 or later**, as declared in this package’s manifest. Install the base distribution using your preferred package manager:

```bash
uv pip install sinapsis-supervision
# or
pip install sinapsis-supervision
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

| Extra | Adds / when to select it |
|---|---|
| `all` | Bundle declared by this package; its manifest includes `sinapsis-data-readers`, `sinapsis-data-writers`, `sinapsis-dfine`, `sinapsis-ultralytics`. |
| `sinapsis-ultralytics` | Sinapsis ultralytics support. **Dependencies:** `sinapsis-ultralytics` |
| `sinapsis-dfine` | Sinapsis dfine support. **Dependencies:** `sinapsis-dfine[training]` |
| `sinapsis-data-readers` | Load external media or datasets into DataContainers. **Dependencies:** `sinapsis-data-readers[opencv]` |
| `sinapsis-data-writers` | Save the resulting DataContainer content to files. **Dependencies:** `sinapsis-data-writers` |

For example:

```bash
uv pip install "sinapsis-supervision[sinapsis-ultralytics]"
```

The manifest also defines development-only dependency groups: `dev` (`ruff`, `pre-commit`). These support source development and testing and are **not** runtime extras.

<h2 id="features">🚀 Features</h2>

<h3> Templates Supported</h3>

The **Sinapsis ByteTrack** module provides a template for multi-object tracking using the **ByteTrack** algorithm. Currently, the package includes the following template:

- **ByteTrack**: A template for tracking objects across video frames, with customizable parameters for track activation, matching thresholds, and occlusion handling.


For example, for ***ByteTrack*** use ```sinx templates example-config ByteTrack``` to produce the following example config:

```yaml
agent:
  name: my_sinapsis_supervision_agent
templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}
- template_name: ByteTrack
  class_name: ByteTrack
  template_input: InputTemplate
  attributes:
    track_activation_threshold: 0.2
    lost_track_buffer: 30
    minimum_matching_threshold: 0.7
    frame_rate: 30
    minimum_consecutive_frames: 1
```

<details>
<summary><strong><span style="font-size: 1.25em;">📚 Example Usage</span></strong></summary>

Below is an example YAML configuration for processing a video file and visualizing tracking results using the **Sinapsis Supervision** template. This configuration loads a video with the **VideoReaderCV2**, performs object detection and real-time tracking with the **UltralyticsPredict** and **ByteTrack** templates, draws bounding boxes around detected objects with the **BBoxDrawer**, and saves the output as a new video file using the **VideoWriterCV2**.

<details>
<summary ><strong><span style="font-size: 1.4em;">Config</span></strong></summary>

```yaml
agent:
  name: cotracker_agent

templates:
  - template_name: InputTemplate
    class_name: InputTemplate
    attributes: {}

  - template_name : VideoReaderCV2
    class_name: VideoReaderCV2
    template_input: InputTemplate
    attributes:
      video_file_path : "artifacts/palace.mp4"
      batch_size: 16

  - template_name: CoTrackerOnline
    class_name: CoTrackerOnline
    template_input: VideoReaderCV2
    attributes:
      model_variant: baseline
      device: cuda
      grid_size: 15

  - template_name: CoTrackerVisualizer
    class_name: CoTrackerVisualizer
    template_input: CoTrackerOnline
    attributes:
      device : cuda
      linewidth: 3
      overwrite: true

  - template_name: VideoWriterCV2
    class_name: VideoWriterCV2
    template_input: CoTrackerVisualizer
    attributes:
      destination_path: "artifacts/result.mp4"
      height: -1
      width: -1
      fps: 30
```
</details>

This configuration defines an **agent** and a sequence of **templates** for video processing, object detection, real-time tracking, and visualization.

**IMPORTANT**: The VideoReaderCV2, BBoxDrawer, and VideoWriterCV2 templates are part of the [sinapsis-data-readers](https://github.com/SinapsisHub/sinapsis-hub), [sinapsis-data-visualization](https://github.com/SinapsisHub/sinapsis-hub), and [sinapsis-data-writers](https://github.com/SinapsisHub/sinapsis-hub) packages, respectively. To use this example, ensure that you have installed these packages.


To run the config, use the CLI:
```bash
sinx jobs run my_agent.yaml
```

</details>

## Example Agent

The following is adapted directly from the package’s shipped [`bytetrack_ultralytics_demo_real_time.yml`](src/sinapsis_supervision/configs/bytetrack_ultralytics_demo_real_time.yml) configuration. Save it as `my_supervision_agent.yaml`. The example may require model checkpoints, input files, additional Template packages, or provider credentials as described in its configuration.

```yaml
agent:
  name: my_supervision_agent
  description: Agent to perform ByteTrack inference using Ultralytics YOLO model as detector (real-time).

templates:
  - template_name: InputTemplate
    class_name: InputTemplate
    attributes: {}

  - template_name: UltralyticsPredict
    class_name: UltralyticsPredict
    template_input: InputTemplate
    attributes:
      model_class: YOLO
      model: yolo11n.pt
      task: detect
      prediction_params:
        conf: 0.7
        iou: 0.8

  - template_name: ByteTrack
    class_name: ByteTrack
    template_input: UltralyticsPredict
    attributes:
      track_activation_threshold: 0.2
      frame_rate: 30

  - template_name: BBoxDrawer
    class_name: BBoxDrawer
    template_input: ByteTrack
    attributes:
      overwrite: true
      draw_classification_label: false
      randomized_color: false
```

```bash
sinx jobs run my_supervision_agent.yaml
```

More configurations: [`bytetrack_ultralytics_demo_real_time.yml`](src/sinapsis_supervision/configs/bytetrack_ultralytics_demo_real_time.yml), [`bytrack_dfine_demo_real_time.yml`](src/sinapsis_supervision/configs/bytrack_dfine_demo_real_time.yml), [`bytetrack_dfine_demo.yml`](src/sinapsis_supervision/configs/bytetrack_dfine_demo.yml), [`bytetrack_ultralytics_demo.yml`](src/sinapsis_supervision/configs/bytetrack_ultralytics_demo.yml).

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.

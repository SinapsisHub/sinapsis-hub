<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Rf-Trackers
<br>
</h1>

<h3 align="center">Track detections over time with SORT and DeepSORT.</h3>

## Overview

**`sinapsis-rf-trackers`** — Multi-object tracking templates using SORT and DeepSORT algorithms.

Detectors return independent boxes per frame, while tracking maintains stable identities. SORT-style trackers supply that temporal association so applications can count objects and analyse trajectories.

### Where it fits

These trackers depend on a suitable detection stream. Choose SORT for simpler association or DeepSORT when appearance features help; the optional detector extras connect supported D-FINE and Ultralytics workflows.

## Installation

Requires **Python 3.13 or later**, as declared in this package’s manifest. Install the base distribution using your preferred package manager:

```bash
uv pip install sinapsis-rf-trackers
# or
pip install sinapsis-rf-trackers
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

| Extra | Adds / when to select it |
|---|---|
| `all` | Bundle declared by this package; its manifest includes `sinapsis-ultralytics`, `sinapsis-dfine`, `sinapsis-data-readers`, `sinapsis-data-writers`. |
| `sinapsis-ultralytics` | Sinapsis ultralytics support. **Dependencies:** `sinapsis-ultralytics` |
| `sinapsis-dfine` | Sinapsis dfine support. **Dependencies:** `sinapsis-dfine[training]` |
| `sinapsis-data-readers` | Load external media or datasets into DataContainers. **Dependencies:** `sinapsis-data-readers[opencv]` |
| `sinapsis-data-writers` | Save the resulting DataContainer content to files. **Dependencies:** `sinapsis-data-writers` |

For example:

```bash
uv pip install "sinapsis-rf-trackers[sinapsis-ultralytics]"
```

The manifest also defines development-only dependency groups: `dev` (`ruff`, `pre-commit`). These support source development and testing and are **not** runtime extras.

<h2 id="features">🚀 Features</h2>

<h3> Templates Supported</h3>

The **Sinapsis RF Trackers** module provides Sinapsis templates that wrap Roboflow's proven tracking algorithms for multi-object tracking. The package leverages the **Roboflow trackers library** to deliver enterprise-grade tracking performance with easy-to-use configurations.

Currently, the package includes the following templates:

- **SORTTrackerInference**: Simple Online and Realtime Tracking algorithm implementation from Roboflow, featuring motion-based tracking using Kalman filters and Hungarian algorithm for data association.

    <details>
    <summary>Attributes</summary>

    - `track_activation_threshold` (Optional): Detection confidence threshold for track activation. Increasing this value improves accuracy and stability but might miss true detections. Decreasing it increases completeness but risks introducing noise and instability (default: `0.25`).
    - `lost_track_buffer` (Optional): Number of frames to buffer when a track is lost. Increasing this value enhances occlusion handling, significantly reducing the likelihood of track fragmentation or disappearance caused by brief detection gaps (default: `30`).
    - `frame_rate` (Optional): The frame rate of the video sequence being processed. This affects the temporal dynamics of the tracking algorithm (default: `30.0`).
    - `minimum_consecutive_frames` (Optional): Number of consecutive frames that an object must be tracked before it is considered a 'valid' track. Increasing this value prevents the creation of accidental tracks from false detection or double detection, but risks missing shorter tracks (default: `3`).
    - `minimum_iou_threshold` (Optional): Minimum IoU threshold for associating detections with tracks. Higher values require better spatial overlap for association, improving precision but potentially reducing recall (default: `0.3`).

    </details>

- **DeepSORTTrackerInference**: Enhanced SORT algorithm from Roboflow with deep appearance features for improved re-identification and reduced identity switches during occlusions.

    <details>
    <summary>Attributes</summary>

    - `track_activation_threshold` (Optional): Detection confidence threshold for track activation. Increasing this value improves accuracy and stability but might miss true detections. Decreasing it increases completeness but risks introducing noise and instability (default: `0.25`).
    - `lost_track_buffer` (Optional): Number of frames to buffer when a track is lost. Increasing this value enhances occlusion handling, significantly reducing the likelihood of track fragmentation or disappearance caused by brief detection gaps (default: `30`).
    - `frame_rate` (Optional): The frame rate of the video sequence being processed. This affects the temporal dynamics of the tracking algorithm (default: `30.0`).
    - `minimum_consecutive_frames` (Optional): Number of consecutive frames that an object must be tracked before it is considered a 'valid' track. Increasing this value prevents the creation of accidental tracks from false detection or double detection, but risks missing shorter tracks (default: `3`).
    - `minimum_iou_threshold` (Optional): Minimum IoU threshold for associating detections with tracks. Higher values require better spatial overlap for association, improving precision but potentially reducing recall (default: `0.3`).
    - `appearance_threshold` (Optional): Threshold for appearance-based matching. Higher values make the tracker more conservative in appearance matching, reducing identity switches but potentially losing tracks during occlusions (default: `0.7`).
    - `appearance_weight` (Optional): Weight of appearance features versus motion features in the association cost. Higher values prioritize appearance matching, lower values prioritize motion consistency (default: `0.5`).
    - `distance_metric` (Optional): Distance metric for appearance feature comparison. Supported metrics include 'cosine' and 'euclidean'. Cosine distance is generally more robust for appearance features (default: `"cosine"`).
    - `reid_model_name` (Optional): Name of the ReID model to use. Should be compatible with either timm library or custom model format (default: `"tf_efficientnet_b1.in1k"`).
    - `reid_device` (Optional): Device to run feature extraction on. CUDA provides faster inference but requires GPU availability. Options: `"auto"`, `"cuda"`, `"cpu"` (default: `"auto"`).
    - `reid_get_pooled_features` (Optional): Whether to use pooled features from the Re-ID model (default: `true`).
    - `reid_kwargs` (Optional): Additional keyword arguments to pass to the Re-ID model constructor.

    </details>


For example, for ***SORTTrackerInference*** use ```sinx templates example-config SORTTrackerInference``` to produce the following example config:

```yaml
agent:
  name: sort_tracker_agent
templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}
- template_name: SORTTrackerInference
  class_name: SORTTrackerInference
  template_input: InputTemplate
  attributes:
    track_activation_threshold: 0.25
    lost_track_buffer: 30
    minimum_consecutive_frames: 3
    minimum_iou_threshold: 0.3
    frame_rate: 30
```

For ***DeepSORTTrackerInference*** use ```sinx templates example-config DeepSORTTrackerInference``` to produce the following example config:

```yaml
agent:
  name: deepsort_tracker_agent
templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}
- template_name: DeepSORTTrackerInference
  class_name: DeepSORTTrackerInference
  template_input: InputTemplate
  attributes:
    track_activation_threshold: 0.25
    lost_track_buffer: 30
    minimum_consecutive_frames: 3
    minimum_iou_threshold: 0.3
    frame_rate: 30
    appearance_threshold: 0.7
    appearance_weight: 0.5
    distance_metric: "cosine"
    reid_model_name: "tf_efficientnet_b1.in1k"
    reid_device: "cuda"
```

<details>
<summary><strong><span style="font-size: 1.25em;">📚 Example Usage</span></strong></summary>

Below are example YAML configurations for processing video files and performing real-time tracking using different detector backends with Roboflow's tracking algorithms.

<details>
<summary><strong><span style="font-size: 1.4em;">SORT with Ultralytics YOLO</span></strong></summary>

```yaml
agent:
  name: sort_tracker_agent
  description: "SORT tracking with Ultralytics detector"

templates:
  - template_name: InputTemplate
    class_name: InputTemplate
    attributes: {}

  - template_name: VideoReaderCV2
    class_name: VideoReaderCV2
    template_input: InputTemplate
    attributes:
      video_file_path: "artifacts/demo_video.mp4"
      batch_size: -1

  - template_name: UltralyticsPredict
    class_name: UltralyticsPredict
    template_input: VideoReaderCV2
    attributes:
      model_class: YOLO
      model: yolo11n.pt
      task: detect
      prediction_params:
        conf: 0.7
        iou: 0.8

  - template_name: SORTTrackerInference
    class_name: SORTTrackerInference
    template_input: UltralyticsPredict
    attributes:
      track_activation_threshold: 0.25
      lost_track_buffer: 30
      minimum_consecutive_frames: 3
      minimum_iou_threshold: 0.3
      frame_rate: 30

  - template_name: BBoxDrawer
    class_name: BBoxDrawer
    template_input: SORTTrackerInference
    attributes:
      overwrite: true
      randomized_color: false
      draw_extra_labels: true

  - template_name: VideoWriterCV2
    class_name: VideoWriterCV2
    template_input: BBoxDrawer
    attributes:
      destination_path: "artifacts/tracked_result.mp4"
      height: -1
      width: -1
      fps: 30
```
</details>

<details>
<summary><strong><span style="font-size: 1.4em;">DeepSORT with DFINE</span></strong></summary>

```yaml
agent:
  name: deepsort_tracker_agent
  description: "DeepSORT tracking with DFINE detector"

templates:
  - template_name: InputTemplate
    class_name: InputTemplate
    attributes: {}

  - template_name: VideoReaderCV2
    class_name: VideoReaderCV2
    template_input: InputTemplate
    attributes:
      video_file_path: "artifacts/demo_video.mp4"
      batch_size: -1

  - template_name: DFINEInference
    class_name: DFINEInference
    template_input: VideoReaderCV2
    attributes:
      threshold: 0.5
      config_file: artifacts/configs/dfine/dfine_hgnetv2_n_coco.yml
      device: cuda
      pretrained_model:
        size: n
        variant: coco

  - template_name: DeepSORTTrackerInference
    class_name: DeepSORTTrackerInference
    template_input: DFINEInference
    attributes:
      track_activation_threshold: 0.25
      lost_track_buffer: 30
      minimum_consecutive_frames: 3
      minimum_iou_threshold: 0.3
      frame_rate: 30
      appearance_threshold: 0.7
      appearance_weight: 0.5
      distance_metric: "cosine"
      reid_model_name: "tf_efficientnet_b1.in1k"
      reid_device: "cuda"

  - template_name: BBoxDrawer
    class_name: BBoxDrawer
    template_input: DeepSORTTrackerInference
    attributes:
      overwrite: true
      randomized_color: false
      draw_extra_labels: true

  - template_name: VideoWriterCV2
    class_name: VideoWriterCV2
    template_input: BBoxDrawer
    attributes:
      destination_path: "artifacts/tracked_result.mp4"
      height: -1
      width: -1
      fps: 30
```
</details>

**IMPORTANT**: The VideoReaderCV2, BBoxDrawer, and VideoWriterCV2 templates are part of the [sinapsis-data-readers](https://github.com/SinapsisHub/sinapsis-hub), [sinapsis-data-visualization](https://github.com/SinapsisHub/sinapsis-hub), and [sinapsis-data-writers](https://github.com/SinapsisHub/sinapsis-hub) packages, respectively. The UltralyticsPredict template is part of [sinapsis-ultralytics](https://github.com/SinapsisHub/sinapsis-hub) and DFINEInference is part of [sinapsis-dfine](https://github.com/SinapsisHub/sinapsis-hub). To use these examples, ensure you have installed the corresponding packages.

To run the config, use the CLI:
```bash
sinx jobs run your_config.yml
```

</details>

## Example Agent

The following is adapted directly from the package’s shipped [`sort_tracker_dfine_demo_real_time.yml`](src/sinapsis_rf_trackers/configs/sort_tracker_dfine_demo_real_time.yml) configuration. Save it as `my_rf_trackers_agent.yaml`. The example may require model checkpoints, input files, additional Template packages, or provider credentials as described in its configuration.

```yaml
agent:
  name: my_rf_trackers_agent
  description: "SORT tracking with DFINE detector"

templates:
  - template_name: InputTemplate
    class_name: InputTemplate
    attributes: {}

  - template_name: DFINEInference
    class_name: DFINEInference
    template_input: InputTemplate
    attributes:
      threshold: 0.5
      config_file: artifacts/configs/dfine/dfine_hgnetv2_n_coco.yml
      device: cuda
      pretrained_model:
        size: n
        variant: coco

  - template_name: SORTTrackerInference
    class_name: SORTTrackerInference
    template_input: DFINEInference
    attributes:
      lost_track_buffer: 30
      track_activation_threshold: 0.25
      minimum_consecutive_frames: 1
      minimum_iou_threshold: 0.3
      frame_rate: 30

  - template_name: BBoxDrawer
    class_name: BBoxDrawer
    template_input: SORTTrackerInference
    attributes:
      overwrite: true
      randomized_color: false
      draw_extra_labels: true
```

```bash
sinx jobs run my_rf_trackers_agent.yaml
```

More configurations: [`sort_tracker_dfine_demo_real_time.yml`](src/sinapsis_rf_trackers/configs/sort_tracker_dfine_demo_real_time.yml), [`sort_tracker_ultralytics_demo_real_time.yml`](src/sinapsis_rf_trackers/configs/sort_tracker_ultralytics_demo_real_time.yml), [`deepsort_tracker_dfine_demo_real_time.yml`](src/sinapsis_rf_trackers/configs/deepsort_tracker_dfine_demo_real_time.yml), [`deepsort_tracker_ultralytics_demo_real_time.yml`](src/sinapsis_rf_trackers/configs/deepsort_tracker_ultralytics_demo_real_time.yml), [`sort_tracker_offline.yml`](src/sinapsis_rf_trackers/configs/sort_tracker_offline.yml), [`sort_tracker_ultralytics.yml`](src/sinapsis_rf_trackers/configs/sort_tracker_ultralytics.yml), [`deepsort_tracker_offline.yml`](src/sinapsis_rf_trackers/configs/deepsort_tracker_offline.yml).

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.

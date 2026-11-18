<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Cotracker
<br>
</h1>

<h3 align="center">Track points and objects across frames with CoTracker.</h3>

## Overview

**`sinapsis-cotracker`** — Templates for multi-object tracking using the CoTracker model, supporting offline, online, and visualization workflows.

Point tracking provides trajectories through a video, even when an application does not start from frame-by-frame object detections. The package includes offline, online and visualisation workflows for different data access patterns.

### Where it fits

Online tracking is useful for streams; offline methods can use full temporal context. Video resolution, sequence length and model state affect memory use.

## Installation

Requires **Python 3.13 or later**, as declared in this package’s manifest. Install the base distribution using your preferred package manager:

```bash
uv pip install sinapsis-cotracker
# or
pip install sinapsis-cotracker
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

| Extra | Adds / when to select it |
|---|---|
| `all` | Bundle declared by this package; its manifest includes `sinapsis-data-readers`, `sinapsis-data-visualization`, `sinapsis-data-writers`. |
| `sinapsis-data-readers` | Load external media or datasets into DataContainers. **Dependencies:** `sinapsis-data-readers[opencv]` |
| `sinapsis-data-writers` | Save the resulting DataContainer content to files. **Dependencies:** `sinapsis-data-writers` |
| `sinapsis-data-visualization` | Render plots or annotate results for inspection. **Dependencies:** `sinapsis-data-visualization[visualization-matplotlib]` |

For example:

```bash
uv pip install "sinapsis-cotracker[sinapsis-data-readers]"
```

The manifest also defines development-only dependency groups: `dev` (`ruff`, `pre-commit`). These support source development and testing and are **not** runtime extras.

<h2 id="features">🚀 Features</h2>

<h3> Templates Supported</h3>

The **Sinapsis CoTracker** module offers a set of templates for multi-object tracking and visualization using the **CoTracker** model. These templates enable users to perform both online and offline tracking, process video inputs, and visualize tracking results on video frames. The templates in this package include functionality for:

- **CoTrackerOffline**: Handles offline multi-object tracking for short videos. It loads the entire video into memory for processing and is the simplest method for offline tasks.
- **CoTrackerOfflineLarge**: Provides offline tracking for long videos by using a memory-efficient, incremental engine.
- **CoTrackerOnline**: Supports real-time object tracking with advanced grid query and support grid features.
- **CoTrackerVisualizer**: Visualizes tracking results with customizable trace, line width, and visualization modes.


For example, for ***CoTrackerOffline*** use ```sinx templates example-config CoTrackerOffline``` to produce the following example config:

```yaml
agent:
  name: my_sinapsis_cotracker_agent
templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}
- template_name: CoTrackerOffline
  class_name: CoTrackerOffline
  template_input: InputTemplate
  attributes:
    device: '`replace_me:typing.Literal[''cuda'', ''cpu'']`'
    generic_key_field: CoTrackerResults
    model_cache_dir: /home/cv/.cache/sinapsis
    model_variant: '`replace_me:typing.Literal[''baseline'', ''scaled'']`'
    use_segmentation_mask: false
    grid_size: '`replace_me:<class ''int''>`'
    grid_query_frame: 0
    backward_tracking: false
```

<details>
<summary><strong><span style="font-size: 1.25em;">📚 Example Usage</span></strong></summary>

Below is an example YAML configuration for processing a video file and visualizing tracking results using **Sinapsis CoTracker** templates. This setup loads a video with the **VideoReaderCV2**, performs real-time object tracking with the **CoTrackerOnline** template, visualizes the results with the **CoTrackerVisualizer**, and saves the output as a new video file using the **VideoWriterCV2**.
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

This configuration defines an **agent** and a sequence of **templates** for video processing, object tracking, and visualization.

**IMPORTANT**: The VideoReaderCV2 and VideoWriterCV2 templates are part of the [sinapsis-data-readers](https://github.com/SinapsisHub/sinapsis-hub) and [sinapsis-data-writers](https://github.com/SinapsisHub/sinapsis-hub) packages, respectively. To use this example, ensure that you have installed these packages.


To run the config, use the CLI:
```bash
sinx jobs run my_agent.yaml
```

</details>

## Example Agent

The following is adapted directly from the package’s shipped [`cotracker_batch.yml`](src/sinapsis_cotracker/configs/cotracker_batch.yml) configuration. Save it as `my_cotracker_agent.yaml`. The example may require model checkpoints, input files, additional Template packages, or provider credentials as described in its configuration.

```yaml
agent:
  name: my_cotracker_agent
  description: >
    "Agent to load video from local dir, perform CoTrackerOnline inference
    and store visualization results in destination path."

templates:
  - template_name: InputTemplate
    class_name: InputTemplate
    attributes: {}

  - template_name : VideoReaderCV2
    class_name: VideoReaderCV2
    template_input: InputTemplate
    attributes:
      root_dir: "."
      video_file_path : "artifacts/apple.mp4"
      batch_size: -1

  - template_name: CoTrackerOfflineLarge
    class_name: CoTrackerOfflineLarge
    template_input: VideoReaderCV2
    attributes:
      model_variant: baseline
      device: cuda
      grid_size: 15

  - template_name: CoTrackerVisualizer
    class_name: CoTrackerVisualizer
    template_input: CoTrackerOfflineLarge
    attributes:
      device : cuda
      linewidth: 3
      overwrite: true
      generic_key_field: CoTrackerOfflineLarge

  - template_name: VideoWriterCV2
    class_name: VideoWriterCV2
    template_input: CoTrackerVisualizer
    attributes:
      root_dir: "."
      destination_path: "artifacts/result.mp4"
      height: -1
      width: -1
      fps: 10
```

```bash
sinx jobs run my_cotracker_agent.yaml
```

More configurations: [`cotracker_batch.yml`](src/sinapsis_cotracker/configs/cotracker_batch.yml), [`cotracker_online.yml`](src/sinapsis_cotracker/configs/cotracker_online.yml), [`cotracker_offline.yml`](src/sinapsis_cotracker/configs/cotracker_offline.yml).

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.

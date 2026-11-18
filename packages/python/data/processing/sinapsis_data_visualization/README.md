<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Data-Visualization
<br>
</h1>

<h3 align="center">Visualise packet content, annotations and distributions.</h3>

## Overview

**`sinapsis-data-visualization`** — Templates to perform visualization of data distributions and image annotations.

Model outputs need inspection: boxes, labels and data distributions help developers and operators understand what an Agent produced. Visualization Templates keep that work inside the graph rather than in ad hoc notebook code.

### Where it fits

Rendering is a separate step from inference. The `visualization-matplotlib` extra is useful when plots are needed; avoid drawing every frame in performance-sensitive pipelines unless required.

## Installation

Requires **Python 3.13 or later**, as declared in this package’s manifest. Install the base distribution using your preferred package manager:

```bash
uv pip install sinapsis-data-visualization
# or
pip install sinapsis-data-visualization
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

| Extra | Adds / when to select it |
|---|---|
| `visualization-matplotlib` | Matplotlib-based rendering and plots. **Dependencies:** `matplotlib` |
| `all` | Bundle declared by this package; its manifest includes `visualization-matplotlib`. |

For example:

```bash
uv pip install "sinapsis-data-visualization[visualization-matplotlib]"
```

The manifest also defines development-only dependency groups: `dev` (`pre-commit`, `ruff`, `ty`). These support source development and testing and are **not** runtime extras.

<h2 id="features">🚀 Features</h2>


For example, for ***BBoxDrawer*** use ```sinx templates example-config BBoxDrawer``` to produce the following example config:
<details id='packages'><summary><strong><span style="font-size: 1.0em;"> Config</span></strong></summary>

```yaml
agent:
    name: my_annotation_preview_agent
    description: Draw existing image annotations for inspection
templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}
- template_name: FolderImageDatasetCV2
  class_name: FolderImageDatasetCV2
  template_input: InputTemplate
  attributes:
    data_dir: '/path/to/sinapsis/cache/dir'
    pattern: '**/*'
    batch_size: 1
    shuffle_data: false
    samples_to_load: -1
    load_on_init: false
    label_path_index: -2
    is_ground_truth: false
- template_name: BBoxDrawer
  class_name: BBoxDrawer
  template_input: FolderImageDatasetCV2
  attributes:
    overwrite: false
    randomized_color: true
    draw_confidence: true
    draw_extra_labels: true
    text_style:
      font: 0
      font_scale: 0.5
      thickness: 2
    draw_classification_label: false
    classification_label_position: top_right
    text_box_to_border_offset: 0.01

```

## Template discovery and examples

The package exposes Template implementations including `BBoxDrawer`, `OrientedBBoxDrawer`, `KeyPointsDrawer`, `SegmentationMaskDrawer`, `TabularDataVisualization`, `DataDistributionVisualization`.

Inspect the installed environment for the exact classes and validated attributes, then generate a starter configuration:

```bash
sinx templates show-all
sinx templates example-config TabularDataVisualization
```

Visualisation operates on existing annotations or tabular data in the input packets. The illustrated `BBoxDrawer` assumes image annotations are already present; a folder reader alone will not generate bounding boxes.

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.

<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Data-Readers
<br>
</h1>

<h3 align="center">Bring files, datasets, video and streaming data into typed Sinapsis packets.</h3>

## Overview

**`sinapsis-data-readers`** — Templates to read data in different formats.

Input adapters are often repeated across projects. These Templates turn source-specific data into a `DataContainer`, letting downstream models operate on a consistent shape and metadata contract.

### Where it fits

Choose the reader and extra for the underlying format—OpenCV, FFmpeg, soundfile, DALI, tabular datasets, and others. Video streaming and offline dataset loading have different buffering and performance needs.

## Installation

Requires **Python 3.13 or later**, as declared in this package’s manifest. Install the base distribution using your preferred package manager:

```bash
uv pip install sinapsis-data-readers
# or
pip install sinapsis-data-readers
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

| Extra | Adds / when to select it |
|---|---|
| `nvidia-dali` | NVIDIA DALI data pipelines. **Dependencies:** `nvidia-dali-cuda120` |
| `torch-codec` | Torch codec support. **Dependencies:** `torch`, `torchcodec` |
| `sklearn-datasets` | Sklearn datasets support. **Dependencies:** `pandas`, `scikit-learn` |
| `sktime-datareaders` | Sktime datareaders support. **Dependencies:** `sktime` |
| `coco-dataset` | Coco dataset support. **Dependencies:** `pycocotools` |
| `soundfile` | Soundfile support. **Dependencies:** `soundfile` |
| `pydub` | Pydub support. **Dependencies:** `pydub`, `soundfile` |
| `all` | Bundle declared by this package; its manifest includes `coco-dataset`, `nvidia-dali`, `pydub`, `sklearn-datasets`, `sktime-datareaders`, `soundfile`, `torch-codec`, `opencv`, `ffmpeg`, `kornia`. |
| `opencv` | OpenCV image/video support. **Dependencies:** `opencv-python-headless` |
| `ffmpeg` | FFmpeg media reading/writing support. **Dependencies:** `ffmpeg-python` |
| `kornia` | Kornia support. **Dependencies:** `kornia`, `kornia-rs`, `pillow` |

For folder-based image loading, install OpenCV support:

```bash
uv pip install "sinapsis-data-readers[opencv]"
```

The manifest also defines development-only dependency groups: `dev` (`pre-commit`, `ruff`, `ty`). These support source development and testing and are **not** runtime extras.

<h2 id="features">🚀 Features</h2>


- **Sinapsis Data Readers**
    - **Audio Readers**\
    _Read audio files from several formats using Pydub, Soundfile, among others._
    - **Dataset Readers**\
    _Read and manipulate tabular datasets from the scikit libraries, among others._
    - **Image Readers**\
    _Read and manipulate images from COCO, paths in CSVs, whole folders, etc._
    - **Text Readers**\
    _Read text data from a simple string and other sources._
    - **Video Readers**\
    _Read videoframes using CV2, Dali, FFMPEG, Torch, among others._


For example, for ***FolderImageDatasetCV2*** use ```sinx templates example-config FolderImageDatasetCV2``` to produce the following example config:


```yaml
agent:
  name: my_image_reader_agent
  description: Agent to read images from a folder using OpenCV
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

```

## Template discovery and examples

The package exposes Template implementations including `FolderImageDatasetCV2`, `CSVDatasetReader`, `TextInput`, `SKTimeDatasets`, `SKLearnDatasets`.

Inspect the installed environment for the exact classes and validated attributes, then generate a starter configuration:

```bash
sinx templates show-all
sinx templates example-config FolderImageDatasetCV2
```

`FolderImageDatasetCV2` is provided by the `opencv` extra. Use it for folder-based images, or select the reader matching your data source and install its corresponding extra.

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.

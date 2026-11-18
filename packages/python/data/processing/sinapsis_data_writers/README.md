<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis Data-Writers
<br>
</h1>

<h3 align="center">Persist images, audio, video and other packet results.</h3>

## Overview

**`sinapsis-data-writers`** — Templates to write DataContainer content to file.

A workflow often produces results in several modalities. Writers standardise saving these outputs so model Templates can remain independent of filesystem paths and export formats.

### Where it fits

Select optional encoders for the output modality: `opencv`/`ffmpeg` for visual media, audio libraries for sound and PDF tools for document rendering. Output destination permissions are environment-specific.

## Installation

Requires **Python 3.13 or later**, as declared in this package’s manifest. Install the base distribution using your preferred package manager:

```bash
uv pip install sinapsis-data-writers
# or
pip install sinapsis-data-writers
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

| Extra | Adds / when to select it |
|---|---|
| `pydub` | Pydub support. **Dependencies:** `pydub` |
| `soundfile` | Soundfile support. **Dependencies:** `soundfile` |
| `pdf-image-writer` | PDF/image export support. **Dependencies:** `pdf2image` |
| `all` | Bundle declared by this package; its manifest includes `pdf-image-writer`, `pydub`, `soundfile`, `opencv`, `ffmpeg`. |
| `opencv` | OpenCV image/video support. **Dependencies:** `opencv-python-headless` |
| `ffmpeg` | FFmpeg media reading/writing support. **Dependencies:** `ffmpeg-python` |

For example:

```bash
uv pip install "sinapsis-data-writers[pydub]"
```

The manifest also defines development-only dependency groups: `dev` (`pre-commit`, `ruff`, `ty`). These support source development and testing and are **not** runtime extras.

<h2 id="features">🚀 Features</h2>

- **Sinapsis Data Writers**\
_Write data to many kinds of files._
    - **Annotation Writers**\
    _Save text annotations to JSON, geometries to polygons, etc._
    - **Audio Writers**\
    _Save to audio files using Soundfile, among others._
    - **Image Writers**
    _Save to image files using CV2, among others._
    - **Video Writers**\
    _Save to video files using CV2 or FFMPEG, among others._
- **Sinapsis Generic Data Tools**\
_Wide range of miscellaneous tools to manipulate your data._


For example, for ***ImageSaver*** use ```sinx templates example-config ImageSaver``` to produce the following example config:


```yaml
agent:
  name: my_image_writer_agent
  description: Agent to save image packets locally
templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}
- template_name: ImageSaver
  class_name: ImageSaver
  template_input: InputTemplate
  attributes:
    save_dir: /path/to/save/dir
    extension: jpg
    root_dir: '/path/to/sinapsis/cache'
    save_full_image: true
    save_bbox_crops: false
    save_mask_crops: false
    min_bbox_dim: 5
```

## Template discovery and examples

The package exposes Template implementations including `ImageSaver`, `GenericDataJSONWriter`, `AudioWriterSoundfile`, `PDFToImage`.

Inspect the installed environment for the exact classes and validated attributes, then generate a starter configuration:

```bash
sinx templates show-all
sinx templates example-config ImageSaver
```

Choose the writer based on the packet type and desired output format. `ImageSaver` writes image packets, while the JSON and audio writers operate on different payloads and have different optional dependencies.

## Documentation

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.

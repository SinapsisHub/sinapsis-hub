<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis docTR
<br>
</h1>

<h3 align="center">Detection plus recognition for document text and geometry.</h3>

## Overview

`sinapsis-doctr` integrates the **docTR** OCR stack as `DocTROCRPrediction`. It uses a two-stage pipeline: detect text regions in an image, then recognise the text associated with those regions. The Template converts docTR page, block, line and word output into `ImageAnnotations` attached to Sinapsis image packets.

### OCR where geometry is as important as the words

For scans, forms, page annotations and document digitisation, word positions and confidences are often needed alongside transcription. A two-stage detector/recogniser lets you control the recognition architecture separately from detection and preserves word-level geometry for crop generation, quality checks and review UIs.

This is **recognition-oriented OCR**. It does not provide a natural-language extraction prompt or guarantee semantic table reconstruction. Its strengths are spatial text detection, recognition and page-processing controls (orientation, straightening and aspect ratio handling).

## Installation

Requires **Python 3.13+**. The base package includes `python-doctr[torch]` and the Sinapsis integration:

```bash
uv pip install sinapsis-doctr
```

For the example with an image-folder reader:

```bash
uv pip install "sinapsis-doctr[sinapsis-data-readers]"
```

## Optional features and dependencies

The base installation includes the dependencies required by the package. The following **extras** are declared in this package’s `pyproject.toml`; install only those needed by your workflow. They are standard Python optional dependencies, not separate execution profiles.

| Extra | Adds / when to select it |
|---|---|
| `sinapsis-data-readers` | Load external media or datasets into DataContainers. **Dependencies:** `sinapsis-data-readers[opencv]` |
| `sinapsis-data-writers` | Save the resulting DataContainer content to files. **Dependencies:** `sinapsis-data-writers` |
| `sinapsis-data-visualization` | Render plots or annotate results for inspection. **Dependencies:** `sinapsis-data-visualization[visualization-matplotlib]` |
| `all` | Bundle declared by this package; its manifest includes `sinapsis-data-readers`, `sinapsis-data-writers`, `sinapsis-data-visualization`. |

For example:

```bash
uv pip install "sinapsis-doctr[sinapsis-data-readers]"
```

The manifest also defines development-only dependency groups: `dev` (`pre-commit`, `ruff`, `ty`). These support source development and testing and are **not** runtime extras.

## `DocTROCRPrediction` Template

| Attribute | Purpose |
|---|---|
| `det_arch` | Text detector backbone, e.g. `fast_base` (default). |
| `reco_arch` | Text recogniser, e.g. `crnn_vgg16_bn` (default). |
| `pretrained`, `pretrained_backbone` | Load available pretrained weights. |
| `assume_straight_pages`, `straighten_pages` | Control skew/orientation handling. |
| `detect_orientation`, `detect_language` | Optional page analysis. |
| `preserve_aspect_ratio`, `symmetric_pad` | Preprocessing and geometry preservation. |
| `recognized_characters_as_labels`, `artefact_type_as_labels` | Annotation label representation. |

### Example: OCR a folder of scanned pages

Create `my_doctr_agent.yaml`:

```yaml
agent:
  name: my_doctr_agent

templates:
  - template_name: Input
    class_name: InputTemplate
    attributes: {}

  - template_name: Scans
    class_name: FolderImageDatasetCV2
    template_input: Input
    attributes:
      data_dir: dataset/input

  - template_name: DocumentOCR
    class_name: DocTROCRPrediction
    template_input: Scans
    attributes:
      det_arch: fast_base
      reco_arch: crnn_vgg16_bn
      pretrained: true
      preserve_aspect_ratio: true
      detect_orientation: false
```

```bash
sinx jobs run my_doctr_agent.yaml
```

`DocumentOCR` adds bounding boxes, labels and recognition information to the input images. You can connect a visualization Template to inspect uncertain regions or retain geometry for indexing/review.

Shipped configurations: [recognition](src/sinapsis_doctr/configs/ocr_prediction.yaml) and [end-to-end demo](src/sinapsis_doctr/configs/doctr_demo.yaml).

### Operational considerations

- Detector and recogniser model choices affect speed, accuracy, memory use and language coverage.
- Rotated or unusual layouts may benefit from the orientation and page-straightening switches rather than assuming straight pages.
- The annotation path retains spatial information; extracting one plain text string for a downstream LLM is a separate, optional workflow step.

## Resources

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.

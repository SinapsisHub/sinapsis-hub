<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/SinapsisHub/brand-resources/blob/main/public/logo/sinapsis-logo-horizontal-dark-brand.png?raw=true"
    alt="Sinapsis"
    width="300">
</a>
<br>
Sinapsis EasyOCR
<br>
</h1>

<h3 align="center">Local, lightweight OCR for multilingual image text and bounding boxes.</h3>

## Overview

`sinapsis-easyocr` wraps the [EasyOCR](https://github.com/JaidedAI/EasyOCR) detector and recogniser as a Sinapsis `EasyOCR` Template. It reads `ImagePacket` objects and appends bounding-box annotations with recognised text. It can also assemble the recognised words into a `TextPacket` through `get_full_text`.

### Best suited to text spotting and conventional recognition

For signs, screenshots, product labels, receipts and ordinary image text, a conventional OCR detector/recogniser is often enough. EasyOCR avoids loading a large prompt-driven vision-language model and supports **CPU execution** (`reader_params.gpu: false`) as well as GPU execution. This makes it an approachable choice when deployment size, hardware and repeatable localisation matter more than generative document interpretation.

Language support is configured with `reader_params.lang_list`. Detection and recognition are independent parts of the Reader, and the current Template exposes `craft` or `dbnet18` for text detection. Results retain text and geometry inside the original `DataContainer`, so a downstream `BBoxDrawer`, cropper, indexer or storage Template can consume them.

EasyOCR does **not** reason about a document's semantic structure or follow open-ended extraction prompts. For complex tables, forms or schema-guided extraction, a vision-language OCR model may be more appropriate; for structured word geometry, docTR is another fit.

## Installation

Requires **Python 3.13+**. Install the base OCR package:

```bash
uv pip install sinapsis-easyocr
```

To run the image-folder example below, include its OpenCV image reader:

```bash
uv pip install "sinapsis-easyocr[sinapsis-data-readers]"
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
uv pip install "sinapsis-easyocr[sinapsis-data-readers]"
```

The manifest also defines development-only dependency groups: `dev` (`pre-commit`, `ruff`, `ty`). These support source development and testing and are **not** runtime extras.

## `EasyOCR` Template

The Template's main Pydantic attributes are:

| Attribute | Meaning |
|---|---|
| `reader_params.lang_list` | Languages to recognise, e.g. `["en", "fr"]`. |
| `reader_params.gpu` | Whether EasyOCR should use GPU acceleration; set to `false` for CPU. |
| `reader_params.detect_network` | `craft` (default) or `dbnet18`. |
| `reader_params.recog_network` | Recognition network (default `standard`). |
| `read_text_params` | Decoding, thresholds, beam width, paragraph grouping, and other EasyOCR `readtext()` options. |
| `get_full_text` | Also append concatenated recognised text as a `TextPacket` (default `false`). |
| `enable_img_resize`, `img_width`, `img_height` | Optional explicit resizing before OCR. |

### Example: image folder → OCR annotations and text

Save as `my_easyocr_agent.yaml`:

```yaml
agent:
  name: my_easyocr_agent

templates:
  - template_name: Input
    class_name: InputTemplate
    attributes: {}

  - template_name: Images
    class_name: FolderImageDatasetCV2
    template_input: Input
    attributes:
      data_dir: dataset/input

  - template_name: OCR
    class_name: EasyOCR
    template_input: Images
    attributes:
      reader_params:
        lang_list: ["en"]
        gpu: false
      get_full_text: true
```

Place images in `dataset/input`, then execute:

```bash
sinx jobs run my_easyocr_agent.yaml
```

This configuration returns the same image packets enriched with detected text annotations and a concatenated text packet. For an annotated image output, continue the graph into `BBoxDrawer` and `ImageSaver` after installing the relevant visualization/writer extras.

Reference configs: [basic inference](src/sinapsis_easyocr/configs/easyocr_inference.yaml) and [drawing demo](src/sinapsis_easyocr/configs/easyocr_demo.yaml).

### Performance and output trade-offs

- A CPU deployment is possible, but processing time grows with image resolution, number of text regions and the recogniser configuration.
- `read_text_params` controls thresholding and decoding and is useful when small, slanted or low-contrast text needs tuning.
- Enabling `get_full_text` gives downstream search/LLM Templates convenient text but does not replace per-word geometry when spatial position matters.
- The first run may download pretrained weights when the model cache is empty (`download_enabled` controls this).

## Resources

- [Sinapsis documentation](https://docs.sinapsis.tech/)
- [Tutorials and examples](https://docs.sinapsis.tech/docs/latest/tutorials)
- [Sinapsis website](https://sinapsis.tech/)

## License

Sinapsis open-source components are available under your choice of the [MIT License](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), unless otherwise noted.
